"""The Hero Archer trailer at 16:9: Google Play's preview video.

    python trailer/make_trailer_wide.py [path-to-game-repo] [--stills]
        --stills  one frame from the middle of every shot and the end card, as a
                  contact sheet (build/wide-stills.jpg), to check the layout first

Why a second cut: the vertical trailer is a YouTube Short, and a game whose
preview video is vertical gets it as the first tile of the screenshot row and
nothing more. The games with a trailer playing across the top of their listing
(Archero, for one) link a regular 16:9 YouTube video. Google documents no
rule, but the header is a wide strip and a vertical video cannot fill it.
Keep the vertical cut on YouTube as the Short; link this one on Play.

Same cut, same sound and same captions as make_trailer.py (its CUT, timing,
taps and sound are imported, captions.py's words are read), laid out for
1920x1080:
  - battle shots crop the portrait take to a 16:9 band around the tower, so
    the fight fills the frame (the HUD below falls away). Play only autoplays
    the first 30 seconds, muted, and that is almost all battle.
  - screen shots (buying upgrades, the gear screen, the pass) keep the whole
    phone screen upright in the middle, on a blurred copy of itself, with the
    caption to its left and the logo to its right
  - captions sit at the left, vertically centred: the YouTube player's title
    bar covers the top, and its controls and Play's title overlay the bottom
  - the end card is the store's feature painting (game repo
    docs/release/store-assets/v29/source/feature_a_horde.png), so the video
    ends on its own cover image

The band is cut from the 1080-wide take and scaled up 1.78x: sharp at phone
size, a little soft full-screen on a desktop. Takes recorded at 2160x3840
(QaTrailerTakes.W/H) would make it native.

Writes trailer/build/out/trailer-1920x1080.mp4.
"""
import ast
import os
import shutil
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_trailer as mt  # noqa: E402  (the cut, the takes, the sound)

W, H = 1920, 1080
SW, SH = 1080, 1920           # the takes
FPS = mt.FPS
EDIT = os.path.join(HERE, "build", "edit_wide")
GAME = mt.GAME
LILITA = os.path.join(GAME, "Assets", "Fonts", "LilitaOne-Regular.ttf")
BALOO = os.path.join(GAME, "Assets", "Fonts", "Baloo2-ExtraBold.ttf")
LOGO = os.path.join(GAME, "Assets", "Art", "UI", "logo_hero_archer.png")
PAINTING = os.path.join(GAME, "docs", "release", "store-assets", "v29", "source", "feature_a_horde.png")

# captions.py's colours (the game's UIHex, Frostpeak Slate)
TITLE_TOP, TITLE_BOTTOM = (243, 249, 252), (182, 220, 240)
TEXT = (237, 242, 246)
OUTLINE = (8, 11, 14)
BAND = (14, 19, 23)

# the shots that show the phone's screen rather than the fight: (take, first frame) as in mt.CUT
SCREEN = {("ember", 515), ("gearcard", 20), ("gearcard", 470), ("gearcard", 612), ("pass", 30), ("pass", 272)}
# the band's centre in the take: the tower stands near y 520, the fight reaches down to ~900, the HUD
# starts near 1270. 600 keeps the archer, the tower and the fight below it.
BAND_CY = 600
# moves, as in mt.CUT's "zoom": (take frame, zoom, centre x, centre y) in take pixels. Gentler than the
# vertical cut's: the band is already scaled up 1.78x.
MOVES = {
    # the hook: the crowd marches in from below, so the band starts on it and rises to the lone archer as
    # it closes in (the band at 600 alone shows an empty field for the first second)
    ("ember", 0): [(0, 1.0, 540, 950), (125, 1.0, 540, 600)],
    ("boss", 630): [(640, 1.0, 540, 600), (657, 1.15, 550, 650), (672, 1.15, 550, 650), (712, 1.5, 540, 470)],
    ("skin", 60): [(60, 1.0, 540, 600), (235, 1.25, 540, 560)],
}

# the screen layout: the phone 608x1080 in the middle
PW = round(H * SW / SH)
PX = (W - PW) // 2


def load_captions():
    """captions.py's CAPTIONS, read without running it (running it rewrites the vertical cards)."""
    tree = ast.parse(open(os.path.join(HERE, "captions.py"), encoding="utf-8").read())
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", "") == "CAPTIONS" for t in node.targets):
            return {name: (head, sub) for name, head, sub in ast.literal_eval(node.value)}
    raise SystemExit("captions.py has no CAPTIONS")


# ---------------------------------------------------------------- type


