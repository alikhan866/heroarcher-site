"""Cut the Hero Archer trailer and the site's gameplay loop from the recorded takes.

    python trailer/make_trailer.py [path-to-game-repo] [--loop]   (--loop: the site loop only)

Reads trailer/build/takes/<take>/ (frames, taps.txt, events.txt from
trailer/unity/record.py) and trailer/build/cards/ (captions.py), and writes:

    trailer/build/out/trailer-1080x1920.mp4   9:16, 60 fps, music + game sound, captions
    assets/video/gameplay.mp4                 the site's muted loop, 1080x1180
    assets/img/gameplay-poster.webp           its poster frame

The game's sound is rebuilt from its own clips at the frames the takes logged
(AudioRenderer gives nothing in the editor): every bow shot, death cry, zap,
ability cast with its announcer line, upgrade, gear pickup and equip, at the
volumes the game plays them, with the game's +/-8% pitch variance.
"""
import math
import os
import random
import shutil
import subprocess
import sys

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.abspath(os.path.join(HERE, ".."))
ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
GAME = os.path.abspath(ARGS[0] if ARGS else os.path.join(SITE, "..", "Evil-archer"))
TAKES = os.path.join(HERE, "build", "takes")
CARDS = os.path.join(HERE, "build", "cards")
EDIT = os.path.join(HERE, "build", "edit")
OUT = os.path.join(HERE, "build", "out")
FF = imageio_ffmpeg.get_ffmpeg_exe()
W, H, FPS, SR = 1080, 1920, 60, 48000
# JPEG frames are full-range BT.601; phones and browsers expect limited-range BT.709
VF = "scale=in_range=pc:out_range=tv:in_color_matrix=bt601:out_color_matrix=bt709,format=yuv420p"
TAGS = ["-color_range", "tv", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709"]

# ---------------------------------------------------------------- the cut
# (take, first frame, end frame, caption card, options). Frames are the take's
# own numbers (60 per second). A caption runs across every consecutive segment
# that names it.
CUT = [
    ("ember", 0, 150, "01_hook", {}),                    # the crowd closes in from every side
    ("alone", 20, 230, "02_alone", {}),                  # no taps: the archer works, the coins tick
    ("ember", 515, 640, "03_spend", {}),                 # Damage bought twice
    ("ember", 140, 215, "04_abilities", {}),             # Arrow Rain on the bunched crowd
    ("frost", 72, 118, "04_abilities", {}),              # Frost Snare
    ("frost", 158, 205, "04_abilities", {}),             # Lightning on the yeti
    ("frost", 243, 305, "04_abilities", {}),             # Poison Cloud
    ("storm", 62, 150, "05_contraption", {}),            # the Storm Rod arcs down a column
    ("ballista", 105, 195, "05_contraption", {}),        # the Ballista spear through a line
    ("boss", 268, 440, "06_boss", {}),                   # SLAM, Mega Gust, BROKEN, Lightning
    # the helm drops and is picked up (a gentle push, the item's name still fits),
    # then in on the archer as it goes on
    ("boss", 440, 580, "07_gear", {"zoom": [(455, 1.0, 540, 960), (482, 1.2, 545, 700), (496, 1.2, 545, 700), (522, 2.2, 545, 470)]}),
    ("gear", 38, 200, "07_gear", {}),                    # the gear screen: a set cloak equipped
    ("blizzard", 60, 122, "08_lands", {}),               # Frostpeak's blizzard
    ("rise", 52, 178, "08_lands", {}),                   # the dead get back up
    ("cinder", 110, 172, "08_lands", {}),                # Cinderdeep's lava hounds
    ("nightmare", 96, 160, "08_lands", {}),              # the Nightmare lap
]
END_FRAMES = 210        # the end card, 3.5 s
END_XFADE = 18          # last shot dissolves into it
CAPTION_FADE = 6

# the site loop: Emberwood, crowd to Arrow Rain to the fight. The field only:
# below the pause button and wave header, above the ability bar, scaled to the
# figure's 1080x1180
LOOP = ("ember", 0, 560, (25, 130, 1055, 1255), 30)  # take, in, out, crop box, xfade frames
LOOP_SIZE = (1080, 1180)

# ---------------------------------------------------------------- helpers


def frame(take, n):
    return Image.open(os.path.join(TAKES, take, "f_%05d.jpg" % n)).convert("RGB")


def read_log(take, name):
    rows = []
    p = os.path.join(TAKES, take, name)
    if os.path.exists(p):
        for line in open(p).read().splitlines():
            parts = line.split()
            if parts:
                rows.append(parts)
    return rows


def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


# a finger's tap: a soft dot while it presses, a ring that opens and fades
RING_FRAMES = 20
_ring_cache = {}


def ring_sprite(age):
    if age in _ring_cache:
        return _ring_cache[age]
    s = 4  # supersample
    size = 200
    im = Image.new("RGBA", (size * s, size * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = size * s / 2
    k = age / RING_FRAMES
    r = (30 + 44 * ease(k)) * s
    a = int(245 * (1 - k) ** 1.3)
    wd = int(10 * s * (1 - 0.45 * k))
    d.ellipse([c - r - 3 * s, c - r - 3 * s, c + r + 3 * s, c + r + 3 * s], outline=(30, 18, 8, int(a * 0.55)), width=wd + 6 * s)
    d.ellipse([c - r, c - r, c + r, c + r], outline=(255, 255, 255, a), width=wd)
    if age < 10:
        rd = (27 - age) * s
        d.ellipse([c - rd - 2 * s, c - rd - 2 * s, c + rd + 2 * s, c + rd + 2 * s], fill=(30, 18, 8, int(70 * (1 - age / 10))))
        d.ellipse([c - rd, c - rd, c + rd, c + rd], fill=(255, 255, 255, int(150 * (1 - age / 10))))
    im = im.resize((size, size), Image.LANCZOS)
    shadow = im.split()[3].filter(ImageFilter.GaussianBlur(4)).point(lambda v: v * 0.45)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste((0, 0, 0, 255), (0, 2), shadow)
    out.alpha_composite(im)
    _ring_cache[age] = out
    return out


def draw_taps(im, taps, n):
    """taps: [(frame the press shows, x, y)]. The finger lands 3 frames before."""
    for f0, x, y in taps:
        age = n - (f0 - 3)
        if 0 <= age < RING_FRAMES:
            sp = ring_sprite(age)
            im.alpha_composite(sp, (int(x - sp.width / 2), int(y - sp.height / 2)))


def zoomed(im, n, keys):
    """keys: [(frame, zoom, centre x, centre y)], eased between keyframes."""
    if n <= keys[0][0]:
        z, cx, cy = keys[0][1:]
    elif n >= keys[-1][0]:
        z, cx, cy = keys[-1][1:]
    else:
        for (f0, z0, x0_, y0_), (f1, z1, x1_, y1_) in zip(keys, keys[1:]):
            if f0 <= n <= f1:
                k = ease((n - f0) / max(1, f1 - f0))
                z, cx, cy = z0 + (z1 - z0) * k, x0_ + (x1_ - x0_) * k, y0_ + (y1_ - y0_) * k
                break
    if z <= 1.0001:
        return im
    cw, ch = W / z, H / z
    x0 = min(max(cx - cw / 2, 0), W - cw)
    y0 = min(max(cy - ch / 2, 0), H - ch)
    return im.crop((x0, y0, x0 + cw, y0 + ch)).resize((W, H), Image.LANCZOS)


# ---------------------------------------------------------------- pictures


def build_frames():
    if os.path.isdir(EDIT):
        shutil.rmtree(EDIT)
    os.makedirs(EDIT)
    cards = {}
    # which output frames each caption spans
    spans, t = [], 0
    for take, a, b, cap, opt in CUT:
        if spans and spans[-1][0] == cap:
            spans[-1][2] = t + (b - a)
        else:
            spans.append([cap, t, t + (b - a)])
        t += b - a
    total_shots = t

    def caption_alpha(cap, n):
        for c, s0, s1 in spans:
            if c == cap and s0 <= n < s1:
                return min(1.0, (n - s0 + 1) / CAPTION_FADE if s0 > 0 else 1.0, (s1 - n) / CAPTION_FADE)
        return 0.0

    timeline = []  # (out frame, take, take frame) for the sound
    out_n = 0
    last = None
    for take, a, b, cap, opt in CUT:
        taps = [(int(r[0]), int(r[1]), int(r[2])) for r in read_log(take, "taps.txt")]
        if cap not in cards:
            cards[cap] = Image.open(os.path.join(CARDS, cap + ".png")).convert("RGBA")
        for n in range(a, b):
            im = frame(take, n).convert("RGBA")
            draw_taps(im, taps, n)
            if "zoom" in opt:
                im = zoomed(im, n, opt["zoom"])
            al = caption_alpha(cap, out_n)
            if al > 0:
                card = cards[cap]
                if al < 1:
                    card = card.copy()
                    card.putalpha(card.split()[3].point(lambda v, al=al: int(v * al)))
                im.alpha_composite(card)
            rgb = im.convert("RGB")
            rgb.save(os.path.join(EDIT, "%05d.jpg" % out_n), quality=95)
            last = rgb
            timeline.append((out_n, take, n))
            out_n += 1
        print("  %-10s %4d-%4d  -> %5.2fs" % (take, a, b, out_n / FPS))
    # the end card, the last shot dissolving into it, a slow push in
    end = Image.open(os.path.join(CARDS, "09_end.png")).convert("RGB")
    for i in range(END_FRAMES):
        z = 1 + 0.035 * (i / END_FRAMES)
        cw, ch = W / z, H / z
        im = end.crop(((W - cw) / 2, (H - ch) / 2, (W + cw) / 2, (H + ch) / 2)).resize((W, H), Image.LANCZOS)
        if i < END_XFADE:
            im = Image.blend(last, im, ease((i + 1) / END_XFADE))
        im.save(os.path.join(EDIT, "%05d.jpg" % out_n), quality=95)
        out_n += 1
    print("  end card -> %.2fs" % (out_n / FPS))
    return timeline, out_n, total_shots


# ---------------------------------------------------------------- sound

_clips = {}


def clip(path):
    if path not in _clips:
        raw = subprocess.run([FF, "-v", "error", "-i", os.path.join(GAME, path), "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"],
                             capture_output=True, check=True).stdout
        _clips[path] = np.frombuffer(raw, dtype=np.float32).reshape(-1, 2).copy()
    return _clips[path]


A = "Assets/Audio/Generated/"
R = "Assets/Resources/"
SFX = {
    "bow": A + "sfx_bow_shot_v3b.mp3", "impact": A + "sfx_arrow_impact_v2.mp3", "click": A + "sfx_ui_click.wav",
    "upgrade": A + "sfx_upgrade.wav", "zap": A + "sfx_storm_zap.wav", "ballista": A + "sfx_ballista_launch.wav",
    "lightning": A + "sfx_lightning.mp3", "frost": A + "sfx_frost_cast.mp3", "poison": A + "sfx_poison_cloud.mp3",
    "gust": A + "sfx_steam_vent.wav", "coin": A + "sfx_coin.wav",
    "Goblin": [A + "vo_goblin_death_a.mp3", A + "vo_goblin_death_b.mp3"],
    "Brute": [A + "vo_brute_death_a.mp3", A + "vo_brute_death_b.mp3"],
    "Undead": [A + "vo_undead_death_a.mp3", A + "vo_undead_death_b.mp3"],
    "land": R + "sfx_gear_drop_land.mp3", "pick": R + "sfx_gear_pick_magic.mp3", "equip": R + "sfx_gear_equip.mp3",
}
ANNOUNCE = {
    "Ability_ArrowRain": A + "vo_announce_arrowrain_loud.wav", "Ability_Frost": A + "vo_announce_frostsnare_loud.wav",
    "Ability_Lightning": A + "vo_announce_lightning_loud.wav", "Ability_Poison": A + "vo_announce_poison_loud.wav",
    "Ability_MegaGust": A + "vo_announce_megagust_loud.wav",
}
CAST = {"Ability_Frost": ("frost", 0.7), "Ability_Lightning": ("lightning", 0.8), "Ability_Poison": ("poison", 0.6),
        "Ability_MegaGust": ("gust", 0.8)}


def build_sound(timeline, total_frames):
    rng = random.Random(7)
    n_samples = int(total_frames / FPS * SR) + SR
    mix = np.zeros((n_samples, 2), dtype=np.float32)
    voice_gate = [-1.0]

    def put(path, at_frame, vol, pitch=True):
        if isinstance(path, list):
            path = rng.choice(path)
        x = clip(path)
        if pitch:
            p = rng.uniform(0.92, 1.08)
            idx = np.arange(0, len(x) - 1, p)
            x = np.stack([np.interp(idx, np.arange(len(x)), x[:, c]) for c in (0, 1)], axis=1).astype(np.float32)
        s0 = int(at_frame / FPS * SR)
        if s0 >= n_samples:
            return
        seg = x[: n_samples - s0] * vol
        mix[s0: s0 + len(seg)] += seg

    # take frame -> output frame(s)
    where = {}
    for out_n, take, n in timeline:
        where.setdefault((take, n), []).append(out_n)

    for take in sorted({t for _, t, _ in timeline}):
        for row in read_log(take, "events.txt"):
            n, kind = int(row[0]), row[1]
            for o in where.get((take, n), []):
                if kind == "shot":
                    put(SFX["bow"], o, 0.42)
                    if rng.random() < 0.7:
                        put(SFX["impact"], o + rng.randint(9, 14), 0.26)
                elif kind == "death":
                    fam = row[2] if len(row) > 2 else "Goblin"
                    boss = "boss" in row
                    t = o / FPS
                    if boss or t - voice_gate[0] >= 0.09:  # the game's voice throttle
                        voice_gate[0] = t
                        put(SFX.get(fam, SFX["Goblin"]), o, 0.6 if boss else 0.4)
                elif kind == "zap":
                    put(SFX["zap"], o, 0.5)
                elif kind == "ballista":
                    put(SFX["ballista"], o, 0.65)
                elif kind == "geardrop":
                    put(SFX["land"], o + 24, 0.4, pitch=False)
                elif kind == "gearpick":
                    put(SFX["pick"], o, 0.45, pitch=False)
                elif kind == "equip":
                    put(SFX["equip"], o, 0.5, pitch=False)
        for row in read_log(take, "taps.txt"):
            n, name = int(row[0]), row[3]
            for o in where.get((take, n), []):
                if name.startswith("Ability_"):
                    put(SFX["click"], o, 0.9)
                    if name in ANNOUNCE:
                        put(ANNOUNCE[name], o + 2, 0.9, pitch=False)
                    if name in CAST:
                        put(SFX[CAST[name][0]], o, CAST[name][1])
                    if name == "Ability_ArrowRain":
                        for k in range(9):
                            put(SFX["impact"], o + 8 + k * 5 + rng.randint(0, 3), 0.3)
                elif name.startswith("Upgrade_"):
                    put(SFX["upgrade"], o, 0.7)
                elif name.startswith("Item") or name.startswith("Cta_"):
                    put(SFX["click"], o, 0.8)

    # the music bed: Emberwood from the top, out over the end card (the game's 0.55)
    music = clip("Assets/Audio/Music/music_ch1_emberwood.wav")[: n_samples].copy()
    total_s = total_frames / FPS
    t = np.arange(len(music)) / SR
    gain = np.clip(t / 0.12, 0, 1) * np.clip((total_s - t) / 2.6, 0, 1)
    music *= (0.55 * gain)[:, None]
    bed = np.zeros_like(mix)
    bed[: len(music)] = music
    out = (mix + bed)[: int(total_s * SR)]
    mix[: int(total_s * SR)].astype(np.float32).tofile(os.path.join(EDIT, "sfx.f32"))  # QA: the game sound alone
    os.makedirs(OUT, exist_ok=True)
    raw = os.path.join(EDIT, "mix.f32")
    out.astype(np.float32).tofile(raw)
    wav = os.path.join(EDIT, "mix.wav")
    # loudness for phones and the platforms: -14 LUFS, peaks under -1.5 dBTP
    subprocess.run([FF, "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", raw,
                    "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", str(SR), wav], check=True)
    return wav


# ---------------------------------------------------------------- encode


def encode_trailer(wav):
    os.makedirs(OUT, exist_ok=True)
    out = os.path.join(OUT, "trailer-1080x1920.mp4")
    subprocess.run([FF, "-v", "error", "-y", "-framerate", str(FPS), "-i", os.path.join(EDIT, "%05d.jpg"), "-i", wav,
                    "-vf", VF, "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-profile:v", "high", *TAGS,
                    "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out], check=True)
    return out


def build_loop():
    take, a, b, box, xf = LOOP
    tmp = os.path.join(HERE, "build", "loop")
    if os.path.isdir(tmp):
        shutil.rmtree(tmp)
    os.makedirs(tmp)
    # 30 fps for the page: every other frame; the last xf frames dissolve into the
    # first ones, so the loop has no seam
    src = list(range(a, b, 2))
    xf //= 2
    body = src[xf:]
    for i, n in enumerate(body):
        im = frame(take, n).crop(box).resize(LOOP_SIZE, Image.LANCZOS)
        j = i - (len(body) - xf)
        if j >= 0:
            im = Image.blend(im, frame(take, src[j]).crop(box).resize(LOOP_SIZE, Image.LANCZOS), ease((j + 1) / (xf + 1)))
        im.save(os.path.join(tmp, "%05d.jpg" % i), quality=92)
    vid = os.path.join(SITE, "assets", "video")
    os.makedirs(vid, exist_ok=True)
    out = os.path.join(vid, "gameplay.mp4")
    subprocess.run([FF, "-v", "error", "-y", "-framerate", "30", "-i", os.path.join(tmp, "%05d.jpg"),
                    "-vf", VF, "-c:v", "libx264", "-preset", "slow", "-crf", "28", "-profile:v", "high", *TAGS,
                    "-an", "-movflags", "+faststart", out], check=True)
    # the poster: the crowd bunching as the rain lands
    poster = frame(take, 172).crop(box).resize(LOOP_SIZE, Image.LANCZOS)
    poster.save(os.path.join(SITE, "assets", "img", "gameplay-poster.webp"), quality=82, method=6)
    return out


if __name__ == "__main__":
    if "--loop" in sys.argv:
        print(" ", build_loop())
        sys.exit()
    print("frames")
    timeline, total, shots = build_frames()
    print("sound")
    wav = build_sound(timeline, total)
    print("encode")
    print(" ", encode_trailer(wav))
    print("loop")
    print(" ", build_loop())
