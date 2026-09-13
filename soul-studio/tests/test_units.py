"""Schnelle Tests ohne externe Dienste: python -m pytest soul-studio/tests -q"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from soul_studio.brief import Block, Brief, Slide, format_from_notion, json_schema, normalize   # noqa: E402
from soul_studio.captions import build_ass, _chunks                                      # noqa: E402
from soul_studio.carousel import render_carousel                                          # noqa: E402
from PIL import Image                                                                       # noqa: E402
from soul_studio.config import Settings, load_settings                                     # noqa: E402
from soul_studio.images import editorial_card, end_card, statement_image                   # noqa: E402
from soul_studio.sources import html_to_text, post_from_text                              # noqa: E402
from soul_studio.voice import Word, _words_from_alignment, evenly_timed_words              # noqa: E402


def test_config_loads_defaults(tmp_path):
    s = load_settings(tmp_path / "missing.yaml")
    assert s.brand.colors.burgundy == "#4A081E"
    assert s.footage.provider == "pexels"
    assert s.notion.trigger_status == "Produzieren"


def test_html_to_text_strips_scripts_and_keeps_title():
    title, text = html_to_text("<html><head><title>Hallo · Desk Revolution</title><style>x{}</style></head>"
                               "<body><script>var a=1</script><h1>Kopf</h1><p>Erster&nbsp;Absatz</p></body></html>")
    assert title.startswith("Hallo")
    assert "var a" not in text and "Hallo" not in text
    assert "Kopf" in text and "Erster Absatz" in text


def test_post_slug_is_stable_and_safe():
    p = post_from_text("Der Posteingang entscheidet nicht über deinen Tag\n\nText …")
    q = post_from_text("Der Posteingang entscheidet nicht über deinen Tag\n\nText …")
    assert p.id == q.id and p.slug.startswith("der-posteingang-entscheidet") and " " not in p.slug


def test_notion_format_mapping():
    assert format_from_notion("Reel") == "video"
    assert format_from_notion("Carousel") == "carousel"
    assert format_from_notion("Bild") == "image"
    assert format_from_notion("Post") == "none"
    assert format_from_notion(None) is None


def test_brief_schema_and_normalize():
    schema = json_schema()
    assert "format" in schema["properties"] and "slides" in schema["properties"]
    b = Brief(format="carousel", title="t", hook="h", caption="c", hashtags=["#a", "b"],
              slides=[Slide(index=9, kind="cover", headline="x"), Slide(index=9, kind="cta", headline="y")])
    b = normalize(b, Settings())
    assert [s.index for s in b.slides] == [1, 2] and b.hashtags == ["a", "b"]
    assert b.caption_with_tags().endswith("#a #b")


def test_words_from_alignment_groups_characters():
    alignment = {"characters": list("Hallo du"),
                 "character_start_times_seconds": [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7],
                 "character_end_times_seconds": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]}
    words = _words_from_alignment(alignment)
    assert [w.text for w in words] == ["Hallo", "du"]
    assert words[0].end == 0.5 and words[1].start == 0.6


def test_evenly_timed_words_cover_duration():
    words = evenly_timed_words("eins zwei drei", 3.0)
    assert len(words) == 3 and abs(words[-1].end - 3.0) < 1e-6


def test_build_ass_word_mode_highlights_each_word():
    ass = build_ass([Word("Vier", 0.0, 0.4), Word("Mails.", 0.4, 0.9), Word("Und", 1.0, 1.2)], Settings(),
                    overlays=[(0.3, 2.0, "64 Mails")])
    assert "PlayResX: 1080" in ass and "Style: Caption,League Spartan" in ass
    assert ass.count("Dialogue: 0,") == 3 and "&H7AA2FC" in ass and "64 Mails" in ass


def test_chunks_respect_word_and_char_limits():
    words = [Word(t, i * 0.3, i * 0.3 + 0.3) for i, t in enumerate("Vierundsechzig ungelesene Mails. Und ich lese keine davon.".split())]
    chunks = _chunks(words, 3, max_chars=18)
    assert all(len(c) <= 3 for c in chunks)
    assert chunks[0][0].text == "Vierundsechzig" and len(chunks[0]) == 1


def test_ass_color_conversion():
    from soul_studio.media import hex_to_ass
    assert hex_to_ass("#4A081E") == "&H001E084A" and hex_to_ass("#FAF7F0", 0x40) == "&H40F0F7FA"


def test_carousel_and_images_render(tmp_path):
    s = Settings()
    slides = [Slide(index=1, kind="cover", headline="Der Posteingang entscheidet nicht über deinen Tag", body="Drei Stapel statt 64 Zeilen"),
              Slide(index=2, kind="content", headline="Vorsortieren lassen", body="Was braucht heute eine Antwort? Was kann warten?"),
              Slide(index=3, kind="cta", headline="Welchen Stapel gibst du zuerst ab?", body="Schreib es in die Kommentare.")]
    pngs, pdf = render_carousel(slides, s, tmp_path / "car")
    assert len(pngs) == 3 and pdf.exists() and pdf.stat().st_size > 1000
    img = statement_image(s, "Der Posteingang entscheidet nicht über deinen Tag", "Wer bestimmt die Reihenfolge?", tmp_path / "b.jpg")
    assert img.exists()
    assert end_card(s, tmp_path / "e.png").exists()


def test_editorial_card_fits_long_and_short_content(tmp_path):
    s = Settings()
    scene = tmp_path / "scene.jpg"
    Image.new("RGB", (1200, 1500), (200, 150, 120)).save(scene)
    long_out = editorial_card(
        s, scene, "KI erledigt die Aufgabe. Die Verantwortung bleibt bei dir.",
        "Eine Aufgabe kann KI übernehmen. Verantwortung beginnt dort, wo ein Ergebnis verstanden werden muss.\n"
        "Welche Aufgabe hast du zuletzt an KI abgegeben, bei der die eigentliche Arbeit erst danach begann?",
        tmp_path / "long.jpg")
    short_out = editorial_card(s, scene, "Kurz.", "Auch kurz.", tmp_path / "short.jpg")
    assert long_out.exists() and short_out.exists()
    assert Image.open(long_out).size == (1080, 1350)


def test_mixed_mode_forces_talking_hook_and_ending():
    s = Settings()
    s.video.mode = "mixed"
    blocks = [Block(index=i, kind="broll", narration="x", footage_query="q") for i in range(1, 5)]
    b = normalize(Brief(format="video", title="t", hook="h", caption="c", blocks=blocks), s)
    assert [x.kind for x in b.blocks] == ["talking", "broll", "broll", "talking"]
    s.video.mode = "broll_only"
    b = normalize(Brief(format="video", title="t", hook="h", caption="c", blocks=blocks), s)
    assert all(x.kind == "broll" for x in b.blocks)
