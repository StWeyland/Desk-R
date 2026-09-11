"""Anbindung an Higgsfield über die offizielle CLI (`higgsfield`).

Die CLI übernimmt Login (OAuth), Uploads, Soul-ID-Training und alle Modelle.
Wir rufen sie mit `--json` auf und lesen die Ergebnisse strukturiert ein.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import httpx

from .config import Settings


class HiggsfieldError(RuntimeError):
    pass


@dataclass
class Job:
    id: str
    status: str
    result_url: str | None
    raw: Any

    @property
    def ok(self) -> bool:
        return self.status.lower() in {"completed", "succeeded", "success", "done"} and bool(self.result_url)


def _first_url(obj: Any) -> str | None:
    """Sucht rekursiv die erste Ergebnis-URL in einem CLI-JSON-Objekt."""
    if isinstance(obj, str):
        return obj if obj.startswith("http") else None
    if isinstance(obj, dict):
        for key in ("result_url", "url", "video_url", "image_url", "audio_url", "download_url"):
            v = obj.get(key)
            if isinstance(v, str) and v.startswith("http"):
                return v
        for key in ("results", "result", "outputs", "output", "media", "job", "jobs", "data"):
            if key in obj:
                u = _first_url(obj[key])
                if u:
                    return u
        for v in obj.values():
            if isinstance(v, (dict, list)):
                u = _first_url(v)
                if u:
                    return u
    if isinstance(obj, list):
        for item in obj:
            u = _first_url(item)
            if u:
                return u
    return None


def _first_dict_with(obj: Any, keys: Iterable[str]) -> dict | None:
    keys = tuple(keys)
    if isinstance(obj, dict):
        if any(k in obj for k in keys):
            return obj
        for v in obj.values():
            d = _first_dict_with(v, keys)
            if d:
                return d
    if isinstance(obj, list):
        for item in obj:
            d = _first_dict_with(item, keys)
            if d:
                return d
    return None


def parse_job(raw: Any) -> Job:
    d = _first_dict_with(raw, ("status", "result_url")) or (raw if isinstance(raw, dict) else {})
    job_id = str(d.get("id") or d.get("job_id") or d.get("request_id") or "")
    status = str(d.get("status") or ("completed" if _first_url(raw) else "unknown"))
    return Job(id=job_id, status=status, result_url=_first_url(raw), raw=raw)


class Higgsfield:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.bin = settings.higgsfield_bin
        self.wait_timeout = settings.video.wait_timeout

    # ------------------------------------------------------------ Basis
    def available(self) -> bool:
        return shutil.which(self.bin) is not None or Path(self.bin).exists()

    def run(self, *args: str, json_out: bool = True, timeout: int = 60 * 40) -> Any:
        cmd = [self.bin, *args]
        if json_out:
            cmd.append("--json")
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        out = proc.stdout.strip()
        if proc.returncode != 0:
            msg = (proc.stderr or out).strip()
            if "Session expired" in msg or "Not authenticated" in msg:
                msg += "\nBitte einmal `higgsfield auth login` ausführen."
            raise HiggsfieldError(f"`{' '.join(cmd)}` fehlgeschlagen:\n{msg}")
        if not json_out:
            return out
        try:
            return json.loads(out) if out else {}
        except json.JSONDecodeError:
            # Manche Befehle drucken vor dem JSON noch eine Zeile Text
            start = min([i for i in (out.find("{"), out.find("[")) if i >= 0] or [-1])
            if start >= 0:
                return json.loads(out[start:])
            raise HiggsfieldError(f"Keine JSON-Antwort von `{' '.join(cmd)}`:\n{out}")

    def account_status(self) -> dict:
        return self.run("account", "status")

    # ------------------------------------------------------------ Uploads
    def upload(self, path: Path) -> str:
        data = self.run("upload", "create", str(path))
        d = _first_dict_with(data, ("id", "upload_id")) or {}
        upload_id = d.get("id") or d.get("upload_id")
        if not upload_id:
            raise HiggsfieldError(f"Upload ohne ID: {data}")
        return str(upload_id)

    # ------------------------------------------------------------ Soul ID
    def soul_create(self, name: str, photos: list[Path], variant: str = "soul-2") -> str:
        args = ["soul-id", "create", "--name", name, f"--{variant}"]
        for p in photos:
            args += ["--image", str(p)]
        data = self.run(*args)
        d = _first_dict_with(data, ("id", "reference_id")) or {}
        soul_id = d.get("id") or d.get("reference_id")
        if not soul_id:
            raise HiggsfieldError(f"Soul-Training ohne ID gestartet: {data}")
        return str(soul_id)

    def soul_wait(self, soul_id: str) -> dict:
        return self.run("soul-id", "wait", soul_id, timeout=60 * 60)

    def soul_list(self) -> Any:
        return self.run("soul-id", "list")

    def voices(self) -> Any:
        return self.run("voices", "list", "--size", "100")

    # ------------------------------------------------------------ Generieren
    def generate(self, model: str, params: dict[str, Any], media: dict[str, list[str] | str] | None = None,
                 wait: bool = True) -> Job:
        """Startet einen Job. `params` → `--key value`, `media` → `--start-image pfad` usw."""
        args = ["generate", "create", model]
        for key, value in params.items():
            if value is None or value == "":
                continue
            flag = f"--{key}"
            if isinstance(value, bool):
                args += [flag, "true" if value else "false"]
            else:
                args += [flag, str(value)]
        for key, value in (media or {}).items():
            values = value if isinstance(value, list) else [value]
            for v in values:
                if v:
                    args += [f"--{key}", str(v)]
        if wait:
            args += ["--wait", "--wait-timeout", self.wait_timeout, "--wait-interval", "4s"]
        data = self.run(*args)
        job = parse_job(data)
        if wait and not job.ok:
            raise HiggsfieldError(f"Job {model} endete mit Status {job.status}: {json.dumps(data)[:800]}")
        return job

    def get_job(self, job_id: str) -> Job:
        return parse_job(self.run("generate", "get", job_id))

    # ------------------------------------------------------------ Bausteine
    def soul_image(self, prompt: str, aspect_ratio: str, out: Path, quality: str | None = None) -> Path:
        s = self.settings
        params = {"prompt": prompt, "aspect_ratio": aspect_ratio, "quality": quality or s.models.image_quality}
        if s.character.soul_id:
            params["soul-id"] = s.character.soul_id
        job = self.generate(s.models.image, params)
        return download(job.result_url, out)

    def talking_video(self, prompt: str, start_image: Path, audio: Path, seconds: int, out: Path) -> Path:
        """Sprechendes Video: Startbild (Soul) + Audio (ElevenLabs) → Lippen synchron zum Ton."""
        s = self.settings
        params = {
            "prompt": prompt,
            "aspect_ratio": s.video.aspect_ratio,
            "duration": seconds,
            "resolution": s.models.talking_video_resolution,
            "mode": s.models.talking_video_mode,
        }
        media = {"start-image": str(start_image), "audio": str(audio)}
        job = self.generate(s.models.talking_video, params, media)
        return download(job.result_url, out)

    def broll_video(self, prompt: str, start_image: Path, seconds: int, out: Path) -> Path:
        s = self.settings
        model = s.models.broll_video
        params: dict[str, Any] = {"prompt": prompt, "aspect_ratio": s.video.aspect_ratio, "duration": seconds}
        if model.startswith("kling3_0") and not model.endswith("turbo"):
            params["mode"] = s.models.broll_video_mode
            params["sound"] = "off"
        elif model.startswith("seedance"):
            params["resolution"] = s.models.talking_video_resolution
            params["generate_audio"] = False
        elif model.startswith("veo3_1"):
            params["duration"] = min((d for d in (4, 6, 8) if d >= seconds), default=8)
        job = self.generate(model, params, {"start-image": str(start_image)})
        return download(job.result_url, out)

    def tts(self, text: str, out: Path) -> Path:
        s = self.settings.voice
        params = {"prompt": text, "variant": s.higgsfield_variant, "voice_type": s.higgsfield_voice_type,
                  "voice_id": s.higgsfield_voice_id}
        job = self.generate("text2speech_v2", params)
        return download(job.result_url, out)


def download(url: str | None, out: Path) -> Path:
    if not url:
        raise HiggsfieldError("Kein Ergebnis-Link vorhanden.")
    out.parent.mkdir(parents=True, exist_ok=True)
    with httpx.stream("GET", url, timeout=300, follow_redirects=True) as r:
        r.raise_for_status()
        with open(out, "wb") as f:
            for chunk in r.iter_bytes():
                f.write(chunk)
    return out
