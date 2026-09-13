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


def _rounded(img: Image.Image, radius: int) -> Image.Image:
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, img.size[0], img.size[1]], radius=radius, fill=255)
    out = Image.new("RGBA", img.size, (0, 0, 0, 0))
    out.paste(img.convert("RGB"), (0, 0), mask)
    return out


def editorial_card(settings: Settings, scene: Path, headline: str, body: str, out: Path,
                   size: tuple[int, int] = (1080, 1350)) -> Path:
    """Hook-Karte im DeskR-Look: zweifarbige Caps-Headline oben, Illustration/Szene in der Mitte,
    kurzer Fließtext plus Frage unten. Die Illustration kommt aus fal.ai (editorial oder mit Steffis Gesicht)."""
    c, b = settings.brand.colors, settings.brand
    W, H = size
    img = Image.new("RGB", (W, H), hex_to_rgb(c.cream))
    d = ImageDraw.Draw(img)
    margin = int(W * 0.08)
    max_width = W - 2 * margin

    # Headline: bis zu zwei farbige Sätze (Trennung an ". " / "! " / "? ")
    buf, parts = headline.strip(), []
    for sep in (". ", "! ", "? "):
        if sep in buf:
            i = buf.index(sep)
            parts = [buf[: i + 1].strip(), buf[i + 1:].strip()]
            break
    if not parts:
        parts = [buf]
    parts = [p for p in parts if p]
    colors = [hex_to_rgb(c.burgundy), hex_to_rgb(c.deep_salmon)]

    # Headline-Schriftgröße wählen: so groß wie möglich, aber höchstens 4 Zeilen insgesamt
    head_top, head_max_h = H * 0.055, H * 0.30
    for size_frac in (0.088, 0.078, 0.068, 0.058, 0.05, 0.044):
        head_font = _font(settings, b.font_body, int(W * size_frac), 800)
        line_h = head_font.size * 1.08
        total_lines = sum(len(_wrap(d, part.upper(), head_font, max_width)) for part in parts)
        if total_lines * line_h <= head_max_h or size_frac == 0.044:
            break

    y = head_top
    for i, part in enumerate(parts):
        for line in _wrap(d, part.upper(), head_font, max_width):
            d.text((margin, y), line, font=head_font, fill=colors[i % 2])
            y += line_h
        y += H * 0.006
    head_bottom = y + H * 0.018

    # Fußzeile fest am unteren Rand; Fließtext-Block bekommt den Rest
    footer_font = _font(settings, b.font_body, int(W * 0.026), 700)
    footer_y = H * 0.955
    body_bottom_max = footer_y - H * 0.025

    # Illustration: feste Höhe, direkt unter der Headline
    scene_h = min(H * 0.40, (body_bottom_max - head_bottom) * 0.62)
    scene_y = head_bottom
    scene_img = Image.open(scene).convert("RGB")
    sw, sh = scene_img.size
    scale = max(max_width / sw, scene_h / sh)
    scene_img = scene_img.resize((round(sw * scale), round(sh * scale)), Image.LANCZOS)
    left, top = (scene_img.width - max_width) // 2, (scene_img.height - int(scene_h)) // 2
    scene_img = scene_img.crop((left, top, left + max_width, top + int(scene_h)))
    rounded = _rounded(scene_img, int(W * 0.02))
    img.paste(rounded, (margin, int(scene_y)), rounded)

    # Fließtext: Schriftgröße wählen, damit er zwischen Illustration und Fußzeile passt
    line_y0 = scene_y + scene_h + H * 0.04
    body_max_h = body_bottom_max - line_y0 - H * 0.018
    paragraphs = [p.strip() for p in body.split("\n") if p.strip()]
    for size_frac in (0.036, 0.032, 0.028, 0.025, 0.022):
        body_font = _font(settings, b.font_body, int(W * size_frac), 500)
        line_h2 = body_font.size * 1.4
        n_lines = sum(len(_wrap(d, para, body_font, max_width)) for para in paragraphs)
        gaps = max(0, len(paragraphs) - 1) * H * 0.014
        if n_lines * line_h2 + gaps <= body_max_h or size_frac == 0.022:
            break

    d.line([(margin, line_y0), (margin + W * 0.12, line_y0)], fill=hex_to_rgb(c.salmon), width=4)
    ty = line_y0 + H * 0.028
    for para in paragraphs:
        for line in _wrap(d, para, body_font, max_width):
            d.text((margin, ty), line, font=body_font, fill=hex_to_rgb(c.burgundy))
            ty += line_h2
        ty += H * 0.014

    d.text((margin, footer_y), f"{b.name.upper()}   \u00b7   {b.handle}", font=footer_font, fill=hex_to_rgb(c.deep_salmon))
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, quality=95)
    return out
