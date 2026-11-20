"""Caption cards and the end card for the Hero Archer trailer.

    python trailer/captions.py [path-to-game-repo]

Writes transparent 1080x1920 PNGs to trailer/build/cards/, one per caption,
in the game's Frostpeak Slate style: a Lilita One headline in the title
colours (frost white to ice) with a dark slate outline and a frost-white Baloo 2
line under it, on a soft dark band near the top
(clear of the TikTok/Shorts buttons at the bottom and right). Also writes the
end card and a preview of every caption over a gameplay frame.
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
GAME = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "..", "Evil-archer"))
OUT = os.path.join(HERE, "build", "cards")
os.makedirs(OUT, exist_ok=True)

W, H = 1080, 1920
# the game's UIHex (Frostpeak Slate): Title, TitleBottom, Text, Deep; the band is
# the site's --bg
TITLE_TOP, TITLE_BOTTOM = (243, 249, 252), (182, 220, 240)
TEXT = (237, 242, 246)
OUTLINE = (8, 11, 14)
BAND = (14, 19, 23)

LILITA = os.path.join(GAME, "Assets", "Fonts", "LilitaOne-Regular.ttf")
BALOO = os.path.join(GAME, "Assets", "Fonts", "Baloo2-ExtraBold.ttf")

# The script: (file name, headline, line under it). Wording from the game's
# tutorial, codex and store copy. No em dashes.
CAPTIONS = [
    ("01_hook", "THE FOREST IS CRAWLING", ""),
    ("02_alone", "YOUR ARCHER FIGHTS ALONE", "Every kill pays coins"),
    ("03_spend", "SPEND THEM", "Damage first is never wrong"),
    ("04_abilities", "EIGHT ABILITIES", "Pick your moment"),
    ("05_contraption", "ONE CONTRAPTION PER RUN", "Storm Rod, Ballista, Barracks and more"),
    ("06_boss", "EVERY 5TH WAVE, A BOSS", "Break the windup before the axe falls"),
    ("07_gear", "DRESS YOUR ARCHER", "Boss loot shows up on your archer"),
    ("08_lands", "FOUR LANDS, 50 WAVES EACH", "Then the Nightmare lap"),
]


def fit(text, path, start, max_w):
    """Largest size from `start` down at which `text` fits in `max_w`."""
    size = start
    while size > 20:
        font = ImageFont.truetype(path, size)
        if font.getlength(text) <= max_w:
            return font
        size -= 2
    return ImageFont.truetype(path, size)


def title_text(canvas, xy, text, font, stroke=8):
    """Title-gradient text with a dark outline and a drop shadow, centred on xy."""
    x, y = xy
    l, t, r, b = font.getbbox(text, stroke_width=stroke)
    w, h = r - l, b - t
    left, top = round(x - w / 2) - l, y - t

    shadow = Image.new("L", canvas.size, 0)
    ImageDraw.Draw(shadow).text((left, top + 8), text, font=font, fill=200, stroke_width=stroke)
    shadow = shadow.filter(ImageFilter.GaussianBlur(6))
    canvas.paste(Image.new("RGBA", canvas.size, (0, 0, 0, 255)), (0, 0), shadow)

    ImageDraw.Draw(canvas).text((left, top), text, font=font, fill=OUTLINE + (255,),
                                stroke_width=stroke, stroke_fill=OUTLINE + (255,))
    mask = Image.new("L", canvas.size, 0)
    ImageDraw.Draw(mask).text((left, top), text, font=font, fill=255)
    grad = Image.new("RGBA", canvas.size)
    gd = ImageDraw.Draw(grad)
    for i in range(h + 1):
        k = i / max(1, h)
        c = tuple(round(TITLE_TOP[j] + (TITLE_BOTTOM[j] - TITLE_TOP[j]) * k) for j in range(3))
        gd.line([(0, y + i), (W, y + i)], fill=c + (255,))
    canvas.paste(grad, (0, 0), mask)
    return y + h


def plain_text(canvas, xy, text, font, fill, stroke=5):
    x, y = xy
    l, t, r, b = font.getbbox(text, stroke_width=stroke)
    ImageDraw.Draw(canvas).text((round(x - (r - l) / 2) - l, y - t), text, font=font, fill=fill + (255,),
                                stroke_width=stroke, stroke_fill=OUTLINE + (255,))
    return y + (b - t)


def band(height=400):
    """A soft dark band at the top so captions read over any battlefield."""
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for y in range(height):
        a = round(190 * (1 - (y / height) ** 2))
        d.line([(0, y), (W, y)], fill=BAND + (a,))
    return im


def caption_card(head, sub):
    im = band()
    # 170 px down clears the platforms' top bar; the tower starts near 390
    y = title_text(im, (W / 2, 170), head, fit(head, LILITA, 96, W - 140))
    if sub:
        plain_text(im, (W / 2, y + 22), sub, fit(sub, BALOO, 52, W - 160), TEXT)
    return im


def end_card():
    im = Image.new("RGBA", (W, H), BAND + (255,))
    dusk = Image.open(os.path.join(GAME, "Assets", "Art", "Generated", "menu_bg_battle.png")).convert("RGB")
    dusk = dusk.resize((W, round(dusk.height * W / dusk.width)), Image.LANCZOS).crop((0, 0, W, H))
    im.paste(dusk, (0, 0))
    im.alpha_composite(Image.new("RGBA", (W, H), BAND + (120,)))
    logo = Image.open(os.path.join(GAME, "Assets", "Art", "UI", "logo_hero_archer.png")).convert("RGBA")
    logo = logo.resize((860, round(logo.height * 860 / logo.width)), Image.LANCZOS)
    im.alpha_composite(logo, ((W - logo.width) // 2, 300))
    tower = Image.open(os.path.join(HERE, "..", "assets", "img", "tower-archer-552.webp")).convert("RGBA")
    tower = tower.resize((520, round(tower.height * 520 / tower.width)), Image.LANCZOS)
    im.alpha_composite(tower, ((W - tower.width) // 2, 820))
    y = title_text(im, (W / 2, 1640), "GOOD HUNTING, HERO", fit("GOOD HUNTING, HERO", LILITA, 92, W - 160))
    plain_text(im, (W / 2, y + 30), "Free on Google Play", fit("Free on Google Play", BALOO, 54, W - 200), TEXT)
    return im


cards = []
for name, head, sub in CAPTIONS:
    card = caption_card(head, sub)
    card.save(os.path.join(OUT, name + ".png"), optimize=True)
    cards.append(card)
    print("  card", name)
end = end_card()
end.convert("RGB").save(os.path.join(OUT, "09_end.png"), optimize=True)
print("  card 09_end")

# Preview: every caption over a clean gameplay frame, plus the end card.
frame = Image.open(os.path.join(GAME, "docs", "release", "store-assets", "raw", "shot_rain.png")).convert("RGBA")
thumbs = []
for card in cards + [end]:
    t = frame.copy()
    t.alpha_composite(card)
    thumbs.append(t.convert("RGB").resize((360, 640), Image.LANCZOS))
sheet = Image.new("RGB", (5 * 370, 2 * 650), (20, 20, 20))
for i, t in enumerate(thumbs):
    sheet.paste(t, ((i % 5) * 370 + 5, (i // 5) * 650 + 5))
sheet.save(os.path.join(HERE, "build", "captions-preview.jpg"), quality=86)
print("  preview build/captions-preview.jpg")
