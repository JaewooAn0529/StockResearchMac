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
    except research_service.UpstreamFetchError as exc:
        # 휴장일(404)과는 다르다 — KRX 쪽 요청 실패(주로 과도한 연속호출로 인한
        # 제한)라 호출자가 잠시 쉬었다 재시도해야 한다. 백필 스크립트가 이걸
        # "휴장일"로 착각해 조용히 건너뛰면 데이터가 빠진 채로 완성된 것처럼
        # 보이므로 반드시 구분되는 상태코드로 알려야 한다.
        raise HTTPException(
            status_code=503,
            detail=f"KRX 응답 실패 (요청 제한 가능성) — 잠시 후 재시도하세요: {exc}",
        )

    if result is None:
        raise HTTPException(status_code=404, detail="해당 날짜에 거래 데이터가 없습니다 (휴장일일 수 있음)")
    return result
