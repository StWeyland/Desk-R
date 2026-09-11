"""Claude liest den Beitrag und schreibt das Produktions-Briefing (Skript + Szenen)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

import anthropic
from pydantic import BaseModel, Field

from .config import Settings
from .sources import Post


class Block(BaseModel):
    index: int = Field(description="Laufende Nummer ab 1")
    kind: Literal["talking", "broll"] = Field(
        description="talking = Steffi spricht in die Kamera; broll = Szene ohne Sprecherin im Bild, Stimme aus dem Off"
    )
    narration: str = Field(description="Gesprochener Text auf Deutsch, max. 22 Wörter, natürlich gesprochen")
    scene_prompt: str = Field(
        description="Englischer Bild-Prompt für die Szene. Ohne Text im Bild. Beschreibt Ort, Licht, Kamera, Handlung."
    )
    on_screen_text: str = Field(default="", description="Optional: 1–4 Wörter als Einblendung, sonst leer")


class VideoBrief(BaseModel):
    format: Literal["video", "image"] = Field(description="video für Kurzvideo, image für ein einzelnes Bild-Posting")
    title: str = Field(description="Kurzer Arbeitstitel")
    hook: str = Field(description="Der erste Satz. Muss in 2 Sekunden neugierig machen.")
    blocks: list[Block] = Field(description="Bei format=video: 4–7 Blöcke. Bei format=image: leer.")
    image_prompt: str = Field(default="", description="Bei format=image: englischer Prompt für das Bild mit Steffi")
    image_headline: str = Field(default="", description="Bei format=image: Headline als Text-Overlay, max. 8 Wörter")
    caption: str = Field(description="Beitragstext für TikTok/Instagram/LinkedIn im Stil von Steffi, 3–8 kurze Zeilen")
    hashtags: list[str] = Field(description="3–6 Hashtags ohne #")
    reasoning_summary: str = Field(default="", description="Ein Satz: warum dieses Format und dieser Aufbau")

    @property
    def total_words(self) -> int:
        return sum(len(b.narration.split()) for b in self.blocks)


def _system_prompt(settings: Settings) -> str:
    path = settings.prompts_path / "brief_system.md"
    text = path.read_text(encoding="utf-8")
    v = settings.video
    return (
        text.replace("{{MIN_BLOCKS}}", str(v.min_blocks))
        .replace("{{MAX_BLOCKS}}", str(v.max_blocks))
        .replace("{{MAX_WORDS}}", str(v.max_words_per_block))
        .replace("{{TARGET_SECONDS}}", str(v.target_seconds))
        .replace("{{MODE}}", v.mode)
        .replace("{{LOOK}}", settings.character.look)
        .replace("{{SETTING}}", settings.character.setting)
    )


def make_brief(post: Post, settings: Settings, force_format: str | None = None) -> VideoBrief:
    client = anthropic.Anthropic()
    user = f"Titel: {post.title}\n\nBeitrag:\n\n{post.text.strip()}"
    if force_format:
        user += f"\n\nVorgabe: format = {force_format}."
    response = client.messages.parse(
        model=settings.llm.model,
        max_tokens=settings.llm.max_tokens,
        system=_system_prompt(settings),
        output_config={"effort": settings.llm.effort},
        messages=[{"role": "user", "content": user}],
        output_format=VideoBrief,
    )
    if response.stop_reason == "refusal":
        details = getattr(response, "stop_details", None)
        raise RuntimeError(f"Claude hat das Briefing abgelehnt: {details}")
    brief = response.parsed_output
    if brief is None:
        raise RuntimeError("Claude hat kein gültiges Briefing geliefert.")
    return _normalize(brief, settings)


def _normalize(brief: VideoBrief, settings: Settings) -> VideoBrief:
    v = settings.video
    if brief.format == "video":
        blocks = brief.blocks[: v.max_blocks]
        if v.mode == "talking_head":
            for b in blocks:
                b.kind = "talking"
        elif v.mode == "broll_only":
            for b in blocks:
                b.kind = "broll"
        for i, b in enumerate(blocks, start=1):
            b.index = i
            words = b.narration.split()
            if len(words) > v.max_words_per_block + 6:
                b.narration = " ".join(words[: v.max_words_per_block + 6])
        brief.blocks = blocks
    brief.hashtags = [h.lstrip("#").strip() for h in brief.hashtags if h.strip()][:6]
    return brief


def save_brief(brief: VideoBrief, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(brief.model_dump(), indent=2, ensure_ascii=False), encoding="utf-8")


def load_brief(path: Path) -> VideoBrief:
    return VideoBrief.model_validate(json.loads(path.read_text(encoding="utf-8")))
