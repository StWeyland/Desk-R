"""Produktionsstrecke: Briefing → Stimme + Szenen-Clips → Video, oder Carousel / Bild / Story."""
from __future__ import annotations

import json
import math
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

from .assemble import BlockMedia, assemble, cleanup
from .brief import Block, Brief, format_from_notion, load_brief, make_brief_via_api, save_brief
from .carousel import render_carousel
from .config import Settings
from .images import placeholder_frame, statement_image
import httpx
from .media import duration_seconds, run_ffmpeg
from .sources import Post
from .voice import VoiceTake, Word, evenly_timed_words, synthesize


@dataclass
class Result:
    post_id: str
    format: str
    output_dir: Path
    media: list[Path]
    caption: str
    brief_path: Path

    def as_dict(self) -> dict:
        return {"post_id": self.post_id, "format": self.format, "output_dir": str(self.output_dir),
                "media": [str(m) for m in self.media], "caption": self.caption, "brief": str(self.brief_path)}


def _write_meta(out_dir: Path, post: Post, brief: Brief, media: list[Path]) -> None:
    (out_dir / "caption.txt").write_text(brief.caption_with_tags(), encoding="utf-8")
    meta = {"post_id": post.id, "title": post.title, "source": post.source, "notion_page_id": post.notion_page_id,
            "format": brief.format, "media": [str(m) for m in media], "hook": brief.hook,
            "platforms": brief.platforms, "caption": brief.caption_with_tags()}
    (out_dir / "result.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")


