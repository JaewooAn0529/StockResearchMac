"""기술적 지표 (지표 #3): 이동평균 이격도, 거래량 급증, RSI/MACD/볼린저밴드.

price.py가 반환하는 정제된 리스트가 아니라 원본 OHLCV DataFrame이 필요해서
(rolling 계산용) 여기서 별도로 pykrx를 호출한다.

RSI/MACD/볼린저밴드는 OpenBB 같은 플랫폼이 제공하는 표준 지표인데, 우리가
이미 들고 있는 OHLCV로 직접 계산할 수 있어서 의존성을 추가하지 않았다
(OpenBB는 AGPLv3라 라이선스도 맞지 않고 한국 주식도 커버하지 않는다).

이 값들은 "지금 이 상태다"라는 계산 결과지, 앞으로 오른다/내린다는 예측이
아니다 — 화면에서도 그렇게만 표시한다.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pandas as pd
from pykrx import stock

KST = timezone(timedelta(hours=9))


def _rsi(close: pd.Series, period: int = 14) -> float | None:
    """Wilder RSI. 0~100이고 통상 70↑ 과매수, 30↓ 과매도 구간으로 본다."""
    if len(close) < period + 1:
        return None
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    # Wilder 평활(alpha=1/period). 단순평균보다 표준 구현에 가깝다
    avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean().iloc[-1]
    avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean().iloc[-1]
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(float(100 - (100 / (1 + rs))), 2)


def _macd(close: pd.Series) -> tuple[float | None, float | None, float | None]:
    """MACD(12,26,9) → (macd, signal, histogram)."""
    if len(close) < 35:
        return None, None, None
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    hist = macd_line - signal_line
    return (
        round(float(macd_line.iloc[-1]), 2),
        round(float(signal_line.iloc[-1]), 2),
        round(float(hist.iloc[-1]), 2),
    )


def _bollinger(close: pd.Series, period: int = 20, num_std: float = 2.0):
    """볼린저밴드(20, 2σ) → (upper, middle, lower, %B).

    %B는 밴드 내 현재 위치(0=하단, 1=상단). 밴드 폭이 0이면 정의되지 않는다.
    """
    if len(close) < period:
        return None, None, None, None
    middle = close.rolling(period).mean().iloc[-1]
    std = close.rolling(period).std().iloc[-1]
    if pd.isna(middle) or pd.isna(std):
        return None, None, None, None
    upper = middle + num_std * std
    lower = middle - num_std * std
    latest = float(close.iloc[-1])
    pct_b = (latest - lower) / (upper - lower) if upper != lower else None
    return (
        round(float(upper), 2),
        round(float(middle), 2),
        round(float(lower), 2),
        round(float(pct_b), 3) if pct_b is not None else None,
    )


def get_technical(ticker: str, days: int = 250) -> dict | None:
    end = datetime.now(KST)
    start = end - timedelta(days=days)
    df = stock.get_market_ohlcv(start.strftime("%Y%m%d"), end.strftime("%Y%m%d"), ticker)
    if df is None or df.empty or len(df) < 60:
        return None  # MA60 계산에 최소 60거래일 필요

    close = df["종가"]
    volume = df["거래량"]
    ma20 = close.rolling(20).mean().iloc[-1]
    ma60 = close.rolling(60).mean().iloc[-1]
    latest_close = int(close.iloc[-1])
    today_volume = int(volume.iloc[-1])
    avg_volume_20 = volume.iloc[-21:-1].mean() if len(volume) >= 21 else None

    macd, macd_signal, macd_hist = _macd(close)
    bb_upper, bb_middle, bb_lower, bb_pct_b = _bollinger(close)

    return {
        "as_of_date": df.index[-1].strftime("%Y-%m-%d"),
        "close": latest_close,
        "ma20": round(float(ma20), 2) if pd.notna(ma20) else None,
        "ma60": round(float(ma60), 2) if pd.notna(ma60) else None,
        "disparity_20": round(latest_close / ma20 * 100, 2) if pd.notna(ma20) else None,
        "disparity_60": round(latest_close / ma60 * 100, 2) if pd.notna(ma60) else None,
        "volume": today_volume,
        "avg_volume_20": int(avg_volume_20) if avg_volume_20 else None,
        "volume_ratio": round(today_volume / avg_volume_20, 2) if avg_volume_20 else None,
        "rsi_14": _rsi(close),
        "macd": macd,
        "macd_signal": macd_signal,
        "macd_histogram": macd_hist,
        "bb_upper": bb_upper,
        "bb_middle": bb_middle,
        "bb_lower": bb_lower,
        "bb_percent_b": bb_pct_b,
    }
