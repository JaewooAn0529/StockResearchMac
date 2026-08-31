from fastapi import APIRouter, HTTPException

from app.agents.client import AgentRefusal
from app.agents.orchestrator import run_analysis
from app.models.schemas import DebateAnalysisResponse, DecisionHistoryResponse
from app.services import eval_log

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("/{ticker}/debate", response_model=DebateAnalysisResponse)
def debate(ticker: str):
    """Multi-agent debate analysis. Multiple model calls happen, so the response can take tens of seconds."""
    try:
        result = run_analysis(ticker)
    except AgentRefusal as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    # Records the decision for later review (a logging failure doesn't block the response)
    eval_log.record_decision(result)
    return result


@router.get("/history", response_model=DecisionHistoryResponse)
def decision_history(limit: int = 30):
    """Past decisions and how the actual stock price moved afterward.

    ⚠️ This is not a guarantee of predictive performance — it's a retrospective
    record lookup showing "this is what was decided then, and this is how the
    price moved afterward."
    """
    return DecisionHistoryResponse(records=eval_log.get_history(limit))
