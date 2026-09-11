"""Untertitel im Marken-Look als ASS-Datei (wortweise hervorgehoben)."""
from __future__ import annotations

from pathlib import Path

from .config import Settings
from .media import hex_to_ass
from .voice import Word


def _ts(seconds: float) -> str:
    seconds = max(0.0, seconds)
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def _escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("{", "(").replace("}", ")")


def _chunks(words: list[Word], size: int, max_chars: int = 18) -> list[list[Word]]:
    """Gruppiert Wörter zu kurzen Einblendungen: höchstens `size` Wörter und `max_chars` Zeichen."""
    out, cur, chars = [], [], 0
    for w in words:
        if cur and (len(cur) >= size or chars + 1 + len(w.text) > max_chars):
            out.append(cur)
            cur, chars = [], 0
        cur.append(w)
        chars += len(w.text) + (1 if len(cur) > 1 else 0)
        if w.text[-1:] in ".!?:":
            out.append(cur)
            cur, chars = [], 0
    if cur:
        out.append(cur)
    return out


def build_ass(words: list[Word], settings: Settings, overlays: list[tuple[float, float, str]] | None = None) -> str:
    """Erzeugt ASS-Untertitel. `overlays` = (start, ende, text) für Einblendungen."""
    v = settings.video
    c = settings.brand.colors
    font = settings.brand.font_body
    size = int(v.width * 0.08)
    margin_v = int(v.height * 0.22)
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {v.width}
PlayResY: {v.height}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,{font},{size},{hex_to_ass(c.cream)},{hex_to_ass(c.salmon)},{hex_to_ass(c.burgundy)},{hex_to_ass(c.burgundy, 0x40)},-1,0,0,0,100,100,1,0,1,{max(2, size // 11)},{max(2, size // 12)},2,60,60,{margin_v},1
Style: Overlay,{settings.brand.font_headline},{int(v.width * 0.085)},{hex_to_ass(c.cream)},{hex_to_ass(c.cream)},{hex_to_ass(c.burgundy)},{hex_to_ass(c.burgundy, 0x40)},-1,0,0,0,100,100,0,0,1,{max(2, size // 14)},{max(2, size // 12)},8,80,80,{int(v.height * 0.14)},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = []
    highlight = hex_to_ass(c.salmon).replace("&H00", "&H")
    base = hex_to_ass(c.cream).replace("&H00", "&H")
    if v.captions == "word":
        for chunk in _chunks(words, v.caption_words_per_chunk):
            for i, w in enumerate(chunk):
                parts = []
                for j, other in enumerate(chunk):
                    txt = _escape(other.text.upper())
                    parts.append(f"{{\\c{highlight}}}{txt}{{\\c{base}}}" if j == i else txt)
                end = chunk[i + 1].start if i + 1 < len(chunk) else w.end
                lines.append(f"Dialogue: 0,{_ts(w.start)},{_ts(max(end, w.start + 0.05))},Caption,,0,0,0,,{' '.join(parts)}")
    elif v.captions == "line":
        for chunk in _chunks(words, max(4, v.caption_words_per_chunk + 1)):
            text = " ".join(_escape(w.text.upper()) for w in chunk)
            lines.append(f"Dialogue: 0,{_ts(chunk[0].start)},{_ts(chunk[-1].end)},Caption,,0,0,0,,{text}")
    for start, end, text in overlays or []:
        lines.append(f"Dialogue: 1,{_ts(start)},{_ts(end)},Overlay,,0,0,0,,{{\\fad(200,200)}}{_escape(text)}")
    return header + "\n".join(lines) + "\n"


def write_ass(words: list[Word], settings: Settings, out: Path,
              overlays: list[tuple[float, float, str]] | None = None) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build_ass(words, settings, overlays), encoding="utf-8")
    return out