def font_fit(text, path, start, min_size, max_w):
    size = start
    while size > min_size and ImageFont.truetype(path, size).getlength(text) > max_w:
        size -= 2
    f = ImageFont.truetype(path, size)
    return f if f.getlength(text) <= max_w else None


def lines_fit(text, path, start, min_size, max_w):
    """One line if it fits at min_size or more, else two balanced lines at one size."""
    f = font_fit(text, path, start, min_size, max_w)
    if f:
        return [text], f
    words = text.split()
    best = None
    for i in range(1, len(words)):
        a, b = " ".join(words[:i]), " ".join(words[i:])
        fa = font_fit(a, path, start, 20, max_w)
        fb = font_fit(b, path, start, 20, max_w)
        size = min(fa.size if fa else 20, fb.size if fb else 20)
        f = ImageFont.truetype(path, size)
        # the bigger size first, then a break after a comma, then the evener pair. Size wins over the
        # comma on purpose: "EVERY 5TH WAVE," fits only at 76 px, "EVERY 5TH" / "WAVE, A BOSS" at 92
        key = (size, a.endswith(","), -abs(f.getlength(a) - f.getlength(b)))
        if best is None or key > best[2]:
            best = (size, [a, b], key)
    return best[1], ImageFont.truetype(path, best[0])


def place(font, text, x, align, stroke):
    l, t, r, b = font.getbbox(text, stroke_width=stroke)
    w = r - l
    left = x - l if align == "left" else (x - w - l if align == "right" else round(x - w / 2) - l)
    return left, t, b - t


def title_text(canvas, x, y, text, font, align, stroke=8):
    """captions.py's title: the title gradient, a dark outline, a soft drop shadow."""
    left, t, h = place(font, text, x, align, stroke)
    top = y - t
    shadow = Image.new("L", canvas.size, 0)
    ImageDraw.Draw(shadow).text((left, top + 8), text, font=font, fill=200, stroke_width=stroke)
    canvas.paste(Image.new("RGBA", canvas.size, (0, 0, 0, 255)), (0, 0), shadow.filter(ImageFilter.GaussianBlur(6)))
    ImageDraw.Draw(canvas).text((left, top), text, font=font, fill=OUTLINE + (255,),
                                stroke_width=stroke, stroke_fill=OUTLINE + (255,))
    mask = Image.new("L", canvas.size, 0)
    ImageDraw.Draw(mask).text((left, top), text, font=font, fill=255)
    grad = Image.new("RGBA", canvas.size)
    gd = ImageDraw.Draw(grad)
    for i in range(h + 1):
        k = i / max(1, h)
        gd.line([(0, y + i), (canvas.width, y + i)],
                fill=tuple(round(TITLE_TOP[j] + (TITLE_BOTTOM[j] - TITLE_TOP[j]) * k) for j in range(3)) + (255,))
    canvas.paste(grad, (0, 0), mask)
    return y + h


def plain_text(canvas, x, y, text, font, fill, align, stroke=5):
    left, t, h = place(font, text, x, align, stroke)
    ImageDraw.Draw(canvas).text((left, y - t), text, font=font, fill=fill + (255,),
                                stroke_width=stroke, stroke_fill=OUTLINE + (255,))
    return y + h


def caption_block(head, sub, x, align, max_w, head_px, sub_px):
    """The caption as an RGBA layer, its block centred on the frame's height."""
    # one line only while it keeps most of its size; two big lines read better than one small one
    hl, hf = lines_fit(head, LILITA, head_px, round(head_px * 0.86), max_w)
    sl, sf = lines_fit(sub, BALOO, sub_px, 34, max_w) if sub else ([], None)
    gap_h, gap_s = 10, 8
    hh = [place(hf, t, 0, align, 8)[2] for t in hl]
    sh = [place(sf, t, 0, align, 5)[2] for t in sl] if sl else []
    total = sum(hh) + gap_h * (len(hh) - 1) + (22 + sum(sh) + gap_s * (len(sh) - 1) if sh else 0)
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    y = (H - total) // 2
    for t in hl:
        y = title_text(im, x, y, t, hf, align) + gap_h
    y += 22 - gap_h
    for t in sl:
        y = plain_text(im, x, y, t, sf, TEXT, align) + gap_s
    return im


def left_shade():
    """A dark wash from the left edge, so a caption reads over any battlefield."""
    g = Image.new("L", (W, 1), 0)
    for x in range(W):
        k = max(0.0, 1 - x / 1050)
        g.putpixel((x, 0), round(175 * k ** 1.6))
    a = g.resize((W, H))
    im = Image.new("RGBA", (W, H), BAND + (0,))
    im.putalpha(a)
    return im


