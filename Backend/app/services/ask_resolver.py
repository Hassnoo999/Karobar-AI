"""Bounded intent/period guards for the five existing read-only ledger tools.

Recognized questions take the deterministic path. Only unrecognized financial
paraphrases reach the model, whose tool arguments are still validated here.
"""
from __future__ import annotations

import calendar
import re
import unicodedata
from datetime import date

from app.ai.base import ToolCall
from app.db import month_key, prev_month_key

MONTH_NAMES = {
    **{calendar.month_name[n].lower(): n for n in range(1, 13)},
    **{calendar.month_abbr[n].lower(): n for n in range(1, 13)},
    "sept": 9, "جنوری": 1, "فروری": 2, "مارچ": 3, "اپریل": 4,
    "مئی": 5, "جون": 6, "جولائی": 7, "اگست": 8, "ستمبر": 9,
    "اکتوبر": 10, "نومبر": 11, "دسمبر": 12,
}
MONTH_PATTERN = re.compile(r"(?<!\w)(" + "|".join(sorted(MONTH_NAMES, key=len, reverse=True)) + r")(?!\w)(?:\s+(\d{4}))?")
ROMAN = re.compile(r"\b(udhaar|udhar|kitna|kitni|qarz|baqaya|pichle|mahine|hai|bikri)\b")
DEBT = re.compile(r"\b(udhaar|udhar|qarz|baqaya|receivables?|outstanding|owes?|owed|debtor|dues?|balance)\b|ادھار|قرض|بقایا")
SALES = re.compile(r"\b(sales?|bikri|revenue|turnover)\b|فروخت|سیلز|بکری")
COMPARE = re.compile(r"\b(compare|comparison|farq|mukabl[ae]|versus|vs|difference)\b|موازنہ|مقابلہ|فرق")
TOP = re.compile(r"\b(top|most|highest|largest|biggest)\b|sab\s*se\s+(?:zyada|bara)|سب\s*سے\s*(?:زیادہ|بڑا)")
OTHER_RANK = re.compile(r"\b(best|lowest|least|smallest|rank|ranking|list)\b|sab\s*se\s*kam|سب\s*سے\s*کم")
UNSUPPORTED = re.compile(
    r"\b(expenses?|profit|cash\s+(?:balance|do\s+i\s+have|in\s+hand)|loan|eligible|eligibility|inventory|"
    r"stock|recover(?:ed|y)?|payments?|repayments?|reminder|send|delete|insert|update|ignore|pretend|"
    r"invent|forecast|predict|income|margin|kharch[a]?|munafa|salary|approval|interest|bank|account|savings)\b|"
    r"منافع|اخراجات|خرچ|قرضہ|اہلیت|یاددہانی|ادائیگی|تنخواہ"
)
DAILY = re.compile(r"\b(today|yesterday|daily|days?|hours?|week|weekly|quarter|yearly|annual|ytd|aaj|kal|parso|hafte)\b|year.to.date|آج|روزانہ|ہفت|سالانہ|کل\s+کی")
LAST_MONTH = re.compile(r"\b(?:last|previous)\s+month|\bpichl[ea]\s+(?:month|mahin[ea])|پچھل[ےا]\s*(?:ماہ|مہین[ےہ])|گزشتہ\s*(?:ماہ|مہین[ےہ])")
THIS_MONTH = re.compile(r"\b(?:this|current)\s+month|\b(?:is|iss)\s+(?:month|mahin[ea])|اس\s*(?:ماہ|مہین[ےہ])")


def normalized(question: str) -> str:
    text = unicodedata.normalize("NFKC", question).lower().replace("’", "'")
    text = text.translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789"))
    return " ".join(text.split())


def language(question: str) -> str:
    return "ur" if re.search(r"[\u0600-\u06ff]", question) else "roman" if ROMAN.search(normalized(question)) else "en"


def blocked(reason: str = "unsupported", *, clarify: bool = False) -> ToolCall:
    return ToolCall(provider="rules", tool="unsupported", args={"reason": reason, "clarify": clarify})


def periods(question: str, today: date) -> tuple[list[str], str | None]:
    """Resolve explicit periods, never silently substitute an invalid period."""
    q = normalized(question)
    if re.search(r"\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b", q):
        return [], "daily_period"
    months = []
    for year, month in re.findall(r"(?<!\d)(\d{4})[-/](\d{1,2})(?!\d)", q):
        if not 1 <= int(year) <= 9999 or not 1 <= int(month) <= 12:
            return [], "invalid_month"
        months.append(f"{int(year):04d}-{int(month):02d}")
    for match in MONTH_PATTERN.finditer(q):
        number = MONTH_NAMES[match.group(1)]
        year = int(match.group(2) or today.year)
        if not 1 <= year <= 9999:
            return [], "invalid_month"
        if not match.group(2) and number > today.month:
            return [], "specify_year"
        months.append(f"{year:04d}-{number:02d}")
    # Relative qualifiers alongside a named month refer to its predecessor;
    # "Compare August to the previous month" must not select today's month.
    if not months:
        if LAST_MONTH.search(q):
            months.append(prev_month_key(month_key(today)))
        if THIS_MONTH.search(q):
            months.append(month_key(today))
    if not months and re.search(r"\b\d{4}\b", q):
        return [], "specify_month"
    months = sorted(set(months))
    if any(month > month_key(today) for month in months):
        return [], "future_month"
    return months, None


