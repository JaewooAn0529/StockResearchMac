"""원본 데이터를 프롬프트에 넣을 수 있게 압축한다.

62거래일치 OHLCV와 수급 시계열을 그대로 넣으면 토큰만 먹고 모델이 읽지도
않는다. 에이전트가 실제로 판단에 쓰는 집계값만 남긴다.
"""

from __future__ import annotations


def _man(won: float) -> str:
    """원 단위 금액을 억 단위로. 수급 금액이 조 단위까지 가서 그대로 두면 읽기 어렵다."""
    return f"{won / 1e8:,.0f}억"


def format_price(price: dict | None) -> str:
    if not price:
        return "시세 데이터 없음"
    ohlcv = price["ohlcv"]
    closes = [p["close"] for p in ohlcv]
    recent = ohlcv[-20:]
    lines = [
        f"현재가 {price['current_price']:,}원 ({price['change_pct']:+.2f}%, {price['as_of_date']} 기준)",
        f"조회기간({len(ohlcv)}거래일) 최고 {max(closes):,}원 / 최저 {min(closes):,}원",
        "최근 20거래일 종가:",
    ]
    lines += [f"  {p['date']} {p['close']:,}원 (거래량 {p['volume']:,})" for p in recent]
    return "\n".join(lines)


def format_flows(flows: list[dict] | None) -> str:
    if not flows:
        return "수급 데이터 없음"

    def cum(days: int, key: str) -> float:
        return sum(p[key] for p in flows[-days:])

    lines = ["외국인/기관 누적 순매수 (양수=순매수, 음수=순매도):"]
    for days in (5, 20, 60):
        if len(flows) >= days:
            lines.append(
                f"  최근 {days}거래일: 외국인 {_man(cum(days, 'foreign_net_buy'))}, "
                f"기관 {_man(cum(days, 'institution_net_buy'))}"
            )
    lines.append("일자별 최근 10거래일:")
    for p in flows[-10:]:
        lines.append(
            f"  {p['date']} 외국인 {_man(p['foreign_net_buy'])} / 기관 {_man(p['institution_net_buy'])}"
        )
    return "\n".join(lines)


def format_valuation(v: dict | None) -> str:
    if not v:
        return "밸류에이션 데이터 없음"
    return "\n".join([
        f"현재 PER {v['per']} / PBR {v['pbr']} ({v['as_of_date']} 기준)",
        f"최근 1년 PER 밴드: 최저 {v['per_min_1y']} / 중앙 {v['per_median_1y']} / 최고 {v['per_max_1y']}",
        f"최근 1년 PBR 밴드: 최저 {v['pbr_min_1y']} / 중앙 {v['pbr_median_1y']} / 최고 {v['pbr_max_1y']}",
    ])


def format_consensus(c: dict | None, current_price: int | None) -> str:
    if not c:
        return "증권사 컨센서스 없음 (커버리지 부족)"
    line = f"증권사 컨센서스 투자의견 {c['opinion_score']} ({c['opinion_text']}), 목표주가 {c['target_price']:,}원"
    if current_price:
        gap = (c["target_price"] - current_price) / current_price * 100
        line += f" — 현재가 대비 {gap:+.1f}%"
    return f"{line}\n출처: {c['source']} (자체 분석이 아니라 인용 데이터)"


def format_technical(t: dict | None) -> str:
    if not t:
        return "기술적 지표 데이터 없음"
    lines = [
        f"종가 {t['close']:,}원 (기준일 {t['as_of_date']})",
        f"20일 이동평균 {t['ma20']:,.0f}원 / 이격도 {t['disparity_20']}%",
        f"60일 이동평균 {t['ma60']:,.0f}원 / 이격도 {t['disparity_60']}%",
        f"당일 거래량 {t['volume']:,} / 20일 평균 대비 {t['volume_ratio']}배",
    ]
    # 표준 지표는 값이 있을 때만 넣는다(표본이 짧으면 None)
    if t.get("rsi_14") is not None:
        lines.append(f"RSI(14) {t['rsi_14']} (통상 70↑ 과매수 / 30↓ 과매도 구간으로 해석)")
    if t.get("macd") is not None:
        lines.append(
            f"MACD {t['macd']} / 시그널 {t['macd_signal']} / 히스토그램 {t['macd_histogram']}"
        )
    if t.get("bb_upper") is not None:
        lines.append(
            f"볼린저밴드 상단 {t['bb_upper']:,.0f} / 중심 {t['bb_middle']:,.0f} / "
            f"하단 {t['bb_lower']:,.0f} / %B {t['bb_percent_b']}"
        )
    return "\n".join(lines)


def format_volatility(v: dict | None) -> str:
    if not v:
        return "변동성 데이터 없음"
    return (
        f"베타 {v['beta']} ({v['benchmark']} 지수 대비, {v['window_days']}거래일 표본) / "
        f"연율화 변동성 {v['annualized_volatility_pct']}%"
    )


def format_peers(p: dict | None) -> str:
    if not p:
        return "동종업계 비교 데이터 없음"
    lines = [f"업종: {p['industry']}"]
    lines += [f"  {r['name']}({r['ticker']}) PER {r['per']} / PBR {r['pbr']}" for r in p["peers"]]
    return "\n".join(lines)


def format_news(news: list[dict] | None) -> str:
    if not news:
        return "수집된 뉴스 없음 (네이버 API 키 미설정이거나 관련 기사 없음)"
    return "\n".join(
        f"[{n['published_at']}] {n['title']}\n  {n['description']}" for n in news
    )
