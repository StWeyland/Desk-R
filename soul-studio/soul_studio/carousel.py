"""Carousel-Slides im Marken-Look (PNG je Slide + PDF für LinkedIn)."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

from .brief import Slide
from .config import Settings
from .images import _font, _wrap
from .media import hex_to_rgb


def _draw_wordmark(d: ImageDraw.ImageDraw, settings: Settings, W: int, H: int, color, index: int, total: int) -> None:
    b = settings.brand
    small = _font(settings, b.font_body, int(W * 0.026), 700)
    d.text((W * 0.08, H * 0.935), b.name.upper(), font=small, fill=color)
    counter = f"{index} / {total}"
    w = d.textlength(counter, font=small)
    d.text((W * 0.92 - w, H * 0.935), counter, font=small, fill=color)


def render_slide(slide: Slide, total: int, settings: Settings, out: Path) -> Path:
    c, b, cc = settings.brand.colors, settings.brand, settings.carousel
    W, H = cc.width, cc.height
    dark = slide.kind in {"cover", "cta"}
    bg = hex_to_rgb(c.burgundy) if dark else hex_to_rgb(c.cream)
    fg = hex_to_rgb(c.cream) if dark else hex_to_rgb(c.burgundy)
    accent = hex_to_rgb(c.salmon) if dark else hex_to_rgb(c.deep_salmon)
    img = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(img)

    if slide.kind == "cover":
        head = _font(settings, b.font_headline, int(W * 0.095), 600)
        sub = _font(settings, b.font_body, int(W * 0.034), 500)
        lines = _wrap(d, slide.headline, head, int(W * 0.84))
        y = H * 0.30
        for line in lines:
            d.text((W * 0.08, y), line, font=head, fill=fg)
            y += head.size * 1.12
        if slide.body:
            y += H * 0.02
            d.line([(W * 0.08, y), (W * 0.2, y)], fill=accent, width=4)
            y += H * 0.03
            for line in _wrap(d, slide.body, sub, int(W * 0.8)):
                d.text((W * 0.08, y), line, font=sub, fill=hex_to_rgb(c.pale_salmon))
                y += sub.size * 1.5
        arrow = _font(settings, b.font_body, int(W * 0.03), 700)
        d.text((W * 0.08, H * 0.86), "WISCHEN  →", font=arrow, fill=accent)
    elif slide.kind == "cta":
        head = _font(settings, b.font_headline, int(W * 0.078), 600)
        body = _font(settings, b.font_body, int(W * 0.036), 500)
        y = H * 0.3
        for line in _wrap(d, slide.headline, head, int(W * 0.84)):
            d.text((W * 0.08, y), line, font=head, fill=fg)
            y += head.size * 1.12
        y += H * 0.03
        for line in _wrap(d, slide.body, body, int(W * 0.8)):
            d.text((W * 0.08, y), line, font=body, fill=hex_to_rgb(c.pale_salmon))
            y += body.size * 1.5
        handle = _font(settings, b.font_body, int(W * 0.032), 700)
        d.text((W * 0.08, H * 0.8), f"{b.handle}  ·  {b.website}", font=handle, fill=accent)
    else:
        num = _font(settings, b.font_headline, int(W * 0.16), 400)
        d.text((W * 0.08, H * 0.09), f"{slide.index - 1:02d}", font=num, fill=hex_to_rgb(c.pale_salmon))
        head = _font(settings, b.font_headline, int(W * 0.072), 600)
        body = _font(settings, b.font_body, int(W * 0.038), 500)
        y = H * 0.32
        for line in _wrap(d, slide.headline, head, int(W * 0.84)):
            d.text((W * 0.08, y), line, font=head, fill=fg)
            y += head.size * 1.15
        y += H * 0.03
        d.line([(W * 0.08, y), (W * 0.18, y)], fill=accent, width=4)
        y += H * 0.035
        for line in _wrap(d, slide.body, body, int(W * 0.82)):
            d.text((W * 0.08, y), line, font=body, fill=hex_to_rgb(c.deep_salmon))
            y += body.size * 1.5
    _draw_wordmark(d, settings, W, H, accent, slide.index, total)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, quality=95)
    return out


def render_carousel(slides: list[Slide], settings: Settings, out_dir: Path) -> tuple[list[Path], Path]:
    total = len(slides)
    pngs = [render_slide(s, total, settings, out_dir / f"slide_{s.index:02d}.png") for s in slides]
    images = [Image.open(p).convert("RGB") for p in pngs]
    pdf = out_dir / "carousel.pdf"
    images[0].save(pdf, save_all=True, append_images=images[1:], resolution=150)
    return pngs, pdf
