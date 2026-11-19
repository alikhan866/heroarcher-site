"""Rebuild every image, font and video the site serves from the game repo.

    python tools/build_assets.py [path-to-game-repo]

The game repo defaults to ../Evil-archer next to this repo. Output overwrites
assets/ and the root icons, so re-run it whenever the game art changes.
Needs Pillow and fontTools + brotli.
"""
import os
import sys

from PIL import Image

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(SITE, "..", "Evil-archer"))
IMG = os.path.join(SITE, "assets", "img")
FONTS = os.path.join(SITE, "assets", "fonts")
for d in (IMG, FONTS):
    os.makedirs(d, exist_ok=True)


def game(*parts):
    return os.path.join(GAME, *parts)


def webp(im, name, width=None, quality=82):
    """Save `im` (optionally downscaled to `width`) as assets/img/<name>.webp."""
    if width and im.width > width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    path = os.path.join(IMG, name + ".webp")
    im.save(path, "WEBP", quality=quality, method=6)
    print(f"  {name}.webp  {im.width}x{im.height}  {os.path.getsize(path) // 1024} KB")
    return im


def trimmed(path):
    im = Image.open(path).convert("RGBA")
    return im.crop(im.getbbox())


print("images")
logo = Image.open(game("Assets", "Art", "UI", "logo_hero_archer.png")).convert("RGBA")
webp(logo, "logo-912", quality=88)
webp(logo, "logo-456", 456, quality=88)

# The home screen's tower with the archer on it, put together the way the game
# does it (Assets/Scripts/UI/MenuArcherDoll.cs): the empty-deck tower painting,
# shown 500 UI units wide, and the archer's 512 canvas drawn 250 units square
# with its centre at (0, 184) from the tower's centre. Frame 06 of the front
# shoot strip has an arrow nocked.
tower = Image.open(game("Assets", "Resources", "hero_menu_tower.png")).convert("RGBA")
k = tower.width / 500.0
size = round(250 * k)
cx, cy = tower.width / 2.0, tower.height / 2.0 - 184 * k
pad = 140
canvas = Image.new("RGBA", (tower.width, tower.height + pad), (0, 0, 0, 0))
canvas.alpha_composite(tower, (0, pad))
archer = Image.open(game("Assets", "Art", "Generated", "Archer", "archer_front_shoot_06.png")).convert("RGBA")
archer = archer.resize((size, size), Image.LANCZOS)
canvas.alpha_composite(archer, (round(cx - size / 2), round(cy + pad - size / 2)))
canvas = canvas.crop(canvas.getbbox())
webp(canvas, "tower-archer-552", quality=80)
webp(canvas, "tower-archer-360", 360, quality=80)

dusk = Image.open(game("Assets", "Art", "Generated", "menu_bg_battle.png")).convert("RGB")
webp(dusk, "dusk-832", quality=80)
webp(dusk, "dusk-480", 480, quality=80)

forest = Image.open(game("Assets", "Art", "UI", "app_icon_bg.png")).convert("RGB")
webp(forest, "forest-1024", quality=74)

for src, name in [
    (("Assets", "Art", "Generated", "bg_forest_sunny.png"), "ch-emberwood"),
    (("Assets", "Art", "Generated", "bg_frostpeak_v2.png"), "ch-frostpeak"),
    (("Assets", "Art", "Generated", "bg_desert_necropolis_v3.png"), "ch-necropolis"),
    (("Assets", "Art", "Generated", "Ch4", "bg_cinderdeep_v2.png"), "ch-cinderdeep"),
]:
    im = Image.open(game(*src)).convert("RGB")
    webp(im, name + "-768", 768, quality=78)
    webp(im, name + "-400", 400, quality=78)

# The screenshot rail: whole 1080x1920 screens from the current build
# (docs/release/store-assets/site, captured 2026-11-19 with trailer/unity: the
# boss and Storm Rod frames come from the still_boss and still_storm takes, the
# contraption pick and the gear screen are single captures).
for src, name in [("shot_boss", "shot-boss"), ("shot_storm", "shot-storm"),
                  ("shot_pick", "shot-contraption"), ("shot_gear", "shot-gear")]:
    im = Image.open(game("docs", "release", "store-assets", "site", src + ".png")).convert("RGB")
    webp(im, name + "-720", 720, quality=82)
    webp(im, name + "-360", 360, quality=80)


