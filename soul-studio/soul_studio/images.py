"""Bildkomposition mit Pillow: Abspann, Bild-Postings, Stories, Platzhalter."""
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
    y = v.height * 0.42
    for line in _wrap(d, v.end_card_text, title_font, int(v.width * 0.84)):
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


def _fit_cover(photo: Path, W: int, H: int) -> Image.Image:
    base = Image.open(photo).convert("RGB")
    scale = max(W / base.width, H / base.height)
    base = base.resize((round(base.width * scale), round(base.height * scale)), Image.LANCZOS)
    left, top = (base.width - W) // 2, (base.height - H) // 2
    return base.crop((left, top, left + W, top + H))


def statement_image(settings: Settings, headline: str, subline: str, out: Path,
                    size: tuple[int, int] = (1080, 1350), photo: Path | None = None) -> Path:
    """Bild-Posting oder Story: Headline in Playfair auf Burgunder, optional mit Foto und Verlauf."""
    c, b = settings.brand.colors, settings.brand
    W, H = size
    if photo and photo.exists():
        img = _fit_cover(photo, W, H)
        gradient = Image.new("L", (1, H))
        for y in range(H):
            t = max(0.0, (y - H * 0.35) / (H * 0.65))
            gradient.putpixel((0, y), int(245 * t ** 1.3))
        overlay = Image.new("RGB", (W, H), hex_to_rgb(c.burgundy))
        img = Image.composite(overlay, img, gradient.resize((W, H)))
        text_color = hex_to_rgb(c.cream)
    else:
        img = Image.new("RGB", (W, H), hex_to_rgb(c.burgundy))
        text_color = hex_to_rgb(c.cream)
    d = ImageDraw.Draw(img)
    head = _font(settings, b.font_headline, int(W * 0.085), 600)
    sub = _font(settings, b.font_body, int(W * 0.036), 500)
    lines = _wrap(d, headline, head, int(W * 0.84))
    sub_lines = _wrap(d, subline, sub, int(W * 0.8)) if subline else []
    block_h = len(lines) * head.size * 1.12 + (len(sub_lines) * sub.size * 1.5 + H * 0.04 if sub_lines else 0)
    y = (H * 0.88 - block_h) if photo else (H - block_h) / 2 - H * 0.03
    for line in lines:
        d.text((W * 0.08, y), line, font=head, fill=text_color)
        y += head.size * 1.12
    if sub_lines:
        y += H * 0.03
        d.line([(W * 0.08, y), (W * 0.18, y)], fill=hex_to_rgb(c.salmon), width=4)
        y += H * 0.03
        for line in sub_lines:
            d.text((W * 0.08, y), line, font=sub, fill=hex_to_rgb(c.pale_salmon))
            y += sub.size * 1.5
    small = _font(settings, b.font_body, int(W * 0.028), 700)
    d.text((W * 0.08, H * 0.935), f"{b.name.upper()}   ·   {b.handle}", font=small, fill=hex_to_rgb(c.salmon))
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, quality=95)
    return out


def placeholder_frame(settings: Settings, out: Path, label: str = "") -> Path:
    """Für Tests ohne Internet: ein weiches Farbfeld statt eines Clips."""
    v, c = settings.video, settings.brand.colors
    img = Image.new("RGB", (v.width, v.height), hex_to_rgb(c.tint))
    d = ImageDraw.Draw(img)
    d.ellipse([v.width * 0.2, v.height * 0.25, v.width * 0.8, v.height * 0.55], fill=hex_to_rgb(c.pale_salmon))
    img = img.filter(ImageFilter.GaussianBlur(6))
    if label:
        d = ImageDraw.Draw(img)
        d.text((60, 60), label, font=_font(settings, settings.brand.font_body, 40, 600), fill=hex_to_rgb(c.burgundy))
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)
    return out
