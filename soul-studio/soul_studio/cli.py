"""Kommandozeile: python -m soul_studio <befehl>"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

from .brief import Brief, json_schema, load_brief, save_brief
from .config import Settings, load_settings
from .pipeline import Producer
from .sources import State, post_from_file, post_from_job, post_from_text


def _settings(args) -> Settings:
    return load_settings(Path(args.config) if args.config else None)


def cmd_check(args) -> int:
    s = _settings(args)
    from .media import ffmpeg_bin

    print("Soul Studio – Systemcheck\n")
    ok = True
    has_el = bool(s.elevenlabs_api_key and s.voice.elevenlabs_voice_id)
    print(("✔" if has_el else "✘") + " ElevenLabs (ELEVENLABS_API_KEY + ELEVENLABS_VOICE_ID) – für Videos mit Stimme")
    has_px = bool(os.environ.get("PEXELS_API_KEY"))
    print(("✔" if has_px else "✘") + " Pexels (PEXELS_API_KEY) – kostenlose Szenen-Clips und Fotos")
    if s.footage.provider == "fal":
        print(("✔" if os.environ.get("FAL_KEY") else "✘") + " fal.ai (FAL_KEY) – KI-Clips, bezahlt")
    has_claude = bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN"))
    print(("✔" if has_claude else "·") + " ANTHROPIC_API_KEY – nur nötig, wenn das Briefing per API statt in der Routine entsteht")
    try:
        print(f"✔ ffmpeg: {ffmpeg_bin()}")
    except Exception as exc:
        ok = False
        print(f"✘ {exc}")
    fonts = [p.name for p in s.fonts_path.glob("*.ttf")]
    print(("✔" if fonts else "✘") + f" Schriften: {', '.join(fonts) or 'fehlen'}")
    print("\nCarousel, Bild und Story funktionieren ohne Schlüssel. Video braucht ElevenLabs und Pexels.")
    print("Bereit." if ok and has_el and has_px else "Für Videos fehlen noch Schlüssel (siehe oben).")
    return 0 if ok else 1


def cmd_voices(args) -> int:
    from .voice import elevenlabs_voices
    for v in elevenlabs_voices(_settings(args)):
        print(f"{v['voice_id']}  {v['name']}  ({v['category']})")
    return 0


def cmd_schema(args) -> int:
    print(json.dumps(json_schema(), indent=2, ensure_ascii=False))
    return 0


def _load_post(args):
    if args.text:
        return post_from_text(args.text, args.title)
    p = Path(args.post)
    if p.suffix == ".json":
        return post_from_job(p)
    return post_from_file(p)


def cmd_brief(args) -> int:
    s = _settings(args)
    post = _load_post(args)
    out_dir = s.output_path / post.slug
    brief = Producer(s, dry_run=True).brief_for(post, out_dir, args.format, reuse=not args.fresh)
    print(json.dumps(brief.model_dump(), indent=2, ensure_ascii=False))
    print(f"\nGespeichert: {out_dir / 'brief.json'}")
    return 0


def cmd_render(args) -> int:
    """Fertiges Briefing (JSON) rendern – so arbeitet die Routine."""
    s = _settings(args)
    brief_path = Path(args.brief)
    brief = load_brief(brief_path, s)
    post = post_from_job(Path(args.job)) if args.job else post_from_text(brief.caption or brief.title, brief.title)
    out_dir = Path(args.out) if args.out else s.output_path / post.slug
    out_dir.mkdir(parents=True, exist_ok=True)
    save_brief(brief, out_dir / "brief.json")
    result = Producer(s, mock=args.mock).render(post, brief, out_dir, args.parallel)
    print(json.dumps(result.as_dict(), indent=2, ensure_ascii=False))
    return 0


def cmd_produce(args) -> int:
    s = _settings(args)
    post = _load_post(args)
    result = Producer(s, dry_run=args.dry_run, mock=args.mock).produce(post, args.format, parallel=args.parallel)
    print(json.dumps(result.as_dict(), indent=2, ensure_ascii=False))
    if not args.no_state and not args.dry_run:
        State(s.state_path).mark(post, {"format": result.format, "media": [str(m) for m in result.media]})
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="soul-studio", description="Videos, Carousels und Bilder aus Beiträgen im Desk-Revolution-Look.")
    p.add_argument("--config", help="Pfad zur config.yaml")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check", help="Systemcheck: Schlüssel, ffmpeg, Schriften").set_defaults(fn=cmd_check)
    sub.add_parser("voices", help="ElevenLabs-Stimmen auflisten").set_defaults(fn=cmd_voices)
    sub.add_parser("schema", help="JSON-Schema des Briefings ausgeben").set_defaults(fn=cmd_schema)

    c = sub.add_parser("render", help="Ein fertiges Briefing (JSON) produzieren")
    c.add_argument("brief", help="brief.json")
    c.add_argument("--job", help="job.json mit title/text/format/page_id (optional)")
    c.add_argument("--out", help="Ausgabeordner")
    c.add_argument("--mock", action="store_true")
    c.add_argument("--parallel", type=int, default=3)
    c.set_defaults(fn=cmd_render)

    for name, fn, helptext in (("brief", cmd_brief, "Briefing per Claude-API erzeugen"),
                               ("produce", cmd_produce, "Beitrag per Claude-API briefen und produzieren")):
        c = sub.add_parser(name, help=helptext)
        c.add_argument("post", nargs="?", help="Datei (.md/.txt/.html) oder job.json")
        c.add_argument("--text", help="Beitragstext direkt übergeben")
        c.add_argument("--title")
        c.add_argument("--format", choices=["video", "image", "carousel", "story", "none"])
        if name == "brief":
            c.add_argument("--fresh", action="store_true")
        else:
            c.add_argument("--dry-run", action="store_true")
            c.add_argument("--mock", action="store_true")
            c.add_argument("--parallel", type=int, default=3)
            c.add_argument("--no-state", action="store_true")
        c.set_defaults(fn=fn)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
