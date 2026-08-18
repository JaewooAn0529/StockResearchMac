"""네이버 뉴스 수집 (뉴스/센티먼트 분석가의 입력).

stock-briefing/briefing.py의 today_news를 확장했다. 원본은 "오늘 발행된
기사"만 최대 2건 받았지만, 여기서는 토론에 쓸 근거가 필요하므로 기간 제한을
풀고 최신순 N건을 가져온다.

NAVER 키가 없으면 조용히 빈 리스트를 반환한다 — 뉴스 없이도 나머지
에이전트들은 정상 동작해야 한다.
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
        # 종목명이 제목에 없으면 동명이인/무관 기사일 확률이 높다
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
