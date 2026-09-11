"""Optional: fertige Beiträge über die Metricool-API im Planer anlegen."""
from __future__ import annotations

from datetime import datetime, timedelta

import httpx

from .config import Settings

METRICOOL_API = "https://app.metricool.com/api/v2"


def schedule_metricool(settings: Settings, text: str, media_url: str | None, when: datetime | None = None) -> dict:
    m = settings.publish.metricool
    token = settings.metricool_token
    if not (token and m.user_id and m.blog_id):
        raise RuntimeError("METRICOOL_TOKEN, publish.metricool.user_id und blog_id werden benötigt.")
    when = when or (datetime.now() + timedelta(hours=m.schedule_offset_hours)).replace(minute=0, second=0, microsecond=0)
    body = {
        "providers": [{"network": n} for n in m.networks],
        "publicationDate": {"dateTime": when.strftime("%Y-%m-%dT%H:%M:%S"), "timezone": m.timezone},
        "text": text,
        "media": [media_url] if media_url else [],
        "autoPublish": not m.draft,
        "draft": m.draft,
    }
    with httpx.Client(timeout=60) as c:
        r = c.post(f"{METRICOOL_API}/scheduler/posts", params={"userId": m.user_id, "blogId": m.blog_id},
                   headers={"X-Mc-Auth": token, "Content-Type": "application/json"}, json=body)
        r.raise_for_status()
        return r.json() if r.content else {}
