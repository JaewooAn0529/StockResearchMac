"""외국인/기관 순매수 추이 (지표 #2, 수급 동향).

daily_log.py의 fetch_foreign_net_buy는 "특정일의 전체 종목 top-N"을 뽑는
용도라 종목 상세 화면에는 안 맞는다. 대신 get_market_trading_value_by_date로
한 종목의 기간별 투자자별(외국인/기관) 순매수 금액 시계열을 가져온다.
detail=False(기본값) 기준 컬럼은 기관합계/기타법인/개인/외국인합계/전체.
"""

from __future__ import annotations  # list[dict] | None 문법은 Python 3.10+ 필요 (이 환경은 3.9)

from datetime import datetime, timedelta, timezone

from pykrx import stock

KST = timezone(timedelta(hours=9))


def get_flows(ticker: str, days: int = 90) -> list[dict] | None:
    end = datetime.now(KST)
    start = end - timedelta(days=days)
    df = stock.get_market_trading_value_by_date(
        start.strftime("%Y%m%d"), end.strftime("%Y%m%d"), ticker
    )
    if df is None or df.empty:
        return None

    return [
        {
            "date": idx.strftime("%Y-%m-%d"),
            "foreign_net_buy": int(row.get("외국인합계", 0)),
            "institution_net_buy": int(row.get("기관합계", 0)),
        }
        for idx, row in df.iterrows()
    ]