def customer_name(question: str) -> str | None:
    q = normalized(question)
    patterns = [
        r"(?:how\s+much\s+)?does\s+(.+?)\s+owe(?:\s|\?|$)",
        r"(?:how\s+much\s+)?(.+?)\s+owes?\s+me(?:\s|\?|$)",
        r"^(.+?)\s+outstanding\s+balance(?:\s|\?|$)",
        r"^(.+?)\s+(?:ka|ki)\s+(?:udhaar|udhar|qarz|baqaya|balance)\b",
        r"^(.+?)\s+کا\s+(?:ادھار|قرض|بقایا)",
        r"(?:balance|udhaar|udhar|dues?)\s+(?:of|for)\s+(.+?)(?:\?|$)",
        r"^(.+?)['’]s\s+(?:balance|udhaar|udhar|dues?|outstanding)",
    ]
    for pattern in patterns:
        match = re.search(pattern, q)
        if match:
            name = match.group(1).strip(" ?.،")
            if name not in {"total", "kul", "sab", "sabka", "sabki", "mera", "mere", "my", "کل", "سب"} and not re.search(r"\b(and|aur|versus|vs)\b|\sاور\s", name):
                return name.title() if name.isascii() else name
    return None


def resolve_question(question: str, today: date) -> ToolCall | None:
    """None means a financial paraphrase may use the guarded model classifier."""
    q = normalized(question)
    debt, sales = bool(DEBT.search(q)), bool(SALES.search(q))
    if UNSUPPORTED.search(q):
        return blocked()
    if debt and sales:
        return blocked("one_question", clarify=True)
    if not debt and not sales:
        return blocked()
    if DAILY.search(q):
        return blocked("daily_period" if sales else "historical_balance")
    if re.search(r"\b(all.time|all\s+months|ever|lifetime|(?:\d+|two|three|six|twelve)\s+months)\b|تمام\s*مہین", q):
        return blocked("sales_scope" if sales else "historical_balance")
    months, period_error = periods(question, today)
    if period_error:
        return blocked(period_error, clarify=True)
    if debt:
        if months or re.search(r"\b(as\s+of|in\s+the\s+past|before|after)\b|پہلے", q):
            return blocked("historical_balance")
        if COMPARE.search(q):
            return blocked("customer_comparison")
        if OTHER_RANK.search(q):
            return blocked("customer_ranking")
        if TOP.search(q):
            return ToolCall(provider="rules", tool="top_debtor")
        name = customer_name(question)
        if name:
            return ToolCall(provider="rules", tool="customer_outstanding", args={"name": name})
        if re.search(r"\bbalance\b", q) and not re.search(r"\b(udhaar|udhar|qarz|outstanding|receivables?|dues?)\b", q):
            return blocked("missing_customer", clarify=True)
        if re.search(r"\b(total|all|overall|my|mera|mere|kul)\b|کل|مجموعی", q) or q.startswith("how much udhaar"):
            return ToolCall(provider="rules", tool="total_outstanding")
        if re.search(r"\b(he|she|his|her|us|iska|uska)\b|اس\s+کا", q):
            return blocked("missing_customer", clarify=True)
        return None
    if TOP.search(q) or OTHER_RANK.search(q) or re.search(r"\b(cash|credit|udhaar|udhar|only|sirf|exclude|sample|seed|average|mean|median|before|after|since|between)\b", q):
        return blocked("sales_scope")
    comparison = bool(COMPARE.search(q))
    if len(months) > 1 and (not comparison or len(months) != 2 or prev_month_key(months[-1]) != months[0]):
        return blocked("comparison_period", clarify=True)
    month = months[-1] if months else month_key(today)
    if comparison and month == "0001-01":
        return blocked("invalid_month", clarify=True)
    return ToolCall(provider="rules", tool="sales_comparison" if comparison else "monthly_sales", args={"month": month})


def validate_model_call(question: str, call: ToolCall, today: date) -> ToolCall:
    """Reject unexpected tools/arguments; explicit periods stay authoritative."""
    allowed = {"total_outstanding": set(), "top_debtor": set(), "customer_outstanding": {"name"}, "monthly_sales": {"month"}, "sales_comparison": {"month"}}
    if call.tool not in allowed or set(call.args) - allowed[call.tool]:
        return blocked()
    q = normalized(question)
    if call.tool in {"total_outstanding", "top_debtor", "customer_outstanding"}:
        if not DEBT.search(q):
            return blocked()
        if call.tool == "customer_outstanding":
            name = call.args.get("name")
            if not isinstance(name, str) or not name.strip() or len(name) > 120 or normalized(name) not in q:
                return blocked("missing_customer", clarify=True)
            call.args = {"name": name.strip()}
        return call
    # Sales queries should already be handled by the deterministic resolver.
    # Refuse to turn an unrecognized debt question into a sales answer.
    return blocked()


URDU_NAMES = {"احمد": {"ahmed", "ahmad"}, "بلال": {"bilal"}, "کامران": {"kamran"}, "طارق": {"tariq"}, "نوید": {"naveed"}, "زین": {"zain"}}


def resolve_customer_alias(name: str, known_names: list[str]) -> tuple[str, list[str]]:
    """Limited Urdu/Latin aliases resolve only to actual merchant-scoped names."""
    exact = [known for known in known_names if normalized(known) == normalized(name)]
    if exact:
        return exact[0], []
    aliases = URDU_NAMES.get(name, set())
    candidates = [known for known in known_names if normalized(known) in aliases]
    return (candidates[0], []) if len(candidates) == 1 else (name, candidates)