# ---------------------------------------------------------------- layouts


def keyed(n, keys):
    if n <= keys[0][0]:
        return keys[0][1:]
    if n >= keys[-1][0]:
        return keys[-1][1:]
    for (f0, z0, x0, y0), (f1, z1, x1, y1) in zip(keys, keys[1:]):
        if f0 <= n <= f1:
            k = mt.ease((n - f0) / max(1, f1 - f0))
            return z0 + (z1 - z0) * k, x0 + (x1 - x0) * k, y0 + (y1 - y0) * k


def band(im, n, keys):
    z, cx, cy = keyed(n, keys) if keys else (1.0, SW / 2, BAND_CY)
    cw = SW / z
    ch = cw * H / W
    x0 = min(max(cx - cw / 2, 0), SW - cw)
    y0 = min(max(cy - ch / 2, 0), SH - ch)
    return im.crop((x0, y0, x0 + cw, y0 + ch)).resize((W, H), Image.LANCZOS)


_phone_shadow = None
_side_logo = None


def screen(im):
    global _phone_shadow, _side_logo
    if _phone_shadow is None:
        s = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(s).rectangle((PX - 6, -40, PX + PW + 6, H + 40), fill=(0, 0, 0, 200))
        _phone_shadow = s.filter(ImageFilter.GaussianBlur(28))
        lg = Image.open(LOGO).convert("RGBA")
        lw = 500
        _side_logo = lg.resize((lw, round(lg.height * lw / lg.width)), Image.LANCZOS)
    # the backdrop: the same screen, blown up, blurred and darkened (blurred small, for speed)
    small = im.resize((480, 853), Image.BILINEAR).crop((0, 100, 480, 370)).filter(ImageFilter.GaussianBlur(10))
    bg = Image.blend(small.resize((W, H), Image.BILINEAR), Image.new("RGB", (W, H), BAND), 0.6).convert("RGBA")
    bg.alpha_composite(_phone_shadow)
    bg.paste(im.resize((PW, H), Image.LANCZOS), (PX, 0))
    rx = PX + PW + (W - PX - PW - _side_logo.width) // 2
    bg.alpha_composite(_side_logo, (rx, (H - _side_logo.height) // 2))
    return bg


def end_card():
    """The feature painting, its 16:9 share kept to the right (the tower, the ogre, the horde), the logo and
    the line on the calm sky to the left."""
    p = Image.open(PAINTING).convert("RGB")
    cw = round(p.height * W / H)
    p = p.crop((p.width - cw, 0, p.width, p.height)).resize((W, H), Image.LANCZOS).convert("RGBA")
    shade = left_shade()
    p.alpha_composite(shade)
    lg = Image.open(LOGO).convert("RGBA")
    lw = 600
    lg = lg.resize((lw, round(lg.height * lw / lg.width)), Image.LANCZOS)
    sh = Image.new("RGBA", lg.size, (0, 0, 0, 0))
    sh.putalpha(lg.getchannel("A").point(lambda a: a * 0.5))
    x = 80
    y = 200
    p.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)), (x + 4, y + 10))
    p.alpha_composite(lg, (x, y))
    y += lg.height + 40
    cx = x + lw // 2
    y = title_text(p, cx, y, "GOOD HUNTING, HERO", font_fit("GOOD HUNTING, HERO", LILITA, 76, 40, lw + 40), "center")
    plain_text(p, cx, y + 26, "Free on Google Play", font_fit("Free on Google Play", BALOO, 48, 30, lw), TEXT, "center")
    return p.convert("RGB")


# ---------------------------------------------------------------- the cut


def plan():
    """mt.CUT with each segment's layout, and the output frames each caption spans (as mt.build_frames)."""
    spans, t = [], 0
    for take, a, b, cap, opt in mt.CUT:
        if spans and spans[-1][0] == cap:
            spans[-1][2] = t + (b - a)
        else:
            spans.append([cap, t, t + (b - a)])
        t += b - a
    return spans


def build_overlays(caps):
    shade = left_shade()
    out = {}
    for take, a, b, cap, opt in mt.CUT:
        if cap in out:
            continue
        head, sub = caps[cap]
        if (take, a) in SCREEN:
            out[cap] = caption_block(head, sub, PX - 56, "right", PX - 110, 76, 42)
        else:
            im = shade.copy()
            # 84..690: the tower stands from ~720 to ~1200 in the band
            im.alpha_composite(caption_block(head, sub, 84, "left", 606, 92, 46))
            out[cap] = im
    return out


