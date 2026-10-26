"""Analyst consensus target price (indicator #9).

This is a "quote of publicly available brokerage data," not "our own judgment,"
so it's handled separately from our own analytical indicators, and the source
field clearly discloses where it came from.

pykrx has no consensus data. Naver Finance's coinfo.naver stock-analysis page
publishes an "opinion / target price" table aggregated by FnGuide, so we parse
that. (For stocks covered by fewer than 3 brokerages, this table itself may be
empty — in that case we return None.)
"""

from __future__ import annotations

import requests
from bs4 import BeautifulSoup

_URL = "https://finance.naver.com/item/coinfo.naver"
_SOURCE = "Naver Finance consensus (FnGuide aggregate, average of 3+ brokers)"


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
        return None  # no coverage (fewer than 3 brokerages providing estimates)

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
