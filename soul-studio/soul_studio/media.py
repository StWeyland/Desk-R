"""ffmpeg/ffprobe-Helfer. Nutzt ffmpeg aus dem PATH oder die statische Version aus imageio-ffmpeg."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path


def ffmpeg_bin() -> str:
    env = os.environ.get("FFMPEG_BIN")
    if env:
        return env
    found = shutil.which("ffmpeg")
    if found:
        return found
    try:
        import imageio_ffmpeg  # type: ignore

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("ffmpeg nicht gefunden. Installiere ffmpeg oder `pip install imageio-ffmpeg`.") from exc


def run_ffmpeg(args: list[str], quiet: bool = True) -> None:
    cmd = [ffmpeg_bin(), "-hide_banner", "-y"]
    if quiet:
        cmd += ["-loglevel", "error"]
    cmd += args
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg fehlgeschlagen:\n{' '.join(cmd)}\n{proc.stderr[-4000:]}")


def duration_seconds(path: Path) -> float:
    """Dauer einer Mediendatei. ffprobe, falls vorhanden, sonst ffmpeg-Ausgabe parsen."""
    probe = shutil.which("ffprobe")
    if probe:
        out = subprocess.run(
            [probe, "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)],
            capture_output=True, text=True,
        ).stdout
        try:
            return float(json.loads(out)["format"]["duration"])
        except Exception:
            pass
    proc = subprocess.run([ffmpeg_bin(), "-hide_banner", "-i", str(path)], capture_output=True, text=True)
    for line in proc.stderr.splitlines():
        line = line.strip()
        if line.startswith("Duration:"):
            hms = line.split()[1].rstrip(",")
            h, m, s = hms.split(":")
            return int(h) * 3600 + int(m) * 60 + float(s)
    raise RuntimeError(f"Dauer von {path} nicht lesbar.")


def hex_to_ass(hex_color: str, alpha: int = 0) -> str:
    """#RRGGBB → &HAABBGGRR (ASS-Farbformat)."""
    h = hex_color.lstrip("#")
    r, g, b = h[0:2], h[2:4], h[4:6]
    return f"&H{alpha:02X}{b}{g}{r}".upper()


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
