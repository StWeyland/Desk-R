"""Die eigentliche Produktionsstrecke: Beitrag → Briefing → Bilder/Videos/Stimme → fertiges Video."""
from __future__ import annotations

import json
import math
import shutil
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

from .assemble import BlockMedia, assemble, cleanup
from .brief import Block, VideoBrief, load_brief, make_brief, save_brief
from .config import Settings
from .higgsfield import Higgsfield
from .images import image_post, placeholder_frame
from .media import duration_seconds
from .sources import Post
from .voice import VoiceTake, Word, evenly_timed_words, synthesize


@dataclass
class Result:
    post_id: str
    format: str
    output_dir: Path
    media: Path | None
    caption: str
    brief_path: Path


TALKING_STYLE = (
    "She speaks directly to the camera in German with natural, clearly articulated lip movements "
    "synchronized to the provided audio, calm confident delivery, subtle natural hand gestures, "
    "gentle head movement, steady eye-level framing, realistic, no on-screen text."
)
BROLL_STYLE = "Slow, smooth camera movement, realistic, cinematic natural light, no on-screen text, no logos."
IMAGE_STYLE = "Photorealistic, natural skin, soft daylight, brand palette of cream, burgundy and warm salmon accents, no text, no logos."


def _scene_prompt(block: Block, settings: Settings) -> str:
    look, setting = settings.character.look, settings.character.setting
    if block.kind == "talking":
        return f"{block.scene_prompt}. Subject: {look}. Environment: {setting}. {IMAGE_STYLE}"
    return f"{block.scene_prompt}. {IMAGE_STYLE}"


def _video_prompt(block: Block) -> str:
    return f"{block.scene_prompt}. {TALKING_STYLE if block.kind == 'talking' else BROLL_STYLE}"


def _talking_seconds(audio_seconds: float) -> int:
    return int(min(15, max(4, math.ceil(audio_seconds + 0.6))))


def _post_caption(brief: VideoBrief) -> str:
    tags = " ".join(f"#{h}" for h in brief.hashtags)
    return f"{brief.caption.strip()}\n\n{tags}".strip()


