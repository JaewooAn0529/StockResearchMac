from fastapi import APIRouter, HTTPException

from app.models.schemas import DailySnapshotResponse
from app.services import research as research_service

router = APIRouter(prefix="/research", tags=["research"])


@router.get("/daily-snapshot", response_model=DailySnapshotResponse)
def daily_snapshot(date: str, market: str = "KOSPI", top_n: int | None = None, include_news: bool = False):
    """특정 거래일의 시장 전체 종목을 외국인 순매수 순위로 반환한다.

    앱 UI가 쓰는 실시간 엔드포인트가 아니라, 백필/백테스트 스크립트가
    반복 호출하는 용도. date는 YYYYMMDD. top_n을 주면 상위 N개만(예: 20 —
    daily_log.py의 TOP_N과 동일), include_news=true면 그 N개에 한해 당일
    뉴스 건수도 채운다(종목당 API 호출 1번이라 비용이 커 top_n 없이는 권장 안 함).
    """
    try:
        result = research_service.get_daily_snapshot(date, market, top_n=top_n, include_news=include_news)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    if result is None:
        raise HTTPException(status_code=404, detail="해당 날짜에 거래 데이터가 없습니다 (휴장일일 수 있음)")
    return result