class Producer:
    def __init__(self, settings: Settings, dry_run: bool = False, mock: bool = False, log=print):
        self.settings = settings
        self.dry_run = dry_run
        self.mock = mock              # ohne Internetdienste: Platzhalter (für Tests)
        self.log = log
        self._used_clips: set[int] = set()
        self._photos: list[Path] = []

    def _character_photos(self, out_dir: Path) -> list[Path]:
        """Fotos aus config/ENV laden; URLs werden einmal heruntergeladen."""
        if self._photos:
            return self._photos
        for i, src in enumerate(self.settings.character.photos):
            if src.startswith("http"):
                dest = out_dir / f"character_{i + 1}.jpg"
                if not dest.exists():
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    with httpx.stream("GET", src, timeout=120, follow_redirects=True) as r:
                        r.raise_for_status()
                        dest.write_bytes(b"".join(r.iter_bytes()))
                self._photos.append(dest)
            else:
                path = self.settings.path(src)
                if path.exists():
                    self._photos.append(path)
        if not self._photos:
            raise RuntimeError("Kein Charakterfoto: character.photos in config.yaml oder CHARACTER_PHOTO_URL setzen.")
        return self._photos

    # ------------------------------------------------------------ Briefing
    def brief_for(self, post: Post, out_dir: Path, force_format: str | None = None, reuse: bool = True) -> Brief:
        path = out_dir / "brief.json"
        if reuse and path.exists():
            self.log(f"  Briefing vorhanden: {path}")
            return load_brief(path, self.settings)
        fmt = force_format or format_from_notion(post.notion_format)
        self.log("  Claude schreibt das Briefing über die API …")
        brief = make_brief_via_api(post.title, post.text, self.settings, fmt)
        save_brief(brief, path)
        return brief

    # ------------------------------------------------------------ Video-Bausteine
    def _voice(self, block: Block, out_dir: Path) -> VoiceTake:
        out = out_dir / f"voice_{block.index:02d}.mp3"
        words_file = out.with_suffix(".json")
        if out.exists():
            take = VoiceTake(out, duration_seconds(out), [])
            take.words = ([Word(**w) for w in json.loads(words_file.read_text(encoding="utf-8"))]
                          if words_file.exists() else evenly_timed_words(block.narration, take.seconds))
            return take
        if self.mock:
            secs = max(2.0, len(block.narration.split()) / 2.3)
            run_ffmpeg(["-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", "-t", f"{secs:.2f}", str(out)])
            take = VoiceTake(out, secs, evenly_timed_words(block.narration, secs))
        else:
            take = synthesize(block.narration, out, self.settings)
            if not take.words:
                take.words = evenly_timed_words(block.narration, take.seconds)
        words_file.write_text(json.dumps([w.__dict__ for w in take.words], ensure_ascii=False), encoding="utf-8")
        return take

    def _clip(self, block: Block, take: VoiceTake, out_dir: Path) -> Path:
        out = out_dir / f"clip_{block.index:02d}.mp4"
        if out.exists():
            return out
        v, f = self.settings.video, self.settings.footage
        if self.mock:
            frame = placeholder_frame(self.settings, out_dir / f"frame_{block.index:02d}.png", f"Block {block.index}")
            run_ffmpeg(["-loop", "1", "-framerate", str(v.fps), "-i", str(frame), "-t", f"{take.seconds + 0.5:.2f}",
                        "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out)])
            return out
        if block.kind == "talking":
            from .fal import talking_video
            photos = self._character_photos(out_dir.parent)
            photo = photos[(block.index - 1) % len(photos)]
            return talking_video(photo, take.audio, out, f.talking_model, f.talking_extra)
        if f.provider == "fal":
            from .fal import text_to_video
            prompt = f"{block.scene_prompt or block.footage_query}. {f.style_suffix}"
            secs = f.fal_seconds if take.seconds <= f.fal_seconds else 10
            return text_to_video(prompt, out, f.fal_model, secs, v.aspect_ratio, f.fal_extra)
        from .pexels import search_video
        path, clip_id = search_video(block.footage_query, out, portrait=v.height > v.width,
                                     min_seconds=take.seconds, exclude_ids=self._used_clips)
        self._used_clips.add(clip_id)
        return path

    def _produce_block(self, block: Block, out_dir: Path) -> BlockMedia:
        self.log(f"  Block {block.index}: Stimme …")
        take = self._voice(block, out_dir)
        self.log(f"  Block {block.index}: Szene ({self.settings.footage.provider}) …")
        clip = self._clip(block, take, out_dir)
        return BlockMedia(block.index, clip, take.audio, take.seconds, take.words, block.on_screen_text)

    # ------------------------------------------------------------ Formate
    def render(self, post: Post, brief: Brief, out_dir: Path, parallel: int = 3) -> Result:
        s = self.settings
        out_dir.mkdir(parents=True, exist_ok=True)
        media: list[Path] = []
        if brief.format == "video":
            work = out_dir / "work"
            work.mkdir(exist_ok=True)
            # Clips nacheinander suchen, damit keine doppelten Stock-Clips entstehen; Stimmen parallel
            with ThreadPoolExecutor(max_workers=max(1, parallel)) as pool:
                takes = list(pool.map(lambda b: self._voice(b, work), brief.blocks))
            blocks = []
            for b, take in zip(brief.blocks, takes):
                self.log(f"  Block {b.index}: {'Steffi spricht (fal)' if b.kind == 'talking' else 'Szene (' + s.footage.provider + ')'} …")
                clip = self._clip(b, take, work)
                blocks.append(BlockMedia(b.index, clip, take.audio, take.seconds, take.words, b.on_screen_text))
            self.log("  Schnitt …")
            media = [assemble(blocks, s, work / "render", out_dir / "final.mp4")]
            if not self.mock:
                cleanup(work / "render")
        elif brief.format == "carousel":
            pngs, pdf = render_carousel(brief.slides, s, out_dir)
            media = [pdf, *pngs]
        elif brief.format in {"image", "story"}:
            size = (1080, 1920) if brief.format == "story" else (1080, 1350)
            photo = None
            if brief.image_query and not self.mock:
                try:
                    from .pexels import search_photo
                    photo = search_photo(brief.image_query, out_dir / "photo.jpg", portrait=True)
                except Exception as exc:
                    self.log(f"  Kein Foto ({exc}); nutze Farbfläche.")
            media = [statement_image(s, brief.image_headline or brief.hook, brief.image_subline,
                                     out_dir / ("final_story.jpg" if brief.format == "story" else "final.jpg"),
                                     size, photo)]
        else:
            self.log("  Format „none“: nur Beitragstext, kein Asset.")
        _write_meta(out_dir, post, brief, media)
        self.log(f"✔ Fertig: {out_dir}")
        return Result(post.id, brief.format, out_dir, media, brief.caption_with_tags(), out_dir / "brief.json")

    def produce(self, post: Post, force_format: str | None = None, parallel: int = 3) -> Result:
        out_dir = self.settings.output_path / post.slug
        out_dir.mkdir(parents=True, exist_ok=True)
        self.log(f"▶ {post.title}  →  {out_dir}")
        brief = self.brief_for(post, out_dir, force_format)
        self.log(f"  Format: {brief.format} · Hook: {brief.hook}")
        if self.dry_run:
            self.log("  (Testlauf: keine Generierung)")
            _write_meta(out_dir, post, brief, [])
            return Result(post.id, brief.format, out_dir, [], brief.caption_with_tags(), out_dir / "brief.json")
        return self.render(post, brief, out_dir, parallel)
