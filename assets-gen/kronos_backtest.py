"""Empirically tests whether Kronos (a K-line forecasting model) can be used
zero-shot on Korean stocks.

⚠️ This is validation for an adoption decision, not a commitment to add it to the
app. Kronos predicts future prices as numbers, which conflicts with the
"fact-based calculation / historical lookup only" principle the app has followed
so far. At minimum, we need to verify whether this model is actually accurate on
Korean stocks before deciding.

Method: cut history off at a past point in time, feed the model only the data
before that cutoff, have it predict the next N days, then compare against the
actual values (no lookahead). As a simple baseline, we also compute "the last
close price stays the same" (naive/persistence) — if the prediction model does
worse than this, there's no reason to use it.
"""

import sys
import time

import pandas as pd
import torch

sys.path.append("/private/tmp/claude-501/-Users-jaewooan-AIstocktrading/2973cf70-02b3-419a-9f35-40c105fe99b4/scratchpad/Kronos")

from dotenv import load_dotenv

load_dotenv("/Users/jaewooan/AIstocktrading/stock-research-app/backend/.env")

from model import Kronos, KronosPredictor, KronosTokenizer  # noqa: E402
from pykrx import stock  # noqa: E402

TICKER = "005930"  # Samsung Electronics
LOOKBACK = 90      # If the normalization window is too long, the trend pulls the prediction toward the window average (measured)
PRED_LEN = 5       # Number of days to predict


def main():
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"device: {device}", flush=True)

    df = stock.get_market_ohlcv("20200101", "20260811", TICKER)
    if df is None or df.empty:
        print("데이터 조회 실패")
        return
    print(f"전체 데이터: {len(df)}행", flush=True)

    # Convert to the column names Kronos expects
    k = pd.DataFrame({
        "open": df["시가"].astype(float),
        "high": df["고가"].astype(float),
        "low": df["저가"].astype(float),
        "close": df["종가"].astype(float),
        "volume": df["거래량"].astype(float),
        "amount": (df["종가"] * df["거래량"]).astype(float),
    })
    k.index = pd.to_datetime(df.index)

    t0 = time.time()
    tokenizer = KronosTokenizer.from_pretrained("NeoQuasar/Kronos-Tokenizer-base")
    model = Kronos.from_pretrained("NeoQuasar/Kronos-small")
    predictor = KronosPredictor(model, tokenizer, device=device, max_context=512)
    print(f"모델 로드: {time.time() - t0:.1f}초", flush=True)

    # Backtest at 3 recent points in time separately (a single run could get lucky)
    results = []
    for offset in (60, 40, 20):
        cut = len(k) - offset
        hist = k.iloc[cut - LOOKBACK:cut]
        actual = k.iloc[cut:cut + PRED_LEN]
        if len(actual) < PRED_LEN:
            continue

        t1 = time.time()
        pred = predictor.predict(
            df=hist[["open", "high", "low", "close", "volume", "amount"]],
            x_timestamp=hist.index.to_series(),
            y_timestamp=actual.index.to_series(),
            pred_len=PRED_LEN,
            T=1.0, top_p=0.9, sample_count=1,
        )
        elapsed = time.time() - t1

        last_close = float(hist["close"].iloc[-1])
        pred_close = float(pred["close"].iloc[-1])
        real_close = float(actual["close"].iloc[-1])

        pred_err = abs(pred_close - real_close) / real_close * 100
        naive_err = abs(last_close - real_close) / real_close * 100
        # Whether the direction (up/down) was correct — more practically important than the exact price
        pred_dir = "상승" if pred_close > last_close else "하락"
        real_dir = "상승" if real_close > last_close else "하락"

        results.append((pred_err, naive_err, pred_dir == real_dir))
        print(
            f"[{actual.index[0].date()}~{actual.index[-1].date()}] "
            f"기준 {last_close:,.0f} → 실제 {real_close:,.0f} / 예측 {pred_close:,.0f}\n"
            f"    예측오차 {pred_err:.2f}% vs 단순유지오차 {naive_err:.2f}% | "
            f"방향 {pred_dir}(실제 {real_dir}) {'O' if pred_dir == real_dir else 'X'} | {elapsed:.1f}초",
            flush=True,
        )

    if results:
        avg_pred = sum(r[0] for r in results) / len(results)
        avg_naive = sum(r[1] for r in results) / len(results)
        hits = sum(1 for r in results if r[2])
        print(f"\n=== 요약 ({len(results)}회) ===", flush=True)
        print(f"평균 예측오차 {avg_pred:.2f}% / 단순유지 {avg_naive:.2f}%", flush=True)
        print(f"방향 적중 {hits}/{len(results)}", flush=True)
        print(
            "판정: " + ("단순유지보다 나음" if avg_pred < avg_naive else "단순유지보다 못함 — 도입 근거 약함"),
            flush=True,
        )


if __name__ == "__main__":
    main()
