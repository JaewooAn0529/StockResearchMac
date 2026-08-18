"""과거 유사 하락→회복 패턴 조회.

⚠️ 이건 미래 예측이 아니라 순수 과거 통계 조회다. "다음에도 며칠 걸릴
것이다" 같은 미래 단정 표현은 여기서도, 이 데이터를 쓰는 macOS 앱에서도
금지 — summary 필드에 넣는 문장은 반드시 "역사적으로는~", "과거 사례를
보면~" 같은 과거형·참고형으로만 쓴다. 표본이 2건 미만이면 통계 자체를
내보내지 않는다(sufficient_sample=False).

알고리즘:
1. 종가 시계열의 "직전 런닝하이(그 시점까지의 최고가)" 대비 낙폭을 매일 계산
2. 사용자의 현재 낙폭(매수가 대비)과 비슷한 낙폭(허용오차 이내)이 나타났던
   과거 구간을 찾는다 — 연속된 매칭일은 하나의 에피소드로 묶어서(같은
   하락의 여러 날을 중복 카운트하지 않으려고) 에피소드 시작일만 표본으로 쓴다
3. 각 에피소드 시작일 이후 종가가 그 시점 런닝하이를 다시 넘어선 날까지의
   일수를 "회복 소요일수"로 기록한다. 회복 못 하고 데이터가 끝난 에피소드는
   평균 계산에서 뺀다(끝까지 회복 안 했다고 단정할 수 없는 미완결 사례라서).
"""

from __future__ import annotations

import statistics
from datetime import date

from pykrx import stock

_TOLERANCE_PCT = 4.0  # 낙폭이 이 범위 안이면 "비슷한 낙폭"으로 본다
_MIN_SAMPLE = 2


def get_recovery_history(ticker: str, buy_price: float) -> dict | None:
    df = stock.get_market_ohlcv("20000101", date.today().strftime("%Y%m%d"), ticker)
    if df is None or df.empty or len(df) < 30:
        return None

    closes = df["종가"]
    current_price = float(closes.iloc[-1])
    current_return_pct = (current_price - buy_price) / buy_price * 100

    if current_return_pct >= 0:
        return {
            "current_price": int(current_price),
            "current_return_pct": round(current_return_pct, 2),
            "applicable": False,
            "sufficient_sample": False,
            "sample_count": 0,
            "unresolved_count": 0,
            "avg_recovery_days": None,
            "median_recovery_days": None,
            "summary": "현재 매수가보다 높거나 같아 하락 회복 히스토리가 해당하지 않습니다.",
        }

    running_max = closes.cummax()
    drawdown_pct = (closes - running_max) / running_max * 100

    lower, upper = current_return_pct - _TOLERANCE_PCT, current_return_pct + _TOLERANCE_PCT
    is_match = (drawdown_pct >= lower) & (drawdown_pct <= upper)

    # 연속된 매칭일을 하나의 에피소드로 묶고 시작일 인덱스만 취한다. 여기서
    # 그치면 하나의 긴 하락이 허용오차 경계를 며칠 간격으로 들락날락할 때마다
    # 별개 사례로 중복 집계된다(실측 확인됨) — 그래서 직전 에피소드 시작일과
    # 60일 이내로 붙어 있으면 같은 사례로 보고 병합한다.
    _MERGE_GAP_DAYS = 60
    raw_starts: list[int] = []
    in_episode = False
    for i, matched in enumerate(is_match):
        if matched and not in_episode:
            raw_starts.append(i)
            in_episode = True
        elif not matched:
            in_episode = False

    episode_starts: list[int] = []
    for idx in raw_starts:
        if episode_starts and (closes.index[idx] - closes.index[episode_starts[-1]]).days <= _MERGE_GAP_DAYS:
            continue  # 직전 사례와 같은 하락 구간으로 취급 — 새 표본으로 안 셈
        episode_starts.append(idx)

    recovery_days: list[int] = []
    for start_idx in episode_starts:
        peak_price = running_max.iloc[start_idx]
        future = closes.iloc[start_idx + 1:]
        recovered = future[future >= peak_price]
        if not recovered.empty:
            days = (recovered.index[0] - closes.index[start_idx]).days
            recovery_days.append(days)
        # else: 이 에피소드는 데이터 끝까지 회복 안 함 — 미완결이라 평균에서 제외

    sample_count = len(recovery_days)
    unresolved_count = len(episode_starts) - sample_count

    if sample_count < _MIN_SAMPLE:
        return {
            "current_price": int(current_price),
            "current_return_pct": round(current_return_pct, 2),
            "applicable": True,
            "sufficient_sample": False,
            "sample_count": sample_count,
            "unresolved_count": unresolved_count,
            "avg_recovery_days": None,
            "median_recovery_days": None,
            "summary": "참고할 만한 과거 사례가 충분하지 않습니다.",
        }

    avg_days = round(statistics.mean(recovery_days))
    median_days = round(statistics.median(recovery_days))

    return {
        "current_price": int(current_price),
        "current_return_pct": round(current_return_pct, 2),
        "applicable": True,
        "sufficient_sample": True,
        "sample_count": sample_count,
        "unresolved_count": unresolved_count,
        "avg_recovery_days": avg_days,
        "median_recovery_days": median_days,
        "summary": (
            f"역사적으로는 이 종목이 매수가 대비 비슷한 폭(약 {current_return_pct:.1f}%)만큼 "
            f"하락했다가 이전 고점을 회복하기까지 평균 {avg_days}일(중앙값 {median_days}일) "
            f"걸린 사례가 {sample_count}건 있었습니다."
        ),
    }
