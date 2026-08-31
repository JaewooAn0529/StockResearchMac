"""The DART API requires an 8-digit unique corp_code, not the 6-digit ticker.

DART provides this mapping as a full list (ZIP) via a separate API, so — following
the same pattern as the KIND caching in universe.py — we fetch it once per process
lifetime and keep it in memory.
"""

from __future__ import annotations

import io
import xml.etree.ElementTree as ET
import zipfile

import requests

from app.core.config import DART_API_KEY

_URL = "https://opendart.fss.or.kr/api/corpCode.xml"

_cache: dict[str, str] | None = None  # ticker (6 digits) -> DART corp_code (8 digits)


def _build_map() -> dict[str, str]:
    res = requests.get(_URL, params={"crtfc_key": DART_API_KEY}, timeout=30)
    res.raise_for_status()
    z = zipfile.ZipFile(io.BytesIO(res.content))
    root = ET.fromstring(z.read("CORPCODE.xml"))

    mapping = {}
    for item in root.findall("list"):
        stock_code = (item.findtext("stock_code") or "").strip()
        if not stock_code:  # blank for unlisted companies
            continue
        mapping[stock_code] = item.findtext("corp_code")
    return mapping


def get_corp_code(ticker: str) -> str | None:
    global _cache
    if not DART_API_KEY:
        return None
    if _cache is None:
        _cache = _build_map()
    return _cache.get(ticker)