for src, name in [("ability_arrow_rain", "ico-arrow-rain"), ("icon_workshop", "ico-workshop"),
                  ("icon_chest", "ico-chest"), ("icon_trophy", "ico-trophy")]:
    webp(trimmed(game("Assets", "Art", "Icons", src + ".png")), name, 112, quality=90)

troll = trimmed(game("Assets", "Art", "Generated", "enemy_boss.png"))
# The sprite keeps a patch of its old white background in the gap between the
# club arm and the body (around x 139-148, y 164-219 of the trimmed sprite).
# Clear it there only, so the teeth and eyes keep their highlights.
px = troll.load()
cleared = set()
for y in range(150, 232):
    for x in range(124, 170):
        r, g, b, a = px[x, y]
        if a and min(r, g, b) > 200:
            px[x, y] = (r, g, b, 0)
            cleared.add((x, y))
# then feather the pale fringe the patch leaves behind, within 3 px of it
for y in range(147, 235):
    for x in range(121, 173):
        r, g, b, a = px[x, y]
        lo = min(r, g, b)
        if not a or lo <= 110 or (x, y) in cleared:
            continue
        if any((x + dx, y + dy) in cleared for dx in range(-3, 4) for dy in range(-3, 4)):
            px[x, y] = (r, g, b, round(a * max(0.0, min(1.0, (175 - lo) / 65))))
webp(troll, "troll-478", quality=86)

print("icons")
icon = Image.open(game("docs", "release", "store-assets", "icon-512.png")).convert("RGB")
webp(icon, "icon-96", 96, quality=88)
icon.save(os.path.join(SITE, "icon-512.png"), optimize=True)
icon.resize((192, 192), Image.LANCZOS).save(os.path.join(SITE, "icon-192.png"), optimize=True)
icon.resize((180, 180), Image.LANCZOS).save(os.path.join(SITE, "apple-touch-icon.png"), optimize=True)
icon.save(os.path.join(SITE, "favicon.ico"), sizes=[(16, 16), (32, 32), (48, 48)])

# Link preview (Open Graph): the store feature graphic on the page colour.
feature = Image.open(game("docs", "release", "store-assets", "feature-graphic-1024x500.png")).convert("RGB")
feature = feature.resize((1200, round(500 * 1200 / 1024)), Image.LANCZOS)
og = Image.new("RGB", (1200, 630), (29, 21, 14))
og.paste(feature, (0, (630 - feature.height) // 2))
og.save(os.path.join(SITE, "og-image.jpg"), "JPEG", quality=86, optimize=True, progressive=True)

print("fonts")
from fontTools import subset  # noqa: E402
from fontTools.ttLib import TTFont  # noqa: E402

# Baloo 2 (OFL, no Reserved Font Name): the variable 400-800 font cut to Latin.
LATIN = ("U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+2000-206F,"
         "U+2074,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD")
out = os.path.join(FONTS, "baloo2-latin.woff2")
subset.main([game("Assets", "Fonts", "Baloo2.ttf"), f"--unicodes={LATIN}", "--flavor=woff2",
             "--layout-features=kern,liga,calt,locl", "--name-IDs=*", f"--output-file={out}"])
print(f"  baloo2-latin.woff2  {os.path.getsize(out) // 1024} KB")
# Lilita One carries the Reserved Font Name "Lilita One", so its glyphs stay
# untouched: only the container changes, TTF to WOFF2.
font = TTFont(game("Assets", "Fonts", "LilitaOne-Regular.ttf"))
font.flavor = "woff2"
out = os.path.join(FONTS, "lilita-one.woff2")
font.save(out)
print(f"  lilita-one.woff2  {os.path.getsize(out) // 1024} KB")

# The "how it plays" loop (assets/video/gameplay.mp4) and its poster come from
# the trailer recording: trailer/make_trailer.py, see trailer/PLAN.md.
print("done")
