from fastapi import APIRouter, HTTPException

from app.models.schemas import DailySnapshotResponse
from app.services import research as research_service

router = APIRouter(prefix="/research", tags=["research"])


@router.get("/daily-snapshot", response_model=DailySnapshotResponse)
def daily_snapshot(date: str, market: str = "KOSPI", top_n: int | None = None, include_news: bool = False):
    """Returns all market stocks for a given trading day, ranked by foreign net buying.

    This isn't the real-time endpoint the app UI uses — it's meant to be called
    repeatedly by backfill/backtest scripts. date is YYYYMMDD. Pass top_n to get
    only the top N (e.g. 20 — matches daily_log.py's TOP_N), and include_news=true
    fills in that day's news count for just those N stocks (one API call per stock,
    so it's expensive and not recommended without top_n).
    """
    try:
        result = research_service.get_daily_snapshot(date, market, top_n=top_n, include_news=include_news)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except research_service.UpstreamFetchError as exc:
        # Different from a market-holiday case (404) — this is a KRX request failure
        # (usually rate limiting from too many consecutive calls), so the caller should
        # back off and retry. If a backfill script mistakes this for "market holiday"
        # and silently skips it, the data ends up looking complete when it's actually
        # missing, so this must be signaled with a distinct status code.
        raise HTTPException(
            status_code=503,
            detail=f"KRX 응답 실패 (요청 제한 가능성) — 잠시 후 재시도하세요: {exc}",
        )

    if result is None:
        raise HTTPException(status_code=404, detail="해당 날짜에 거래 데이터가 없습니다 (휴장일일 수 있음)")
    return result