def render(take, a, n, opt, overlay, al, taps, swipes):
    im = mt.frame(take, n).convert("RGBA")
    mt.draw_taps(im, taps, n)
    mt.draw_swipes(im, swipes, n)
    if (take, a) in SCREEN:
        im = screen(im.convert("RGB"))
    else:
        im = band(im, n, MOVES.get((take, a))).convert("RGBA")
    if al > 0:
        card = overlay
        if al < 1:
            card = card.copy()
            card.putalpha(card.split()[3].point(lambda v, al=al: int(v * al)))
        im.alpha_composite(card)
    return im.convert("RGB")


def logs(take):
    taps = [(int(r[0]), int(r[1]), int(r[2])) for r in mt.read_log(take, "taps.txt")]
    swipes = [(int(r[0]), int(r[2]), int(r[3]), int(r[4]), int(r[5])) for r in mt.read_log(take, "events.txt")
              if len(r) >= 6 and r[1] == "swipe"]
    return taps, swipes


def caption_alpha(spans, cap, n):
    for c, s0, s1 in spans:
        if c == cap and s0 <= n < s1:
            return min(1.0, (n - s0 + 1) / mt.CAPTION_FADE if s0 > 0 else 1.0, (s1 - n) / mt.CAPTION_FADE)
    return 0.0


def stills():
    caps = load_captions()
    overlays = build_overlays(caps)
    spans = plan()
    tiles, out_n = [], 0
    for take, a, b, cap, opt in mt.CUT:
        n = (a + b) // 2
        taps, swipes = logs(take)
        tiles.append(render(take, a, n, opt, overlays[cap], 1.0, taps, swipes))
        out_n += b - a
    tiles.append(end_card())
    cols = 4
    tw, th = W // 4, H // 4
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * (tw + 8), rows * (th + 8)), (40, 40, 40))
    for i, t in enumerate(tiles):
        sheet.paste(t.resize((tw, th), Image.LANCZOS), ((i % cols) * (tw + 8), (i // cols) * (th + 8)))
    path = os.path.join(HERE, "build", "wide-stills.jpg")
    sheet.save(path, quality=88)
    for i, t in enumerate(tiles):
        t.save(os.path.join(HERE, "build", "wide-still-%02d.jpg" % i), quality=90)
    print(" ", path)


def build_frames():
    if os.path.isdir(EDIT):
        shutil.rmtree(EDIT)
    os.makedirs(EDIT)
    caps = load_captions()
    overlays = build_overlays(caps)
    spans = plan()
    timeline, out_n, last = [], 0, None
    del mt.BOSS_SPANS[:]
    for take, a, b, cap, opt in mt.CUT:
        if opt.get("music") == "boss":
            mt.BOSS_SPANS.append((out_n, out_n + (b - a)))
        taps, swipes = logs(take)
        for n in range(a, b):
            rgb = render(take, a, n, opt, overlays[cap], caption_alpha(spans, cap, out_n), taps, swipes)
            rgb.save(os.path.join(EDIT, "%05d.jpg" % out_n), quality=95)
            last = rgb
            timeline.append((out_n, take, n))
            out_n += 1
        print("  %-10s %4d-%4d  -> %5.2fs" % (take, a, b, out_n / FPS))
    end = end_card()
    for i in range(mt.END_FRAMES):
        z = 1 + 0.035 * (i / mt.END_FRAMES)
        cw, ch = W / z, H / z
        im = end.crop(((W - cw) / 2, (H - ch) / 2, (W + cw) / 2, (H + ch) / 2)).resize((W, H), Image.LANCZOS)
        if i < mt.END_XFADE:
            im = Image.blend(last, im, mt.ease((i + 1) / mt.END_XFADE))
        im.save(os.path.join(EDIT, "%05d.jpg" % out_n), quality=95)
        out_n += 1
    print("  end card -> %.2fs" % (out_n / FPS))
    return timeline, out_n


def encode(wav):
    os.makedirs(mt.OUT, exist_ok=True)
    out = os.path.join(mt.OUT, "trailer-1920x1080.mp4")
    subprocess.run([mt.FF, "-v", "error", "-y", "-framerate", str(FPS), "-i", os.path.join(EDIT, "%05d.jpg"), "-i", wav,
                    "-vf", mt.VF, "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-profile:v", "high", *mt.TAGS,
                    "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out], check=True)
    return out


if __name__ == "__main__":
    if "--stills" in sys.argv:
        stills()
        sys.exit()
    print("frames")
    timeline, total = build_frames()
    print("sound")
    mt.EDIT = EDIT  # the mix files go beside these frames, not the vertical cut's
    wav = mt.build_sound(timeline, total)
    print("encode")
    print(" ", encode(wav))