def _write_meta(out_dir: Path, post: Post, brief: VideoBrief, media: Path | None) -> None:
    (out_dir / "caption.txt").write_text(_post_caption(brief), encoding="utf-8")
    meta = {
        "post_id": post.id, "title": post.title, "source": post.source, "path": post.path,
        "format": brief.format, "media": str(media) if media else None, "hook": brief.hook,
        "blocks": [b.model_dump() for b in brief.blocks],
    }
    (out_dir / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")


class Producer:
    def __init__(self, settings: Settings, dry_run: bool = False, mock: bool = False, log=print):
        self.settings = settings
        self.dry_run = dry_run
        self.mock = mock              # ohne Higgsfield/ElevenLabs: Platzhalter (für Tests)
        self.log = log
        self.hf = Higgsfield(settings)

    # ------------------------------------------------------------ Briefing
    def brief_for(self, post: Post, out_dir: Path, force_format: str | None = None, reuse: bool = True) -> VideoBrief:
        path = out_dir / "brief.json"
        if reuse and path.exists():
            self.log(f"  Briefing vorhanden: {path}")
            return load_brief(path)
        self.log("  Claude schreibt das Briefing …")
        brief = make_brief(post, self.settings, force_format)
        save_brief(brief, path)
        return brief

    # ------------------------------------------------------------ Bausteine
    def _voice(self, block: Block, out_dir: Path) -> VoiceTake:
        out = out_dir / f"voice_{block.index:02d}.mp3"
        words_file = out.with_suffix(".json")
        if out.exists():
            take = VoiceTake(out, duration_seconds(out), [])
            if words_file.exists():
                take.words = [Word(**w) for w in json.loads(words_file.read_text(encoding="utf-8"))]
            else:
                take.words = evenly_timed_words(block.narration, take.seconds)
            return take
        if self.mock:
            from .media import run_ffmpeg
            secs = max(2.0, len(block.narration.split()) / 2.3)
            run_ffmpeg(["-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", "-t", f"{secs:.2f}", str(out)])
            take = VoiceTake(out, secs, evenly_timed_words(block.narration, secs))
        else:
            take = synthesize(block.narration, out, self.settings, self.hf)
            if not take.words:
                take.words = evenly_timed_words(block.narration, take.seconds)
        words_file.write_text(json.dumps([w.__dict__ for w in take.words], ensure_ascii=False), encoding="utf-8")
        return take

    def _image(self, block: Block, out_dir: Path) -> Path:
        out = out_dir / f"frame_{block.index:02d}.png"
        if out.exists():
            return out
        if self.mock:
            return placeholder_frame(self.settings, out, f"Block {block.index}")
        return self.hf.soul_image(_scene_prompt(block, self.settings), self.settings.video.aspect_ratio, out)

    def _video(self, block: Block, frame: Path, take: VoiceTake, out_dir: Path) -> Path:
        out = out_dir / f"clip_{block.index:02d}.mp4"
        if out.exists():
            return out
        if self.mock:
            from .media import run_ffmpeg
            v = self.settings.video
            run_ffmpeg(["-loop", "1", "-framerate", str(v.fps), "-i", str(frame), "-t", f"{take.seconds + 0.5:.2f}",
                        "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out)])
            return out
        if block.kind == "talking":
            return self.hf.talking_video(_video_prompt(block), frame, take.audio, _talking_seconds(take.seconds), out)
        secs = max(self.settings.models.broll_seconds, math.ceil(take.seconds))
        return self.hf.broll_video(_video_prompt(block), frame, min(secs, 10), out)

    def _produce_block(self, block: Block, out_dir: Path) -> BlockMedia:
        self.log(f"  Block {block.index} ({block.kind}): Stimme …")
        take = self._voice(block, out_dir)
        self.log(f"  Block {block.index}: Bild mit Soul ID …")
        frame = self._image(block, out_dir)
        self.log(f"  Block {block.index}: Video …")
        clip = self._video(block, frame, take, out_dir)
        return BlockMedia(block.index, clip, take.audio, take.seconds, take.words, block.on_screen_text)

    # ------------------------------------------------------------ Produktion
    def produce(self, post: Post, force_format: str | None = None, parallel: int = 3) -> Result:
        s = self.settings
        out_dir = s.output_path / post.slug
        out_dir.mkdir(parents=True, exist_ok=True)
        self.log(f"▶ {post.title}  →  {out_dir}")
        brief = self.brief_for(post, out_dir, force_format)
        self.log(f"  Format: {brief.format} · Hook: {brief.hook}")

        if self.dry_run:
            self.log("  (Testlauf: keine Generierung)")
            _write_meta(out_dir, post, brief, None)
            return Result(post.id, brief.format, out_dir, None, _post_caption(brief), out_dir / "brief.json")

        if brief.format == "image":
            frame = out_dir / "frame.png"
            if not frame.exists():
                if self.mock:
                    placeholder_frame(s, frame, "Bild")
                else:
                    prompt = f"{brief.image_prompt}. Subject: {s.character.look}. {IMAGE_STYLE}"
                    self.hf.soul_image(prompt, "4:5", frame)
            final = image_post(s, frame, brief.image_headline or brief.hook, out_dir / "final.jpg")
            _write_meta(out_dir, post, brief, final)
            return Result(post.id, "image", out_dir, final, _post_caption(brief), out_dir / "brief.json")

        work = out_dir / "work"
        work.mkdir(exist_ok=True)
        with ThreadPoolExecutor(max_workers=max(1, parallel)) as pool:
            media = list(pool.map(lambda b: self._produce_block(b, work), brief.blocks))
        self.log("  Schnitt …")
        final = assemble(media, s, work / "render", out_dir / "final.mp4")
        _write_meta(out_dir, post, brief, final)
        if not self.mock:
            cleanup(work / "render")
        self.log(f"✔ Fertig: {final}")
        return Result(post.id, "video", out_dir, final, _post_caption(brief), out_dir / "brief.json")


def result_public_url(result: Result, settings: Settings) -> str | None:
    """Öffentliche URL des Ergebnisses, wenn der Output-Ordner über GitHub Pages ausgeliefert wird."""
    if not result.media:
        return None
    try:
        rel = result.media.resolve().relative_to(settings.path(".").resolve())
    except ValueError:
        return None
    base = settings.publish.public_base_url.rstrip("/")
    return f"{base}/{rel.as_posix()}"
