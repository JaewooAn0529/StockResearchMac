"""Naver News collection (input for the news/sentiment analyst).

Extends today_news from stock-briefing/briefing.py. The original fetched at
most 2 articles, only "articles published today," but here we need supporting
evidence for the debate, so we drop the date restriction and fetch the N most
recent articles instead.

If the NAVER keys are missing, this silently returns an empty list — the
other agents should still work fine even without news.
"""

from __future__ import annotations

from datetime import timedelta, timezone
from email.utils import parsedate_to_datetime

import requests

from app.core.config import NAVER_CLIENT_ID, NAVER_CLIENT_SECRET

KST = timezone(timedelta(hours=9))
_URL = "https://openapi.naver.com/v1/search/news.json"


def _strip_tags(s: str) -> str:
    return (
        s.replace("<b>", "").replace("</b>", "")
        .replace("&quot;", '"').replace("&amp;", "&")
        .replace("&lt;", "<").replace("&gt;", ">")
    )


def get_news(name: str, limit: int = 10) -> list[dict]:
    if not (NAVER_CLIENT_ID and NAVER_CLIENT_SECRET):
        return []

    res = requests.get(
        _URL,
        headers={
            "X-Naver-Client-Id": NAVER_CLIENT_ID,
            "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
        },
        params={"query": name, "display": 100, "sort": "date"},
        timeout=10,
    )
    res.raise_for_status()

    out = []
    for item in res.json().get("items", []):
        title = _strip_tags(item["title"])
        # if the stock name isn't in the title, it's likely an unrelated article about a namesake
        if name[:2] not in title:
            continue
        pub = parsedate_to_datetime(item["pubDate"]).astimezone(KST)
        out.append({
            "title": title,
            "description": _strip_tags(item.get("description", "")),
            "published_at": pub.strftime("%Y-%m-%d %H:%M"),
            "link": item.get("originallink") or item.get("link", ""),
        })
        if len(out) >= limit:
            break
    return out
