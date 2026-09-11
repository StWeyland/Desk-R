"""Sprachausgabe: ElevenLabs (mit Wort-Zeitstempeln) oder Higgsfield text2speech_v2 als Ersatz."""
from __future__ import annotations

import base64
from dataclasses import dataclass
from pathlib import Path

import httpx

from .config import Settings
from .media import duration_seconds

ELEVEN_API = "https://api.elevenlabs.io/v1"


@dataclass
class Word:
    text: str
    start: float
    end: float


@dataclass
class VoiceTake:
    audio: Path
    seconds: float
    words: list[Word]          # leer, wenn keine Zeitstempel verfügbar


def _words_from_alignment(alignment: dict) -> list[Word]:
    chars = alignment.get("characters") or []
    starts = alignment.get("character_start_times_seconds") or []
    ends = alignment.get("character_end_times_seconds") or []
    words: list[Word] = []
    buf, w_start, w_end = "", None, None
    for ch, s, e in zip(chars, starts, ends):
        if ch.isspace():
            if buf:
                words.append(Word(buf, w_start, w_end))
            buf, w_start, w_end = "", None, None
            continue
        if not buf:
            w_start = s
        buf += ch
        w_end = e
    if buf:
        words.append(Word(buf, w_start, w_end))
    # Audio-Tags wie [warm] oder [pause] nicht als Untertitel anzeigen
    return [w for w in words if not (w.text.startswith("[") and w.text.endswith("]"))]


def elevenlabs_tts(text: str, out: Path, settings: Settings) -> VoiceTake:
    v = settings.voice
    key = settings.elevenlabs_api_key
    if not key:
        raise RuntimeError("ELEVENLABS_API_KEY fehlt.")
    if not v.elevenlabs_voice_id:
        raise RuntimeError("voice.elevenlabs_voice_id fehlt in der config.yaml (oder ELEVENLABS_VOICE_ID).")
    body = {
        "text": text,
        "model_id": v.elevenlabs_model,
        "voice_settings": {
            "stability": v.stability,
            "similarity_boost": v.similarity_boost,
            "style": v.style,
            "use_speaker_boost": True,
            "speed": v.speed,
        },
    }
    if v.language and not v.elevenlabs_model.startswith("eleven_multilingual"):
        body["language_code"] = v.language
    headers = {"xi-api-key": key, "Content-Type": "application/json"}
    url = f"{ELEVEN_API}/text-to-speech/{v.elevenlabs_voice_id}/with-timestamps"
    out.parent.mkdir(parents=True, exist_ok=True)
    with httpx.Client(timeout=180) as c:
        r = c.post(url, headers=headers, params={"output_format": "mp3_44100_128"}, json=body)
        if r.status_code >= 400:
            # Ersatz ohne Zeitstempel (z. B. wenn das Modell den Endpunkt nicht unterstützt)
            r2 = c.post(f"{ELEVEN_API}/text-to-speech/{v.elevenlabs_voice_id}", headers=headers,
                        params={"output_format": "mp3_44100_128"}, json=body)
            if r2.status_code >= 400:
                raise RuntimeError(f"ElevenLabs-Fehler {r.status_code}: {r.text[:500]}")
            out.write_bytes(r2.content)
            return VoiceTake(out, duration_seconds(out), [])
        data = r.json()
    out.write_bytes(base64.b64decode(data["audio_base64"]))
    alignment = data.get("normalized_alignment") or data.get("alignment") or {}
    words = _words_from_alignment(alignment)
    seconds = words[-1].end if words else duration_seconds(out)
    return VoiceTake(out, max(seconds, duration_seconds(out)), words)


def elevenlabs_voices(settings: Settings) -> list[dict]:
    key = settings.elevenlabs_api_key
    if not key:
        raise RuntimeError("ELEVENLABS_API_KEY fehlt.")
    with httpx.Client(timeout=60) as c:
        r = c.get(f"{ELEVEN_API}/voices", headers={"xi-api-key": key})
        r.raise_for_status()
        return [{"voice_id": v["voice_id"], "name": v["name"], "category": v.get("category", "")}
                for v in r.json().get("voices", [])]


def synthesize(text: str, out: Path, settings: Settings, higgsfield=None) -> VoiceTake:
    """Wählt den konfigurierten Anbieter."""
    if settings.voice.provider == "elevenlabs":
        return elevenlabs_tts(text, out, settings)
    if higgsfield is None:
        raise RuntimeError("Higgsfield-Client fehlt für die Sprachausgabe.")
    path = higgsfield.tts(text, out)
    return VoiceTake(path, duration_seconds(path), [])


def evenly_timed_words(text: str, seconds: float, offset: float = 0.0) -> list[Word]:
    """Ersatz-Zeitstempel: Wörter gleichmäßig über die Audiodauer verteilen."""
    tokens = text.split()
    if not tokens:
        return []
    weights = [max(len(t), 2) for t in tokens]
    total = sum(weights)
    words, t = [], offset
    for tok, w in zip(tokens, weights):
        d = seconds * w / total
        words.append(Word(tok, t, t + d))
        t += d
    return words
