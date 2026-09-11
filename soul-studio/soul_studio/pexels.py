"""Kostenlose Stock-Clips und Fotos von Pexels (API-Schlüssel ist gratis)."""
from __future__ import annotations

import os
from pathlib import Path

import httpx

PEXELS_API = "https://api.pexels.com"


class PexelsError(RuntimeError):
    pass


def _key() -> str:
    key = os.environ.get("PEXELS_API_KEY", "")
    if not key:
        raise PexelsError("PEXELS_API_KEY fehlt (kostenlos unter pexels.com/api).")
    return key


def _download(url: str, out: Path) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    with httpx.stream("GET", url, timeout=300, follow_redirects=True) as r:
        r.raise_for_status()
        with open(out, "wb") as f:
            for chunk in r.iter_bytes():
                f.write(chunk)
    return out


def search_video(query: str, out: Path, portrait: bool = True, min_seconds: float = 4.0,
                 exclude_ids: set[int] | None = None, page: int = 1) -> tuple[Path, int]:
    """Sucht einen passenden Clip und lädt die beste HD-Variante. Gibt (Pfad, Pexels-ID) zurück."""
    params = {"query": query, "per_page": 15, "page": page, "size": "medium"}
    if portrait:
        params["orientation"] = "portrait"
    with httpx.Client(timeout=60) as c:
        r = c.get(f"{PEXELS_API}/videos/search", headers={"Authorization": _key()}, params=params)
        r.raise_for_status()
        videos = r.json().get("videos", [])
    exclude_ids = exclude_ids or set()
    candidates = [v for v in videos if v.get("duration", 0) >= min_seconds and v["id"] not in exclude_ids]
    if not candidates and page == 1 and portrait:
        return search_video(query, out, portrait=False, min_seconds=min_seconds, exclude_ids=exclude_ids)
    if not candidates:
        raise PexelsError(f"Kein Clip für „{query}“ gefunden.")
    video = candidates[0]
    files = [f for f in video.get("video_files", []) if f.get("file_type") == "video/mp4"]
    files.sort(key=lambda f: abs((f.get("height") or 0) - 1920) + abs((f.get("width") or 0) - 1080))
    # bevorzugt ~1080x1920, aber nicht größer als nötig
    files.sort(key=lambda f: 0 if (f.get("height") or 0) >= 1080 else 1)
    if not files:
        raise PexelsError("Clip ohne MP4-Datei.")
    return _download(files[0]["link"], out), video["id"]


def search_photo(query: str, out: Path, portrait: bool = True) -> Path:
    params = {"query": query, "per_page": 10}
    if portrait:
        params["orientation"] = "portrait"
    with httpx.Client(timeout=60) as c:
        r = c.get(f"{PEXELS_API}/v1/search", headers={"Authorization": _key()}, params=params)
        r.raise_for_status()
        photos = r.json().get("photos", [])
    if not photos:
        raise PexelsError(f"Kein Foto für „{query}“ gefunden.")
    return _download(photos[0]["src"]["large2x"], out)
