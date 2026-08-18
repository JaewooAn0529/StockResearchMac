"""DART 공시 기반 지표 두 가지.

1. 실적발표 캘린더 (지표 #7): DART는 "다음 실적발표일"을 직접 알려주지 않는다.
   대신 company.json의 결산월(acc_mt)로 자본시장법상 정기공시 법정 제출기한을
   계산한다 — 분기/반기보고서는 분기 종료 후 45일, 사업보고서는 사업연도 종료
   후 90일 이내. 그래서 이건 "회사가 발표하겠다고 예고한 날짜"가 아니라
   "법으로 정해진 마감일 추정치"라는 걸 응답에 명확히 표시한다.

2. 리스크 체크리스트 (지표 #8): 최근 공시목록 제목에서 보호예수·대량보유·
   최대주주 관련 키워드를 찾아 배지로 노출한다. DART의 세부 공시유형 코드를
   완벽히 분류하기보다, 실제 공시 제목을 그대로 보여주고 원문 링크를 붙여서
   사용자가 직접 확인하게 하는 쪽이 더 정직하다.
"""

from __future__ import annotations

import calendar
from datetime import date, timedelta

import requests

from app.core.config import DART_API_KEY
from app.services.dart_codes import get_corp_code

_COMPANY_URL = "https://opendart.fss.or.kr/api/company.json"
_LIST_URL = "https://opendart.fss.or.kr/api/list.json"

# "특정증권등소유상황보고서"(임원·주요주주 지분 변동)와 단순 "최대주주"는 일상적으로도
# 자주 나와서 넣으면 경고가 아니라 소음이 된다(삼성전자 기준 180일에 91건). 실제로
# "위험 신호"라고 부를 만한 보호예수/의무보유 해제와 대량(5%+) 지분 변동만 남긴다.
_RISK_KEYWORDS = ["보호예수", "의무보유", "대량보유상황보고서"]


def _month_end(year: int, month: int) -> date:
    return date(year, month, calendar.monthrange(year, month)[1])


def _milestones(fy_start: date) -> list[tuple[str, date, int]]:
    """(공시유형, 분기/사업연도 종료일, 제출기한 일수) 목록."""
    out = []
    for offset, (label, deadline_days) in {
        3: ("1분기보고서", 45),
        6: ("반기보고서", 45),
        9: ("3분기보고서", 45),
        12: ("사업보고서", 90),
    }.items():
        idx = fy_start.month - 2 + offset
        year = fy_start.year + idx // 12
        month = idx % 12 + 1
        period_end = _month_end(year, month)
        out.append((label, period_end, deadline_days))
    return out


def get_earnings_calendar(ticker: str, today: date | None = None) -> dict | None:
    corp_code = get_corp_code(ticker)
    if not corp_code:
        return None

    res = requests.get(_COMPANY_URL, params={"crtfc_key": DART_API_KEY, "corp_code": corp_code}, timeout=10)
    res.raise_for_status()
    body = res.json()
    if body.get("status") != "000":
        return None

    acc_mt = int(body["acc_mt"])  # 결산월 (예: 12)
    fy_start_month = acc_mt % 12 + 1
    today = today or date.today()

    candidates = []
    for cycle_year in (today.year - 1, today.year, today.year + 1):
        fy_start = date(cycle_year, fy_start_month, 1)
        for label, period_end, deadline_days in _milestones(fy_start):
            deadline = period_end + timedelta(days=deadline_days)
            if deadline >= today:
                candidates.append((deadline, label))

    if not candidates:
        return None
    deadline, label = min(candidates)

    return {
        "report_type": label,
        "deadline_date": deadline.strftime("%Y-%m-%d"),
        "d_day": (deadline - today).days,
        "note": "회사가 예고한 실적발표일이 아니라 자본시장법상 정기공시 법정 제출기한 추정치입니다.",
    }


def get_risk_flags(ticker: str, lookback_days: int = 180) -> list[dict] | None:
    corp_code = get_corp_code(ticker)
    if not corp_code:
        return None

    today = date.today()
    res = requests.get(
        _LIST_URL,
        params={
            "crtfc_key": DART_API_KEY,
            "corp_code": corp_code,
            "bgn_de": (today - timedelta(days=lookback_days)).strftime("%Y%m%d"),
            "end_de": today.strftime("%Y%m%d"),
            "page_count": 100,
        },
        timeout=10,
    )
    res.raise_for_status()
    body = res.json()
    if body.get("status") not in ("000", "013"):  # 013 = 조회된 데이터 없음(정상)
        return None

    flags = []
    for item in body.get("list", []):
        title = item.get("report_nm", "")
        matched = [kw for kw in _RISK_KEYWORDS if kw in title]
        if not matched:
            continue
        flags.append({
            "title": title,
            "date": item.get("rcept_dt", ""),
            "matched_keyword": matched[0],
            "url": f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={item.get('rcept_no', '')}",
        })
    return flags
