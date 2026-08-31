"""Technical indicators (indicator #3): moving-average disparity, volume spikes, RSI/MACD/Bollinger Bands.

We call pykrx separately here because we need the raw OHLCV DataFrame (for
rolling calculations), not the cleaned-up list that price.py returns.

RSI/MACD/Bollinger Bands are standard indicators offered by platforms like
OpenBB, but since we can compute them directly from the OHLCV data we already
have, we didn't add that dependency (OpenBB is AGPLv3, which doesn't fit our
license, and it doesn't cover Korean stocks anyway).

These values are a computed snapshot of "this is the current state," not a
prediction of future direction — they're presented to the user that way too.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pandas as pd
from pykrx import stock

KST = timezone(timedelta(hours=9))


def _rsi(close: pd.Series, period: int = 14) -> float | None:
    """Wilder RSI. Ranges 0-100; conventionally, above 70 is considered overbought and below 30 oversold."""
    if len(close) < period + 1:
        return None
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    # Wilder smoothing (alpha=1/period) — closer to the standard implementation than a simple average
    avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean().iloc[-1]
    avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean().iloc[-1]
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(float(100 - (100 / (1 + rs))), 2)


def _macd(close: pd.Series) -> tuple[float | None, float | None, float | None]:
    """MACD(12,26,9) -> (macd, signal, histogram)."""
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
    """Bollinger Bands(20, 2sigma) -> (upper, middle, lower, %B).

    %B is the current position within the band (0 = lower, 1 = upper). Undefined if the band width is 0.
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
        return None  # need at least 60 trading days to compute MA60

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
