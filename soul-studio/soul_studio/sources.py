"""Beitragsquellen: Ordner mit Textdateien (md/txt/html) und optional Notion."""
from __future__ import annotations

import hashlib
import html
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

import httpx

from .config import Settings


@dataclass
class Post:
    id: str
    title: str
    text: str
    source: str                      # "folder" | "notion" | "inline"
    path: str | None = None
    notion_page_id: str | None = None
    meta: dict = field(default_factory=dict)

    @property
    def slug(self) -> str:
        base = re.sub(r"[^a-z0-9]+", "-", self.title.lower()).strip("-")[:48] or "beitrag"
        return f"{base}-{self.id[:8]}"


# ---------------------------------------------------------------- HTML → Text
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
    return Post(id=_hash(text), title=title or _title_from_text(text, "beitrag"), text=text, source="inline")


def folder_posts(settings: Settings) -> list[Post]:
    root = settings.path(settings.sources.posts_dir)
    if not root.exists():
        return []
    posts = []
    for p in sorted(root.rglob("*")):
        if p.is_file() and p.suffix.lower() in settings.sources.extensions and not p.name.startswith("_"):
            posts.append(post_from_file(p))
    return posts


# ---------------------------------------------------------------- Notion (optional)
NOTION_API = "https://api.notion.com/v1"


def _notion_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "Notion-Version": "2022-06-28", "Content-Type": "application/json"}


def _rich_text(prop: dict) -> str:
    kind = prop.get("type")
    items = prop.get(kind, []) if kind in {"rich_text", "title"} else []
    return "".join(i.get("plain_text", "") for i in items)


def _page_text(token: str, page_id: str) -> str:
    """Liest die Blöcke einer Notion-Seite als reinen Text."""
    out, cursor = [], None
    with httpx.Client(timeout=30) as c:
        while True:
            params = {"page_size": 100}
            if cursor:
                params["start_cursor"] = cursor
            r = c.get(f"{NOTION_API}/blocks/{page_id}/children", headers=_notion_headers(token), params=params)
            r.raise_for_status()
            data = r.json()
            for b in data.get("results", []):
                t = b.get("type")
                rt = b.get(t, {}).get("rich_text")
                if rt:
                    out.append("".join(i.get("plain_text", "") for i in rt))
            if not data.get("has_more"):
                break
            cursor = data.get("next_cursor")
    return "\n\n".join(out)


def notion_posts(settings: Settings) -> list[Post]:
    cfg = settings.sources.notion
    token = settings.notion_token
    if not (cfg.database_id and token):
        return []
    body = {"filter": {"property": cfg.status_property, "status": {"equals": cfg.ready_value}}}
    with httpx.Client(timeout=30) as c:
        r = c.post(f"{NOTION_API}/databases/{cfg.database_id}/query", headers=_notion_headers(token), json=body)
        if r.status_code == 400:   # Status-Property ist evtl. ein Select
            body = {"filter": {"property": cfg.status_property, "select": {"equals": cfg.ready_value}}}
            r = c.post(f"{NOTION_API}/databases/{cfg.database_id}/query", headers=_notion_headers(token), json=body)
        r.raise_for_status()
        pages = r.json().get("results", [])
    posts = []
    for page in pages:
        props = page.get("properties", {})
        title = _rich_text(props.get(cfg.title_property, {})) or "Beitrag"
        text = _rich_text(props.get(cfg.text_property, {})) if cfg.text_property in props else ""
        if not text.strip():
            text = _page_text(token, page["id"])
        if not text.strip():
            continue
        posts.append(Post(id=_hash(text), title=title, text=text, source="notion", notion_page_id=page["id"]))
    return posts


def notion_mark_done(settings: Settings, page_id: str, video_url: str | None = None) -> None:
    cfg = settings.sources.notion
    token = settings.notion_token
    if not token:
        return
    props: dict = {cfg.status_property: {"status": {"name": cfg.done_value}}}
    with httpx.Client(timeout=30) as c:
        r = c.patch(f"{NOTION_API}/pages/{page_id}", headers=_notion_headers(token), json={"properties": props})
        if r.status_code == 400:
            props = {cfg.status_property: {"select": {"name": cfg.done_value}}}
            c.patch(f"{NOTION_API}/pages/{page_id}", headers=_notion_headers(token), json={"properties": props})


# ---------------------------------------------------------------- Status-Datei
class State:
    def __init__(self, path: Path):
        self.path = path
        self.data: dict = {}
        if path.exists():
            self.data = json.loads(path.read_text(encoding="utf-8"))

    def is_done(self, post_id: str) -> bool:
        return post_id in self.data

    def mark(self, post: Post, result: dict) -> None:
        self.data[post.id] = {
            "title": post.title,
            "source": post.source,
            "path": post.path,
            "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            **result,
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, indent=2, ensure_ascii=False), encoding="utf-8")


def new_posts(settings: Settings, state: State) -> list[Post]:
    posts = folder_posts(settings) + notion_posts(settings)
    return [p for p in posts if not state.is_done(p.id)]
