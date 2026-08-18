from fastapi import APIRouter, HTTPException

from app.agents.client import AgentRefusal
from app.agents.orchestrator import run_analysis
from app.models.schemas import DebateAnalysisResponse, DecisionHistoryResponse
from app.services import eval_log

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("/{ticker}/debate", response_model=DebateAnalysisResponse)
def debate(ticker: str):
    """멀티에이전트 토론 분석. 모델 호출이 여러 번 일어나 응답까지 수십 초 걸린다."""
    try:
        result = run_analysis(ticker)
    except AgentRefusal as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    # 나중에 되돌아볼 수 있게 판단을 남긴다(기록 실패가 응답을 막지는 않는다)
    eval_log.record_decision(result)
    return result


@router.get("/history", response_model=DecisionHistoryResponse)
def decision_history(limit: int = 30):
    """지난 판단들과 그 이후 실제 주가 변화.

    ⚠️ 예측 성능 보장이 아니라 "그때 이렇게 판단했고 이후 이렇게 움직였다"는
    사후 기록 조회다.
    """
    return DecisionHistoryResponse(records=eval_log.get_history(limit))
