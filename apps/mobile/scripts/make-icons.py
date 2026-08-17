#!/usr/bin/env python3
"""
apps/mobile/scripts/make-icons.py
Generates the icon set from the brand tokens. Run it, don't hand-edit the PNGs.

    python scripts/make-icons.py

Why a script and not a folder of binaries: the brand colours live in
constants/theme.ts, the mark is a single letter, and every size is derived. A
committed generator means the next tweak is a one-line diff instead of six
opaque files nobody can regenerate.

The mark is a monogram, not the wordmark. "FinSight.ai" is ~11 characters; at
the 48px a browser tab gives you, or the ~20px a home-screen icon renders its
text at, a wordmark is a smudge. The monogram carries the same orange.

Orange fill rather than the app's dark background: a near-black icon disappears
into a dark wallpaper, which is what most of the target users have.
"""

import os

from PIL import Image, ImageDraw, ImageFont

ORANGE = "#FF6B00"          # COLORS.ORANGE
DARK = "#131313"            # COLORS.BACKGROUND
FONT = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"

HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.dirname(HERE)
ASSETS = os.path.join(APP, "assets")
PUBLIC = os.path.join(APP, "public")


def _fitted_font(draw, text, target_px, font_path=FONT):
    """Binary-search the point size whose cap height matches target_px."""
    lo, hi = 8, 2000
    while lo < hi:
        mid = (lo + hi + 1) // 2
        f = ImageFont.truetype(font_path, mid)
        box = draw.textbbox((0, 0), text, font=f)
        if (box[3] - box[1]) <= target_px:
            lo = mid
        else:
            hi = mid - 1
    return ImageFont.truetype(font_path, lo)


def glyph(size, bg, fg, text="F.", coverage=0.60):
    """Square icon with an optically centred monogram."""
    img = Image.new("RGBA", (size, size), bg if bg else (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font = _fitted_font(draw, text, int(size * coverage))
    box = draw.textbbox((0, 0), text, font=font)
    x = (size - (box[2] - box[0])) / 2 - box[0]
    y = (size - (box[3] - box[1])) / 2 - box[1]
    draw.text((x, y), text, font=font, fill=fg)
    return img


def wordmark(width, height, fg, bg=None, text="FinSight.ai"):
    img = Image.new("RGBA", (width, height), bg if bg else (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font = _fitted_font(draw, text, int(height * 0.30))
    box = draw.textbbox((0, 0), text, font=font)
    while (box[2] - box[0]) > width * 0.8:
        font = ImageFont.truetype(FONT, font.size - 2)
        box = draw.textbbox((0, 0), text, font=font)
    x = (width - (box[2] - box[0])) / 2 - box[0]
    y = (height - (box[3] - box[1])) / 2 - box[1]
    draw.text((x, y), text, font=font, fill=fg)
    return img


def main():
    os.makedirs(ASSETS, exist_ok=True)
    os.makedirs(PUBLIC, exist_ok=True)
    written = []

    def save(img, path):
        img.save(path)
        written.append(os.path.relpath(path, APP))

    # Native + PWA source. Full bleed: every platform applies its own mask.
    save(glyph(1024, ORANGE, DARK), os.path.join(ASSETS, "icon.png"))

    # Android adaptive foreground: transparent, glyph inside the 66% safe zone
    # so the launcher can crop to a circle without clipping the mark.
    save(glyph(1024, None, ORANGE, coverage=0.40),
         os.path.join(ASSETS, "adaptive-icon.png"))

    # Splash: resizeMode "contain" over backgroundColor #131313, so the wordmark
    # is legible here — this is the one place it has room.
    save(wordmark(1242, 500, ORANGE), os.path.join(ASSETS, "splash.png"))

    save(glyph(48, ORANGE, DARK), os.path.join(ASSETS, "favicon.png"))

    # Web. apple-touch-icon must be opaque: iOS composites transparency onto
    # black and the mark would vanish.
    save(glyph(180, ORANGE, DARK).convert("RGB"),
         os.path.join(PUBLIC, "apple-touch-icon.png"))
    save(glyph(192, ORANGE, DARK), os.path.join(PUBLIC, "icon-192.png"))
    save(glyph(512, ORANGE, DARK), os.path.join(PUBLIC, "icon-512.png"))

    # Maskable: Android crops up to 20% on each edge, so the glyph shrinks and
    # the orange runs to the bleed.
    save(glyph(512, ORANGE, DARK, coverage=0.40),
         os.path.join(PUBLIC, "icon-maskable-512.png"))

    save(glyph(512, DARK, ORANGE), os.path.join(PUBLIC, "icon-dark-512.png"))

    for path in written:
        print("wrote", path)


if __name__ == "__main__":
    main()
