from fastapi import APIRouter, HTTPException, Query
from pykrx import stock as krx

from app.models.schemas import (
    ConsensusResponse,
    EarningsCalendarResponse,
    FlowsResponse,
    NewsResponse,
    PeerComparisonResponse,
    PriceResponse,
    RecoveryHistoryResponse,
    RiskFlagsResponse,
    RsiSignalStatsResponse,
    SearchResult,
    TechnicalResponse,
    ValuationResponse,
    VolatilityResponse,
)
from app.services import consensus as consensus_service
from app.services import dart as dart_service
from app.services import flows as flows_service
from app.services import historical_pattern as historical_pattern_service
from app.services import news as news_service
from app.services import peers as peers_service
from app.services import price as price_service
from app.services import signal_stats as signal_stats_service
from app.services import technical as technical_service
from app.services import universe
from app.services import valuation as valuation_service
from app.services import volatility as volatility_service

router = APIRouter(prefix="/stocks", tags=["stocks"])


@router.get("/search", response_model=list[SearchResult])
def search_stocks(q: str = Query(..., min_length=1)):
    return universe.search(q)


@router.get("/{ticker}/price", response_model=PriceResponse)
def get_price(ticker: str):
    data = price_service.get_price_and_chart(ticker)
    if data is None:
        raise HTTPException(status_code=404, detail=f"시세 데이터를 찾을 수 없습니다: {ticker}")
    name = krx.get_market_ticker_name(ticker)
    return PriceResponse(ticker=ticker, name=name, **data)


@router.get("/{ticker}/flows", response_model=FlowsResponse)
def get_flows(ticker: str):
    series = flows_service.get_flows(ticker)
    if series is None:
        raise HTTPException(status_code=404, detail=f"수급 데이터를 찾을 수 없습니다: {ticker}")
    name = krx.get_market_ticker_name(ticker)
    return FlowsResponse(ticker=ticker, name=name, series=series)


@router.get("/{ticker}/valuation", response_model=ValuationResponse)
def get_valuation(ticker: str):
    data = valuation_service.get_valuation(ticker)
    if data is None:
        raise HTTPException(status_code=404, detail=f"밸류에이션 데이터를 찾을 수 없습니다: {ticker}")
    name = krx.get_market_ticker_name(ticker)
    return ValuationResponse(ticker=ticker, name=name, **data)


@router.get("/{ticker}/consensus", response_model=ConsensusResponse)
def get_consensus(ticker: str):
    data = consensus_service.get_consensus(ticker)
    if data is None:
        raise HTTPException(
            status_code=404,
            detail=f"컨센서스 데이터가 없습니다(추정 증권사 3곳 미만이거나 커버리지 없음): {ticker}",
        )
    name = krx.get_market_ticker_name(ticker)
    return ConsensusResponse(ticker=ticker, name=name, **data)


@router.get("/{ticker}/technical", response_model=TechnicalResponse)
def get_technical(ticker: str):
    data = technical_service.get_technical(ticker)
    if data is None:
        raise HTTPException(status_code=404, detail=f"기술적 지표 데이터를 찾을 수 없습니다: {ticker}")
    name = krx.get_market_ticker_name(ticker)
    return TechnicalResponse(ticker=ticker, name=name, **data)


@router.get("/{ticker}/volatility", response_model=VolatilityResponse)
def get_volatility(ticker: str):
    data = volatility_service.get_volatility_beta(ticker)
    if data is None:
        raise HTTPException(status_code=404, detail=f"변동성/베타 데이터를 찾을 수 없습니다: {ticker}")
    name = krx.get_market_ticker_name(ticker)
    return VolatilityResponse(ticker=ticker, name=name, **data)


@router.get("/{ticker}/peers", response_model=PeerComparisonResponse)
def get_peers(ticker: str):
    data = peers_service.get_peer_comparison(ticker)
    if data is None:
        raise HTTPException(status_code=404, detail=f"동종업계 비교 데이터를 찾을 수 없습니다: {ticker}")
    name = krx.get_market_ticker_name(ticker)
    return PeerComparisonResponse(ticker=ticker, name=name, **data)


@router.get("/{ticker}/earnings-calendar", response_model=EarningsCalendarResponse)
def get_earnings_calendar(ticker: str):
    data = dart_service.get_earnings_calendar(ticker)
    if data is None:
        raise HTTPException(status_code=404, detail=f"실적발표 캘린더 데이터를 찾을 수 없습니다: {ticker}")
    name = krx.get_market_ticker_name(ticker)
    return EarningsCalendarResponse(ticker=ticker, name=name, **data)


@router.get("/{ticker}/risk-flags", response_model=RiskFlagsResponse)
def get_risk_flags(ticker: str):
    flags = dart_service.get_risk_flags(ticker)
    if flags is None:
        raise HTTPException(status_code=404, detail=f"리스크 체크리스트 데이터를 찾을 수 없습니다: {ticker}")
    name = krx.get_market_ticker_name(ticker)
    return RiskFlagsResponse(ticker=ticker, name=name, flags=flags)


@router.get("/{ticker}/news", response_model=NewsResponse)
def get_news(ticker: str):
    name = krx.get_market_ticker_name(ticker)
    articles = news_service.get_news(name)
    return NewsResponse(ticker=ticker, name=name, articles=articles)


@router.get("/{ticker}/recovery-history", response_model=RecoveryHistoryResponse)
def get_recovery_history(ticker: str, buy_price: float = Query(..., gt=0)):
    data = historical_pattern_service.get_recovery_history(ticker, buy_price)
    if data is None:
        raise HTTPException(status_code=404, detail=f"과거 데이터를 찾을 수 없습니다: {ticker}")
    name = krx.get_market_ticker_name(ticker)
    return RecoveryHistoryResponse(ticker=ticker, name=name, **data)


@router.get("/{ticker}/rsi-signal-stats", response_model=RsiSignalStatsResponse)
def get_rsi_signal_stats(ticker: str):
    data = signal_stats_service.get_rsi_signal_stats(ticker)
    if data is None:
        raise HTTPException(status_code=404, detail=f"RSI 신호 통계 데이터를 찾을 수 없습니다: {ticker}")
    name = krx.get_market_ticker_name(ticker)
    return RsiSignalStatsResponse(ticker=ticker, name=name, **data)
