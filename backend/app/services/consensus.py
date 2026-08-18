"""애널리스트 컨센서스 목표주가 (지표 #9).

이건 "우리 자체 판단"이 아니라 "증권사들의 공개된 데이터 인용"이므로 자체
분석 지표와 분리해서 다루고, source 필드로 출처를 명확히 밝힌다.

pykrx에는 컨센서스 데이터가 없다. 네이버금융의 coinfo.naver 종목분석 페이지에
에프앤가이드가 집계한 "투자의견/목표주가" 표가 공개되어 있어 이를 파싱한다.
(증권사 추정치가 3곳 미만인 종목은 이 표 자체가 비어 있을 수 있다 — 그 경우 None)
"""

from __future__ import annotations

import requests
from bs4 import BeautifulSoup

_URL = "https://finance.naver.com/item/coinfo.naver"
_SOURCE = "네이버금융 컨센서스(에프앤가이드 집계, 증권사 3곳 이상 평균)"


def get_consensus(ticker: str) -> dict | None:
    res = requests.get(_URL, params={"code": ticker}, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
    res.raise_for_status()
    res.encoding = "euc-kr"

    soup = BeautifulSoup(res.text, "lxml")
    table = soup.find("table", attrs={"summary": "투자의견 정보"})
    if table is None:
        return None

    first_row_td = table.find("tr").find("td")
    if first_row_td is None:
        return None

    ems = first_row_td.find_all("em")
    if len(ems) < 2:
        return None  # 커버리지(추정 증권사 3곳 이상) 없는 종목

    opinion_score_text = ems[0].get_text(strip=True)
    target_price_text = ems[1].get_text(strip=True)

    opinion_span = first_row_td.find("span", class_=lambda c: bool(c) and c.startswith("f_"))
    opinion_text = None
    if opinion_span:
        opinion_text = opinion_span.get_text(strip=True).replace(opinion_score_text, "", 1).strip()

    try:
        opinion_score = float(opinion_score_text)
        target_price = int(target_price_text.replace(",", ""))
    except ValueError:
        return None

    return {
        "opinion_score": opinion_score,
        "opinion_text": opinion_text,
        "target_price": target_price,
        "source": _SOURCE,
    }
