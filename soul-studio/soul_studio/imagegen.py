"""Plakat-Erzeugung nach Steffis Creative-Director-Workflow.

Zwei Ausführungswege für dieselbe Aufgabe:
1. API vorhanden (OPENAI_API_KEY oder FAL_KEY) und erreichbar → automatisches Rendern.
2. Kein Zugang / nicht erreichbar → der fertige Prompt wird als Text zurückgegeben,
   den Steffi genauso in ChatGPT einfügt wie bisher ("Erstelle ein Bild zur Projektanweisung").
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import httpx

from .config import Settings

MASTER_PROMPT_FILE = "poster_master_prompt.md"


class NeedsManualGeneration(Exception):
    """Kein API-Zugang (oder nicht erreichbar) – der Prompt muss von Hand erzeugt werden."""

    def __init__(self, prompt: str, reason: str):
        super().__init__(reason)
        self.prompt = prompt
        self.reason = reason


@dataclass
class PosterResult:
    path: Path
    prompt: str


def master_prompt(settings: Settings) -> str:
    return (settings.prompts_path / MASTER_PROMPT_FILE).read_text(encoding="utf-8")


def build_poster_prompt(settings: Settings, briefing: str) -> str:
    """Kombiniert Steffis Master-Prompt mit dem für den Beitrag ausgefüllten Briefing –
    genau der Text, den sie sonst von Hand in ChatGPT einfügt."""
    return f"{master_prompt(settings)}\n\n---\n\n# PROJEKTBRIEFING\n\n{briefing.strip()}\n\n---\n\nAusgabeformat: Plakat 9:16"


def _openai_size(aspect_ratio: str) -> str:
    # gpt-image unterstützt feste Größen; 1024x1536 liegt am nächsten an 9:16/4:5.
    return "1024x1536" if aspect_ratio != "1:1" else "1024x1024"


def _generate_openai(prompt: str, out: Path, aspect_ratio: str) -> Path:
    key = os.environ.get("OPENAI_API_KEY", "")
    if not key:
        raise NeedsManualGeneration(prompt, "OPENAI_API_KEY fehlt")
    body = {"model": "gpt-image-1", "prompt": prompt, "size": _openai_size(aspect_ratio), "quality": "high", "n": 1}
    try:
        with httpx.Client(timeout=180) as c:
            r = c.post("https://api.openai.com/v1/images/generations",
                      headers={"Authorization": f"Bearer {key}"}, json=body)
    except httpx.HTTPError as exc:
        raise NeedsManualGeneration(prompt, f"OpenAI nicht erreichbar: {exc}") from exc
    if r.status_code >= 400:
        raise NeedsManualGeneration(prompt, f"OpenAI-Fehler {r.status_code}: {r.text[:300]}")
    data = r.json()["data"][0]
    out.parent.mkdir(parents=True, exist_ok=True)
    if "b64_json" in data:
        import base64
        out.write_bytes(base64.b64decode(data["b64_json"]))
    else:
        with httpx.stream("GET", data["url"], timeout=120, follow_redirects=True) as resp:
            resp.raise_for_status()
            out.write_bytes(b"".join(resp.iter_bytes()))
    return out


def _generate_fal(prompt: str, out: Path, settings: Settings, aspect_ratio: str) -> Path:
    if not os.environ.get("FAL_KEY"):
        raise NeedsManualGeneration(prompt, "FAL_KEY fehlt")
    try:
        from .fal import generate_image
        return generate_image(prompt, out, settings.footage.image_model, aspect_ratio=aspect_ratio,
                              extra={"resolution": settings.footage.image_resolution})
    except NeedsManualGeneration:
        raise
    except Exception as exc:
        raise NeedsManualGeneration(prompt, f"fal.ai fehlgeschlagen: {exc}") from exc


def generate_poster(settings: Settings, briefing: str, out: Path, aspect_ratio: str = "9:16") -> PosterResult:
    """Versucht das Plakat automatisch zu erzeugen. Wenn kein Weg funktioniert,
    wird NeedsManualGeneration ausgelöst — der Aufrufer legt dann den Prompt als Text ab."""
    prompt = build_poster_prompt(settings, briefing)
    provider = settings.footage.image_provider
    errors = []
    order = [provider] + [p for p in ("openai", "fal") if p != provider]
    for name in order:
        try:
            if name == "openai":
                return PosterResult(_generate_openai(prompt, out, aspect_ratio), prompt)
            if name == "fal":
                return PosterResult(_generate_fal(prompt, out, settings, aspect_ratio), prompt)
        except NeedsManualGeneration as exc:
            errors.append(f"{name}: {exc.reason}")
    raise NeedsManualGeneration(prompt, "; ".join(errors))
