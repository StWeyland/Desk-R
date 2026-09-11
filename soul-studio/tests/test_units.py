"""Schnelle Tests ohne externe Dienste: python -m pytest soul-studio/tests -q"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from soul_studio.captions import build_ass                      # noqa: E402
from soul_studio.config import Settings, load_settings           # noqa: E402
from soul_studio.higgsfield import Higgsfield, parse_job         # noqa: E402
from soul_studio.sources import html_to_text, post_from_text     # noqa: E402
from soul_studio.voice import Word, _words_from_alignment, evenly_timed_words  # noqa: E402


def test_config_loads_defaults(tmp_path):
    s = load_settings(tmp_path / "missing.yaml")
    assert s.brand.colors.burgundy == "#4A081E"
    assert s.video.aspect_ratio == "9:16"
    assert s.models.image == "text2image_soul_v2"


def test_html_to_text_strips_scripts_and_keeps_title():
    title, text = html_to_text("<html><head><title>Hallo · Desk Revolution</title><style>x{}</style></head>"
                               "<body><script>var a=1</script><h1>Kopf</h1><p>Erster&nbsp;Absatz</p></body></html>")
    assert title.startswith("Hallo")
    assert "var a" not in text
    assert "Kopf" in text and "Erster Absatz" in text


def test_post_slug_is_stable_and_safe():
    p = post_from_text("Der Posteingang entscheidet nicht über deinen Tag\n\nText …")
    q = post_from_text("Der Posteingang entscheidet nicht über deinen Tag\n\nText …")
    assert p.id == q.id
    assert p.slug.startswith("der-posteingang-entscheidet")
    assert " " not in p.slug


def test_parse_job_finds_url_in_nested_result():
    raw = [{"id": "job-1", "status": "completed", "results": [{"url": "https://cdn.example/x.mp4"}]}]
    job = parse_job(raw)
    assert job.ok and job.id == "job-1" and job.result_url.endswith("x.mp4")
    raw2 = {"job": {"id": "j2", "status": "failed"}}
    assert not parse_job(raw2).ok


def test_generate_builds_cli_args(monkeypatch):
    s = Settings()
    s.character.soul_id = "soul-123"
    hf = Higgsfield(s)
    seen = {}

    def fake_run(*args, **kwargs):
        seen["args"] = args
        return {"id": "j", "status": "completed", "result_url": "https://cdn/x.png"}

    monkeypatch.setattr(hf, "run", fake_run)
    hf.generate("text2image_soul_v2", {"prompt": "p", "aspect_ratio": "9:16", "soul-id": "soul-123", "sound": False},
                {"start-image": "/tmp/a.png", "audio": ["/tmp/v.mp3"]})
    a = seen["args"]
    assert a[:3] == ("generate", "create", "text2image_soul_v2")
    assert "--soul-id" in a and "soul-123" in a
    assert "--start-image" in a and "--audio" in a
    assert a[a.index("--sound") + 1] == "false"
    assert "--wait" in a


def test_words_from_alignment_groups_characters():
    alignment = {
        "characters": list("Hallo du"),
        "character_start_times_seconds": [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7],
        "character_end_times_seconds": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8],
    }
    words = _words_from_alignment(alignment)
    assert [w.text for w in words] == ["Hallo", "du"]
    assert words[0].start == 0.0 and words[0].end == 0.5
    assert words[1].start == 0.6


def test_evenly_timed_words_cover_duration():
    words = evenly_timed_words("eins zwei drei", 3.0)
    assert len(words) == 3
    assert abs(words[-1].end - 3.0) < 1e-6


def test_build_ass_word_mode_highlights_each_word():
    s = Settings()
    words = [Word("Vier", 0.0, 0.4), Word("Mails.", 0.4, 0.9), Word("Und", 1.0, 1.2)]
    ass = build_ass(words, s, overlays=[(0.3, 2.0, "64 Mails")])
    assert "PlayResX: 1080" in ass
    assert "Style: Caption,League Spartan" in ass
    assert ass.count("Dialogue: 0,") == 3            # ein Dialog pro Wort
    assert "&H7AA2FC" in ass                          # Salmon als Hervorhebung
    assert "Dialogue: 1," in ass and "64 Mails" in ass


def test_ass_color_conversion():
    from soul_studio.media import hex_to_ass
    assert hex_to_ass("#4A081E") == "&H001E084A"
    assert hex_to_ass("#FAF7F0", 0x40) == "&H40F0F7FA"


def test_chunks_respect_word_and_char_limits():
    from soul_studio.captions import _chunks
    words = [Word(t, i * 0.3, i * 0.3 + 0.3) for i, t in enumerate("Vierundsechzig ungelesene Mails. Und ich lese keine davon.".split())]
    chunks = _chunks(words, 3, max_chars=18)
    assert all(len(c) <= 3 for c in chunks)
    assert all(len(" ".join(w.text for w in c)) <= 18 or len(c) == 1 for c in chunks)
    assert chunks[0][0].text == "Vierundsechzig" and len(chunks[0]) == 1
