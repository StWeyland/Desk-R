"""Schnitt mit ffmpeg: Clips auf Sprachlänge bringen, zusammenfügen, Untertitel einbrennen, Abspann."""
from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from .captions import write_ass
from .config import Settings
from .images import end_card
from .media import duration_seconds, run_ffmpeg
from .voice import Word


@dataclass
class BlockMedia:
    index: int
    video: Path            # generierter Clip (Video, Ton wird verworfen)
    audio: Path            # Sprachaufnahme
    seconds: float         # Länge der Sprachaufnahme
    words: list[Word]
    on_screen_text: str = ""


def _scale_filter(settings: Settings) -> str:
    v = settings.video
    return (f"scale={v.width}:{v.height}:force_original_aspect_ratio=increase,"
            f"crop={v.width}:{v.height},setsar=1")


def render_block(block: BlockMedia, settings: Settings, out: Path, tail: float = 0.25) -> Path:
    """Ein Block: Bild auf Zielformat, Länge = Sprachdauer + kurze Pause, Ton = Sprachaufnahme."""
    length = block.seconds + tail
    v = settings.video
    vf = (f"[0:v]{_scale_filter(settings)},tpad=stop_mode=clone:stop_duration=30,"
          f"trim=duration={length:.3f},setpts=PTS-STARTPTS,fps={v.fps},format=yuv420p[v]")
    af = f"[1:a]apad=pad_dur={tail + 30:.2f},atrim=duration={length:.3f},asetpts=PTS-STARTPTS,aformat=sample_rates=48000:channel_layouts=stereo[a]"
    run_ffmpeg([
        "-i", str(block.video), "-i", str(block.audio),
        "-filter_complex", f"{vf};{af}", "-map", "[v]", "-map", "[a]",
        "-r", str(v.fps), "-fps_mode", "cfr",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-c:a", "aac", "-b:a", "192k",
        "-t", f"{length:.3f}", str(out),
    ])
    return out


def render_end_card(settings: Settings, workdir: Path) -> Path:
    v = settings.video
    png = end_card(settings, workdir / "end_card.png")
    out = workdir / "end_card.mp4"
    run_ffmpeg([
        "-loop", "1", "-framerate", str(v.fps), "-i", str(png),
        "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
        "-vf", f"{_scale_filter(settings)},fps={v.fps},format=yuv420p,fade=t=in:st=0:d=0.4",
        "-t", f"{v.end_card_seconds:.2f}", "-shortest", "-r", str(v.fps), "-fps_mode", "cfr",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-c:a", "aac", "-b:a", "192k", str(out),
    ])
    return out


def concat(parts: list[Path], out: Path) -> Path:
    listfile = out.with_suffix(".txt")
    listfile.write_text("".join(f"file '{p.resolve().as_posix()}'\n" for p in parts), encoding="utf-8")
    run_ffmpeg(["-f", "concat", "-safe", "0", "-i", str(listfile), "-c", "copy", str(out)])
    return out


def assemble(blocks: list[BlockMedia], settings: Settings, workdir: Path, final: Path) -> Path:
    workdir.mkdir(parents=True, exist_ok=True)
    rendered, timeline_words, overlays, t = [], [], [], 0.0
    tail = 0.25
    for b in sorted(blocks, key=lambda x: x.index):
        part = render_block(b, settings, workdir / f"block_{b.index:02d}.mp4", tail)
        actual = duration_seconds(part)
        for w in b.words:
            timeline_words.append(Word(w.text, t + w.start, t + w.end))
        if b.on_screen_text:
            overlays.append((t + 0.3, t + min(actual, 3.2), b.on_screen_text))
        t += actual
        rendered.append(part)
    if settings.video.end_card_seconds > 0:
        rendered.append(render_end_card(settings, workdir))
    joined = concat(rendered, workdir / "joined.mp4")

    filters = []
    if settings.video.captions != "none" and (timeline_words or overlays):
        ass = write_ass(timeline_words, settings, workdir / "captions.ass", overlays)
        fonts = settings.fonts_path.resolve().as_posix()
        filters.append(f"ass={ass.resolve().as_posix()}:fontsdir={fonts}")
    args = ["-i", str(joined)]
    if filters:
        args += ["-vf", ",".join(filters)]
    args += ["-af", "loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000",
             "-r", str(settings.video.fps), "-fps_mode", "cfr",
             "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
             "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(final)]
    final.parent.mkdir(parents=True, exist_ok=True)
    run_ffmpeg(args)
    return final


def cleanup(workdir: Path) -> None:
    shutil.rmtree(workdir, ignore_errors=True)
