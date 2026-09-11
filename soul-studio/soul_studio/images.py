"""Bildkomposition mit Pillow: Abspann-Karte und Bild-Postings mit Headline im Marken-Look."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from .config import Settings
from .media import hex_to_rgb


def _font(settings: Settings, family: str, size: int, weight: int = 700) -> ImageFont.FreeTypeFont:
    name = "PlayfairDisplay.ttf" if "Playfair" in family else "LeagueSpartan.ttf"
    path = settings.fonts_path / name
    try:
        font = ImageFont.truetype(str(path), size)
        try:
            font.set_variation_by_axes([weight])
        except Exception:
            pass
        return font
    except OSError:
        return ImageFont.load_default(size)


def _wrap(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = f"{cur} {w}".strip()
        if draw.textlength(trial, font=font) <= max_width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def end_card(settings: Settings, out: Path) -> Path:
    """Abspann: Burgunder-Fläche, Wortmarke in Playfair, Claim in League Spartan."""
    v, c, b = settings.video, settings.brand.colors, settings.brand
    img = Image.new("RGB", (v.width, v.height), hex_to_rgb(c.burgundy))
    d = ImageDraw.Draw(img)
    title_font = _font(settings, b.font_headline, int(v.width * 0.11), 600)
    sub_font = _font(settings, b.font_body, int(v.width * 0.036), 600)
    handle_font = _font(settings, b.font_body, int(v.width * 0.03), 500)
    title = v.end_card_text
    y = v.height * 0.42
    for line in _wrap(d, title, title_font, int(v.width * 0.84)):
        w = d.textlength(line, font=title_font)
        d.text(((v.width - w) / 2, y), line, font=title_font, fill=hex_to_rgb(c.cream))
        y += title_font.size * 1.1
    y += v.height * 0.015
    d.line([(v.width * 0.4, y), (v.width * 0.6, y)], fill=hex_to_rgb(c.salmon), width=3)
    y += v.height * 0.025
    sub = v.end_card_sub.upper()
    w = d.textlength(sub, font=sub_font)
    d.text(((v.width - w) / 2, y), sub, font=sub_font, fill=hex_to_rgb(c.pale_salmon))
    handle = f"{b.handle}  ·  {b.website}"
    w = d.textlength(handle, font=handle_font)
    d.text(((v.width - w) / 2, v.height * 0.9), handle, font=handle_font, fill=hex_to_rgb(c.salmon))
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, quality=95)
    return out


def image_post(settings: Settings, photo: Path, headline: str, out: Path, size: tuple[int, int] = (1080, 1350)) -> Path:
    """Bild-Posting: Soul-Foto, Verlauf unten, Headline in Playfair, Wortmarke klein."""
    c, b = settings.brand.colors, settings.brand
    W, H = size
    base = Image.open(photo).convert("RGB")
    scale = max(W / base.width, H / base.height)
    base = base.resize((round(base.width * scale), round(base.height * scale)), Image.LANCZOS)
    left, top = (base.width - W) // 2, (base.height - H) // 2
    img = base.crop((left, top, left + W, top + H))

    # Verlauf ins Burgunder für lesbaren Text
    gradient = Image.new("L", (1, H))
    for y in range(H):
        t = max(0.0, (y - H * 0.45) / (H * 0.55))
        gradient.putpixel((0, y), int(230 * t ** 1.4))
    overlay = Image.new("RGB", (W, H), hex_to_rgb(c.burgundy))
    img = Image.composite(overlay, img, gradient.resize((W, H)))

    d = ImageDraw.Draw(img)
    font = _font(settings, b.font_headline, int(W * 0.082), 600)
    lines = _wrap(d, headline, font, int(W * 0.84))
    line_h = font.size * 1.12
    y = H * 0.9 - line_h * len(lines) - H * 0.06
    for line in lines:
        d.text((W * 0.08, y), line, font=font, fill=hex_to_rgb(c.cream))
        y += line_h
    small = _font(settings, b.font_body, int(W * 0.028), 700)
    d.text((W * 0.08, H * 0.925), f"{b.name.upper()}   ·   {b.handle}", font=small, fill=hex_to_rgb(c.salmon))
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, quality=95)
    return out


def placeholder_frame(settings: Settings, out: Path, label: str = "") -> Path:
    """Für Tests ohne Higgsfield: ein weiches Farbfeld statt eines generierten Bildes."""
    v, c = settings.video, settings.brand.colors
    img = Image.new("RGB", (v.width, v.height), hex_to_rgb(c.tint))
    d = ImageDraw.Draw(img)
    d.ellipse([v.width * 0.2, v.height * 0.25, v.width * 0.8, v.height * 0.55], fill=hex_to_rgb(c.pale_salmon))
    img = img.filter(ImageFilter.GaussianBlur(6))
    if label:
        d = ImageDraw.Draw(img)
        f = _font(settings, settings.brand.font_body, 40, 600)
        d.text((60, 60), label, font=f, fill=hex_to_rgb(c.burgundy))
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)
    return out
