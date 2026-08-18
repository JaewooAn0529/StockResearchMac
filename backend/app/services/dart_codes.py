"""DART API는 6자리 종목코드가 아니라 8자리 고유번호(corp_code)를 요구한다.

이 매핑은 DART가 별도 API로 전체 목록(ZIP)을 내려주는 방식이라, universe.py의
KIND 캐싱과 같은 패턴으로 프로세스 생애주기 동안 한 번만 받아서 메모리에 둔다.
"""

from __future__ import annotations

import io
import xml.etree.ElementTree as ET
import zipfile

import requests

from app.core.config import DART_API_KEY

_URL = "https://opendart.fss.or.kr/api/corpCode.xml"

_cache: dict[str, str] | None = None  # 종목코드(6자리) -> DART corp_code(8자리)


def _build_map() -> dict[str, str]:
    res = requests.get(_URL, params={"crtfc_key": DART_API_KEY}, timeout=30)
    res.raise_for_status()
    z = zipfile.ZipFile(io.BytesIO(res.content))
    root = ET.fromstring(z.read("CORPCODE.xml"))

    mapping = {}
    for item in root.findall("list"):
        stock_code = (item.findtext("stock_code") or "").strip()
        if not stock_code:  # 비상장사는 공백
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
