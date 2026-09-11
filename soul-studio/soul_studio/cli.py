"""Kommandozeile: python -m soul_studio <befehl>"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
from pathlib import Path

from .config import Settings, load_settings
from .pipeline import Producer, result_public_url
from .sources import State, new_posts, notion_mark_done, post_from_file, post_from_text


def _settings(args) -> Settings:
    return load_settings(Path(args.config) if args.config else None)


def cmd_check(args) -> int:
    s = _settings(args)
    from .higgsfield import Higgsfield
    from .media import ffmpeg_bin

    ok = True
    print("Soul Studio – Systemcheck\n")
    hf = Higgsfield(s)
    if hf.available():
        try:
            acc = hf.account_status()
            print(f"✔ Higgsfield CLI angemeldet: {json.dumps(acc, ensure_ascii=False)[:160]}")
        except Exception as exc:
            ok = False
            print(f"✘ Higgsfield CLI vorhanden, aber nicht nutzbar: {str(exc).splitlines()[-1]}")
    else:
        ok = False
        print("✘ Higgsfield CLI nicht gefunden (npm i -g @higgsfield/cli oder Installer, dann `higgsfield auth login`).")
    print(("✔" if s.character.soul_id else "✘") + f" Soul ID: {s.character.soul_id or 'fehlt – `soul create` ausführen'}")
    if not s.character.soul_id:
        ok = False
    if s.voice.provider == "elevenlabs":
        print(("✔" if s.elevenlabs_api_key else "✘") + " ELEVENLABS_API_KEY")
        print(("✔" if s.voice.elevenlabs_voice_id else "✘") + f" ElevenLabs voice_id: {s.voice.elevenlabs_voice_id or 'fehlt'}")
        ok = ok and bool(s.elevenlabs_api_key and s.voice.elevenlabs_voice_id)
    else:
        print(("✔" if s.voice.higgsfield_voice_id else "✘") + " Higgsfield voice_id")
    has_claude = bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN") or shutil.which("ant"))
    print(("✔" if has_claude else "✘") + " ANTHROPIC_API_KEY (für das Briefing)")
    ok = ok and has_claude
    try:
        print(f"✔ ffmpeg: {ffmpeg_bin()}")
    except Exception as exc:
        ok = False
        print(f"✘ {exc}")
    fonts = [p.name for p in s.fonts_path.glob("*.ttf")]
    print(("✔" if fonts else "✘") + f" Schriften: {', '.join(fonts) or 'fehlen'}")
    print(f"\nBeiträge-Ordner: {s.path(s.sources.posts_dir)}")
    print(f"Ausgabe: {s.output_path}")
    print("\nAlles bereit." if ok else "\nBitte die markierten Punkte erledigen.")
    return 0 if ok else 1


def cmd_soul_create(args) -> int:
    s = _settings(args)
    from .higgsfield import Higgsfield

    photos_dir = Path(args.photos or s.path(s.character.photos_dir))
    photos = sorted(p for p in photos_dir.glob("*") if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"})
    if len(photos) < 5:
        print(f"Mindestens 5 Fotos nötig, gefunden: {len(photos)} in {photos_dir}")
        return 1
    hf = Higgsfield(s)
    name = args.name or s.character.name
    print(f"Trainiere Soul ID „{name}“ mit {len(photos)} Fotos ({args.variant}) …")
    soul_id = hf.soul_create(name, photos[:20], args.variant)
    print(f"Training gestartet: {soul_id}. Warte …")
    hf.soul_wait(soul_id)
    print(f"\nSoul ID bereit: {soul_id}")
    print("Trage sie in soul-studio/config.yaml unter character.soul_id ein (oder setze SOUL_ID in .env).")
    return 0


def cmd_soul_list(args) -> int:
    from .higgsfield import Higgsfield
    print(json.dumps(Higgsfield(_settings(args)).soul_list(), indent=2, ensure_ascii=False))
    return 0


def cmd_voices(args) -> int:
    s = _settings(args)
    if s.voice.provider == "elevenlabs":
        from .voice import elevenlabs_voices
        for v in elevenlabs_voices(s):
            print(f"{v['voice_id']}  {v['name']}  ({v['category']})")
    else:
        from .higgsfield import Higgsfield
        print(json.dumps(Higgsfield(s).voices(), indent=2, ensure_ascii=False))
    return 0


def _load_post(args):
    if args.text:
        return post_from_text(args.text, args.title)
    return post_from_file(Path(args.post))


def cmd_brief(args) -> int:
    s = _settings(args)
    post = _load_post(args)
    producer = Producer(s, dry_run=True)
    out_dir = s.output_path / post.slug
    brief = producer.brief_for(post, out_dir, args.format, reuse=not args.fresh)
    print(json.dumps(brief.model_dump(), indent=2, ensure_ascii=False))
    print(f"\nGespeichert: {out_dir / 'brief.json'}")
    return 0


def cmd_produce(args) -> int:
    s = _settings(args)
    post = _load_post(args)
    producer = Producer(s, dry_run=args.dry_run, mock=args.mock)
    result = producer.produce(post, args.format, parallel=args.parallel)
    print(f"\nErgebnis: {result.media}\nBeitragstext: {result.output_dir / 'caption.txt'}")
    if not args.no_state and not args.dry_run:
        State(s.state_path).mark(post, {"format": result.format, "media": str(result.media)})
    return 0


def _run_once(s: Settings, args) -> int:
    state = State(s.state_path)
    posts = new_posts(s, state)
    if not posts:
        print("Keine neuen Beiträge.")
        return 0
    print(f"{len(posts)} neue(r) Beitrag/Beiträge.")
    producer = Producer(s, dry_run=args.dry_run, mock=args.mock)
    failures = 0
    for post in posts[: args.limit]:
        try:
            result = producer.produce(post, parallel=args.parallel)
        except Exception as exc:
            failures += 1
            print(f"✘ Fehler bei „{post.title}“: {exc}")
            continue
        if args.dry_run:
            continue
        url = result_public_url(result, s)
        info = {"format": result.format, "media": str(result.media), "url": url}
        if s.publish.enabled and args.publish:
            try:
                from .publish import schedule_metricool
                info["metricool"] = schedule_metricool(s, result.caption, url)
                print("  Im Metricool-Planer angelegt.")
            except Exception as exc:
                print(f"  Metricool übersprungen: {exc}")
        if post.notion_page_id:
            try:
                notion_mark_done(s, post.notion_page_id, url)
            except Exception as exc:
                print(f"  Notion-Status nicht aktualisiert: {exc}")
        state.mark(post, info)
    return 1 if failures else 0


def cmd_run(args) -> int:
    return _run_once(_settings(args), args)


def cmd_watch(args) -> int:
    s = _settings(args)
    print(f"Beobachte {s.path(s.sources.posts_dir)} alle {args.interval} s. Strg+C zum Beenden.")
    while True:
        try:
            _run_once(s, args)
        except KeyboardInterrupt:
            return 0
        except Exception as exc:
            print(f"Fehler: {exc}")
        time.sleep(args.interval)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="soul-studio", description="Automatische Videos und Bilder mit deiner Soul ID.")
    p.add_argument("--config", help="Pfad zur config.yaml")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("check", help="Systemcheck: CLI, Schlüssel, ffmpeg").set_defaults(fn=cmd_check)

    sc = sub.add_parser("soul", help="Soul ID verwalten")
    ssub = sc.add_subparsers(dest="soul_cmd", required=True)
    c = ssub.add_parser("create", help="Soul ID aus Fotos trainieren")
    c.add_argument("--name")
    c.add_argument("--photos", help="Ordner mit 5–20 Fotos")
    c.add_argument("--variant", choices=["soul-2", "soul-cinematic"], default="soul-2")
    c.set_defaults(fn=cmd_soul_create)
    ssub.add_parser("list", help="Vorhandene Soul IDs").set_defaults(fn=cmd_soul_list)

    sub.add_parser("voices", help="Stimmen auflisten").set_defaults(fn=cmd_voices)

    for name, fn, helptext in (("brief", cmd_brief, "Nur das Briefing erzeugen"),
                               ("produce", cmd_produce, "Einen Beitrag produzieren")):
        c = sub.add_parser(name, help=helptext)
        c.add_argument("post", nargs="?", help="Datei (.md/.txt/.html)")
        c.add_argument("--text", help="Beitragstext direkt übergeben")
        c.add_argument("--title")
        c.add_argument("--format", choices=["video", "image"])
        if name == "brief":
            c.add_argument("--fresh", action="store_true", help="Vorhandenes Briefing verwerfen")
        else:
            c.add_argument("--dry-run", action="store_true", help="Nur Briefing, keine Generierung")
            c.add_argument("--mock", action="store_true", help="Platzhalter statt Higgsfield/ElevenLabs (Test)")
            c.add_argument("--parallel", type=int, default=3)
            c.add_argument("--no-state", action="store_true")
        c.set_defaults(fn=fn)

    for name, fn, helptext in (("run", cmd_run, "Alle neuen Beiträge produzieren"),
                               ("watch", cmd_watch, "Ordner dauerhaft beobachten")):
        c = sub.add_parser(name, help=helptext)
        c.add_argument("--dry-run", action="store_true")
        c.add_argument("--mock", action="store_true")
        c.add_argument("--publish", action="store_true", help="Zusätzlich in Metricool einplanen")
        c.add_argument("--limit", type=int, default=5)
        c.add_argument("--parallel", type=int, default=3)
        if name == "watch":
            c.add_argument("--interval", type=int, default=300)
        c.set_defaults(fn=fn)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
