"""Das Produktions-Briefing: Skript, Szenen, Slides, Beitragstext.

Geschrieben entweder von Claude in der Routine (als JSON-Datei) oder,
wenn ein ANTHROPIC_API_KEY vorhanden ist, direkt über die Claude-API.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from .config import Settings

Format = Literal["video", "image", "carousel", "story", "none"]


class Block(BaseModel):
    index: int = Field(description="Laufende Nummer ab 1")
    narration: str = Field(description="Gesprochener Text auf Deutsch, max. 22 Wörter, natürlich gesprochen")
    footage_query: str = Field(description="2–4 englische Suchwörter für einen Stock-Clip, z.B. 'office inbox laptop morning'")
    scene_prompt: str = Field(default="", description="Englischer Prompt, falls der Clip per KI erzeugt wird")
    on_screen_text: str = Field(default="", description="Optional: 1–4 Wörter als Einblendung, sonst leer")


class Slide(BaseModel):
    index: int
    kind: Literal["cover", "content", "cta"]
    headline: str = Field(description="Kurz, max. 8 Wörter")
    body: str = Field(default="", description="1–3 kurze Sätze, bei cover leer oder Unterzeile")


class Brief(BaseModel):
    format: Format = Field(description="video | image | carousel | story | none")
    title: str
    hook: str = Field(description="Der erste Satz. Muss in zwei Sekunden neugierig machen.")
    blocks: list[Block] = Field(default_factory=list, description="Nur bei video: 4–7 Blöcke")
    slides: list[Slide] = Field(default_factory=list, description="Nur bei carousel: 7 Slides (cover, 5x content, cta)")
    image_headline: str = Field(default="", description="Bei image/story: Headline, max. 10 Wörter")
    image_subline: str = Field(default="", description="Bei image/story: eine Zeile darunter, optional")
    image_query: str = Field(default="", description="Bei image/story: englische Suchwörter für ein Hintergrundfoto, leer = reine Farbfläche")
    caption: str = Field(description="Beitragstext im Stil von Steffi, kurze Zeilen")
    hashtags: list[str] = Field(default_factory=list, description="3–6 Hashtags ohne #")
    platforms: list[str] = Field(default_factory=list, description="linkedin, instagram, tiktok")
    reasoning_summary: str = Field(default="")

    @property
    def total_words(self) -> int:
        return sum(len(b.narration.split()) for b in self.blocks)

    def caption_with_tags(self) -> str:
        tags = " ".join(f"#{h.lstrip('#')}" for h in self.hashtags)
        return f"{self.caption.strip()}\n\n{tags}".strip()


# Notion-Format → Briefing-Format
NOTION_FORMAT_MAP = {
    "video": "video", "reel": "video", "carousel": "carousel", "bild": "image",
    "story": "story", "post": "none", "poll": "none",
}


def format_from_notion(value: str | None) -> Format | None:
    if not value:
        return None
    return NOTION_FORMAT_MAP.get(value.strip().lower())  # type: ignore[return-value]


def system_prompt(settings: Settings) -> str:
    text = (settings.prompts_path / "brief_system.md").read_text(encoding="utf-8")
    v = settings.video
    return (text.replace("{{MIN_BLOCKS}}", str(v.min_blocks)).replace("{{MAX_BLOCKS}}", str(v.max_blocks))
            .replace("{{MAX_WORDS}}", str(v.max_words_per_block)).replace("{{TARGET_SECONDS}}", str(v.target_seconds))
            .replace("{{SLIDES}}", str(settings.carousel.slides)))


def json_schema() -> dict:
    return Brief.model_json_schema()


def make_brief_via_api(title: str, text: str, settings: Settings, force_format: str | None = None) -> Brief:
    """Briefing über die Claude-API (braucht ANTHROPIC_API_KEY)."""
    import anthropic

    client = anthropic.Anthropic()
    user = f"Titel: {title}\n\nBeitrag:\n\n{text.strip()}"
    if force_format:
        user += f"\n\nVorgabe: format = {force_format}."
    response = client.messages.parse(
        model=settings.llm.model, max_tokens=settings.llm.max_tokens, system=system_prompt(settings),
        output_config={"effort": settings.llm.effort},
        messages=[{"role": "user", "content": user}], output_format=Brief,
    )
    if response.stop_reason == "refusal":
        raise RuntimeError(f"Claude hat das Briefing abgelehnt: {getattr(response, 'stop_details', None)}")
    if response.parsed_output is None:
        raise RuntimeError("Claude hat kein gültiges Briefing geliefert.")
    return normalize(response.parsed_output, settings)


def normalize(brief: Brief, settings: Settings) -> Brief:
    v = settings.video
    if brief.format == "video":
        brief.blocks = brief.blocks[: v.max_blocks]
        for i, b in enumerate(brief.blocks, start=1):
            b.index = i
            words = b.narration.split()
            if len(words) > v.max_words_per_block + 6:
                b.narration = " ".join(words[: v.max_words_per_block + 6])
    if brief.format == "carousel":
        for i, s in enumerate(brief.slides, start=1):
            s.index = i
    brief.hashtags = [h.lstrip("#").strip() for h in brief.hashtags if h.strip()][:6]
    brief.platforms = [p.lower() for p in brief.platforms]
    return brief


def save_brief(brief: Brief, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(brief.model_dump(), indent=2, ensure_ascii=False), encoding="utf-8")


def load_brief(path: Path, settings: Settings | None = None) -> Brief:
    brief = Brief.model_validate(json.loads(path.read_text(encoding="utf-8")))
    return normalize(brief, settings) if settings else brief
