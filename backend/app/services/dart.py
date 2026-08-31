"""Two indicators based on DART disclosures.

1. Earnings calendar (indicator #7): DART doesn't directly tell you the "next
   earnings date." Instead, we use the fiscal year-end month (acc_mt) from
   company.json to compute the statutory filing deadline for periodic
   disclosures under the Capital Markets Act — quarterly/semiannual reports
   are due within 45 days of the period end, and the annual report within 90
   days of the fiscal year end. So the response makes clear that this is not
   "the date the company announced it will report," but an "estimated
   legally mandated deadline."

2. Risk checklist (indicator #8): scans recent disclosure titles for keywords
   related to lock-ups, large shareholding reports, and major shareholders,
   and surfaces them as badges. Rather than trying to perfectly classify
   DART's detailed disclosure-type codes, it's more honest to just show the
   actual disclosure titles as-is with a link to the source, and let the
   user verify for themselves.
"""

from __future__ import annotations

import calendar
from datetime import date, timedelta

import requests

from app.core.config import DART_API_KEY
from app.services.dart_codes import get_corp_code

_COMPANY_URL = "https://opendart.fss.or.kr/api/company.json"
_LIST_URL = "https://opendart.fss.or.kr/api/list.json"

# "Report on Status of Specific Securities Ownership" (changes in executive/major
# shareholder stakes) and a plain "major shareholder" mention show up so routinely
# that including them would be noise rather than a warning (91 filings in 180 days
# for Samsung Electronics alone). We keep only things actually worth calling a
# "risk signal": lock-up/mandatory-holding releases and large (5%+) stake changes.
_RISK_KEYWORDS = ["보호예수", "의무보유", "대량보유상황보고서"]


def _month_end(year: int, month: int) -> date:
    return date(year, month, calendar.monthrange(year, month)[1])


def _milestones(fy_start: date) -> list[tuple[str, date, int]]:
    """List of (disclosure type, quarter/fiscal-year end date, days until filing deadline)."""
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

    acc_mt = int(body["acc_mt"])  # fiscal year-end month (e.g. 12)
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
    if body.get("status") not in ("000", "013"):  # 013 = no data found (normal)
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
