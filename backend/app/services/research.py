"""리서치 전용 벌크 조회 (앱 UI가 아니라 백테스트/외부 스크립트가 쓰는 용도).

/stocks/{ticker}/flows는 종목 하나의 기간별 시계열을 주지만, 여기는 반대로
"하루" 기준으로 시장 전체 종목을 외국인 순매수 순위로 뽑는다. 종목마다
개별 호출하면 3년 백필에 KOSPI 847종목 × 750거래일 = 수십만 번 호출이라
비현실적이라, pykrx의 시장 전체 벌크 함수(하루 3콜)로 대체했다.
"""

from __future__ import annotations

import contextlib
import io
from datetime import datetime, timedelta, timezone

from pykrx import stock

from app.services import news as news_service

KST = timezone(timedelta(hours=9))

_INDEX_CODE = {"KOSPI": "1001", "KOSDAQ": "2001"}


class UpstreamFetchError(RuntimeError):
    """KRX 응답 실패(요청 제한 등)로 데이터를 못 받은 경우. 휴장일과는 다르다.

    pykrx는 json.JSONDecodeError 같은 파싱 실패를 내부에서 삼키고
    "Error occurred in ..."을 표준출력에 찍은 뒤 빈 DataFrame을 반환한다
    (site-packages/pykrx/website/comm/util.py의 dataframe_empty_handler).
    그래서 겉보기엔 "그냥 빈 데이터"라 휴장일과 구분이 안 되는데, 백필처럼
    반복 호출하는 입장에선 이 둘을 절대 같은 걸로 취급하면 안 된다 —
    휴장일은 건너뛰어야 하지만, 요청 제한은 재시도해야 하고, 그걸 "휴장일"로
    기록해버리면 데이터가 조용히 빠진 채로 완성된 것처럼 보인다.
    """


@contextlib.contextmanager
def _detect_upstream_errors():
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        yield
    if "Error occurred in" in buf.getvalue():
        raise UpstreamFetchError(buf.getvalue().strip())


def _same_day_news_count(name: str, date_str: str) -> int | None:
    """daily_log.py의 fetch_news_counts와 같은 개념 — 해당일 발행 기사 수.

    stock-briefing 쪽 원본은 Naver API를 직접 호출했지만, 여기서는 이미
    같은 필터링(제목에 종목명 포함 여부)이 들어간 news_service.get_news를
    재사용한다. 종목마다 API 호출 1번이라 비용이 크므로 top_n으로 개수를
    제한했을 때만 켜는 걸 권장한다.
    """
    target = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
    try:
        articles = news_service.get_news(name, limit=100)
    except Exception as exc:
        print(f"[warn] {name} 뉴스 조회 실패: {exc}")
        return None
    return sum(1 for a in articles if a["published_at"].startswith(target))


def get_daily_snapshot(
    date_str: str,
    market: str = "KOSPI",
    top_n: int | None = None,
    include_news: bool = False,
) -> dict | None:
    """date_str: YYYYMMDD. 휴장일이면 None.

    top_n: daily_log.py처럼 상위 N개만 남기고 싶을 때 지정 (기본은 전종목 반환).
    include_news: True면 top_n으로 걸러진 종목에 한해 당일 뉴스 건수를 채운다
    (종목당 API 호출 1번이라 전종목에 걸면 느리고 쿼터도 빨리 소진된다).
    """
    if market not in _INDEX_CODE:
        raise ValueError(f"지원하지 않는 시장: {market} (KOSPI/KOSDAQ만 가능)")

    with _detect_upstream_errors():
        flow = stock.get_market_net_purchases_of_equities_by_ticker(date_str, date_str, market, "외국인")
    if flow is None or flow.empty:
        return None  # 진짜 휴장일 — 에러 없이 그냥 빈 데이터였던 경우만 여기 도달

    with _detect_upstream_errors():
        price = stock.get_market_ohlcv(date_str, market=market)
    with _detect_upstream_errors():
        index = stock.get_index_ohlcv(date_str, date_str, _INDEX_CODE[market])
    kospi_close = float(index["종가"].iloc[0]) if index is not None and not index.empty else None

    merged = flow.join(price[["종가"]], how="inner")
    merged = merged.sort_values("순매수거래대금", ascending=False)
    if top_n is not None:
        merged = merged.head(top_n)

    rows = []
    for rank, (ticker, row) in enumerate(merged.iterrows(), start=1):
        name = row["종목명"]
        rows.append({
            "date": f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}",
            "ticker": ticker,
            "name": name,
            "rank": rank,
            "foreign_net_buy": int(row["순매수거래대금"]),
            "close": int(row["종가"]),
            # 필드명은 kospi_close로 고정 — daily_log.py 스키마와 맞추기 위함.
            # market=KOSDAQ로 호출하면 이 값엔 코스닥지수 종가가 들어간다.
            "kospi_close": kospi_close,
            "news_count": _same_day_news_count(name, date_str) if include_news else None,
        })

    return {
        "date": f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}",
        "market": market,
        "count": len(rows),
        "rows": rows,
    }
