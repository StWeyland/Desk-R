"""Beiträge als Datei oder Text (für Tests und Einzelproduktionen) und die Status-Datei."""
from __future__ import annotations

import hashlib
import html
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path


@dataclass
class Post:
    id: str
    title: str
    text: str
    source: str = "inline"
    path: str | None = None
    notion_page_id: str | None = None
    notion_format: str | None = None
    meta: dict = field(default_factory=dict)

    @property
    def slug(self) -> str:
        base = re.sub(r"[^a-z0-9]+", "-", self.title.lower()).strip("-")[:48] or "beitrag"
        return f"{base}-{self.id[:8]}"


class _TextExtractor(HTMLParser):
    SKIP = {"head", "script", "style", "noscript", "svg", "form", "nav", "footer", "header"}

    def __init__(self) -> None:
        super().__init__()
        self._skip = 0
        self.parts: list[str] = []
        self.title = ""
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self._skip += 1
        if tag == "title":
            self._in_title = True
        if tag in {"p", "br", "h1", "h2", "h3", "h4", "li", "div", "section", "blockquote"}:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in self.SKIP and self._skip:
            self._skip -= 1
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        elif not self._skip:
            self.parts.append(data)


def html_to_text(raw: str) -> tuple[str, str]:
    p = _TextExtractor()
    p.feed(raw)
    text = html.unescape("".join(p.parts)).replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text).strip()
    return p.title.strip(), text


def _hash(text: str) -> str:
    return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()[:16]


def _title_from_text(text: str, fallback: str) -> str:
    for line in text.splitlines():
        line = line.strip().lstrip("#").strip()
        if line:
            return line[:80]
    return fallback


def post_from_file(path: Path) -> Post:
    raw = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".html", ".htm"}:
        title, text = html_to_text(raw)
        title = title.split("·")[0].split("|")[0].strip() or path.stem
    else:
        text = raw
        title = _title_from_text(text, path.stem)
    return Post(id=_hash(text), title=title, text=text, source="folder", path=str(path))


def post_from_text(text: str, title: str | None = None) -> Post:
    return Post(id=_hash(text), title=title or _title_from_text(text, "beitrag"), text=text)


def post_from_job(path: Path) -> Post:
    """Job-Datei aus der Routine: {"title", "text", "format", "page_id"}."""
    data = json.loads(path.read_text(encoding="utf-8"))
    text = data.get("text", "")
    return Post(id=_hash(data.get("page_id") or text), title=data.get("title") or _title_from_text(text, "beitrag"),
                text=text, source="notion", notion_page_id=data.get("page_id"), notion_format=data.get("format"),
                meta=data)


class State:
    def __init__(self, path: Path):
        self.path = path
        self.data: dict = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}

    def is_done(self, post_id: str) -> bool:
        return post_id in self.data

    def mark(self, post: Post, result: dict) -> None:
        self.data[post.id] = {"title": post.title, "source": post.source, "path": post.path,
                              "at": datetime.now(timezone.utc).isoformat(timespec="seconds"), **result}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, indent=2, ensure_ascii=False), encoding="utf-8")
