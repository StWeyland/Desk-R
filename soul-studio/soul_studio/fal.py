"""fal.ai: sprechende Videos aus Foto + Stimme (OmniHuman) und optional KI-Szenen-Clips.

Bezahlung pro Sekunde, kein Abo. Modelle und Eingabefelder sind in der config.yaml
unter `footage` einstellbar, damit neue Modelle ohne Codeänderung nutzbar sind.
"""
from __future__ import annotations

import base64
import mimetypes
import os
import time
from pathlib import Path

import httpx

QUEUE = "https://queue.fal.run"


class FalError(RuntimeError):
    pass


def _headers() -> dict:
    key = os.environ.get("FAL_KEY", "")
    if not key:
        raise FalError("FAL_KEY fehlt (fal.ai → Keys).")
    return {"Authorization": f"Key {key}", "Content-Type": "application/json"}


def run(model: str, payload: dict, timeout_s: int = 900) -> dict:
    """Job einreichen, warten, Ergebnis holen (fal Queue-API)."""
    with httpx.Client(timeout=120) as c:
        r = c.post(f"{QUEUE}/{model}", headers=_headers(), json=payload)
        if r.status_code >= 400:
            raise FalError(f"fal {model}: {r.status_code} {r.text[:600]}")
        job = r.json()
        status_url = job.get("status_url") or f"{QUEUE}/{model}/requests/{job['request_id']}/status"
        response_url = job.get("response_url") or f"{QUEUE}/{model}/requests/{job['request_id']}"
        start = time.time()
        while True:
            s = c.get(status_url, headers=_headers(), params={"logs": "0"})
            s.raise_for_status()
            state = s.json().get("status")
            if state == "COMPLETED":
                break
            if state in {"FAILED", "CANCELLED"}:
                raise FalError(f"fal {model} endete mit {state}: {s.text[:600]}")
            if time.time() - start > timeout_s:
                raise FalError(f"fal {model}: Zeitüberschreitung")
            time.sleep(4)
        res = c.get(response_url, headers=_headers())
        res.raise_for_status()
        return res.json()


def _first_url(obj) -> str | None:
    if isinstance(obj, dict):
        if isinstance(obj.get("url"), str):
            return obj["url"]
        for v in obj.values():
            u = _first_url(v)
            if u:
                return u
    if isinstance(obj, list):
        for item in obj:
            u = _first_url(item)
            if u:
                return u
    return None


def text_to_video(prompt: str, out: Path, model: str, seconds: int, aspect_ratio: str,
                  extra: dict | None = None) -> Path:
    payload = {"prompt": prompt, "duration": str(seconds), "aspect_ratio": aspect_ratio,
               "negative_prompt": "text, watermark, logo, blur, distortion, low quality, people looking at camera"}
    payload.update(extra or {})
    result = run(model, payload)
    url = _first_url(result.get("video") or result)
    if not url:
        raise FalError(f"Keine Video-URL im Ergebnis: {str(result)[:400]}")
    out.parent.mkdir(parents=True, exist_ok=True)
    with httpx.stream("GET", url, timeout=300, follow_redirects=True) as r:
        r.raise_for_status()
        with open(out, "wb") as f:
            for chunk in r.iter_bytes():
                f.write(chunk)
    return out


def data_uri(path: Path) -> str:
    """Datei als data:-URI, damit kein Hosting nötig ist (fal akzeptiert das für image_url/audio_url)."""
    mime = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode()}"


def _save(url: str, out: Path) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    with httpx.stream("GET", url, timeout=300, follow_redirects=True) as r:
        r.raise_for_status()
        with open(out, "wb") as f:
            for chunk in r.iter_bytes():
                f.write(chunk)
    return out


def talking_video(photo: Path, audio: Path, out: Path, model: str, extra: dict | None = None) -> Path:
    """Foto von Steffi + Tonspur → Video, in dem sie den Text spricht (Lippen, Mimik, Gestik)."""
    payload = {"image_url": data_uri(photo), "audio_url": data_uri(audio)}
    payload.update(extra or {})
    result = run(model, payload, timeout_s=1500)
    url = _first_url(result.get("video") or result)
    if not url:
        raise FalError(f"Keine Video-URL im Ergebnis: {str(result)[:400]}")
    return _save(url, out)


def generate_image(prompt: str, out: Path, model: str, aspect_ratio: str = "4:5",
                   image_urls: list[str] | None = None, extra: dict | None = None) -> Path:
    """Bildgenerierung (Illustration ohne Gesicht) oder Bildbearbeitung mit Referenzfotos
    (für Szenen mit Steffis Gesicht). `image_urls` gesetzt → Edit-Modus (z.B. nano-banana-pro/edit)."""
    payload: dict = {"prompt": prompt, "num_images": 1, "output_format": "png"}
    if aspect_ratio:
        payload["aspect_ratio"] = aspect_ratio
    if image_urls:
        payload["image_urls"] = image_urls
    payload.update(extra or {})
    result = run(model, payload, timeout_s=180)
    images = result.get("images") or []
    url = images[0]["url"] if images and isinstance(images[0], dict) else _first_url(result)
    if not url:
        raise FalError(f"Keine Bild-URL im Ergebnis: {str(result)[:400]}")
    return _save(url, out)
