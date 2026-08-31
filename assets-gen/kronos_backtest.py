"""Kronos(K-line 예측 모델)를 한국 주식에 zero-shot으로 써도 되는지 실측한다.

⚠️ 이건 도입 결정을 위한 검증이지, 앱에 넣기로 한 게 아니다. Kronos는 미래
가격을 숫자로 예측하는 모델이라 지금 앱이 지켜온 "사실 계산/과거 조회" 원칙과
충돌한다. 최소한 "이 모델이 한국 주식에서 실제로 맞기는 하는지"는 확인하고
판단해야 한다.

방법: 과거 시점을 잘라서 그 이전 데이터만 모델에 주고, 이후 N일을 예측시킨 뒤
실제 값과 대조한다(lookahead 없음). 단순 비교군으로 "마지막 종가가 그대로
유지된다"(naive/persistence)를 같이 계산한다 — 예측 모델이 이것보다 못하면
쓸 이유가 없다.
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

TICKER = "005930"  # 삼성전자
LOOKBACK = 90      # 정규화 구간이 길면 추세 때문에 예측이 구간평균으로 끌려간다(실측)
PRED_LEN = 5       # 예측할 일수


def main():
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"device: {device}", flush=True)

    df = stock.get_market_ohlcv("20200101", "20260811", TICKER)
    if df is None or df.empty:
        print("데이터 조회 실패")
        return
    print(f"전체 데이터: {len(df)}행", flush=True)

    # Kronos가 기대하는 컬럼명으로 변환
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

    # 최근 3개 시점에서 각각 백테스트 (한 번만 하면 운으로 맞을 수 있다)
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
        # 방향(오름/내림)을 맞췄는지 — 가격 수치보다 이게 실용적으로 중요하다
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
