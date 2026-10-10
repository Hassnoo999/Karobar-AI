"""Render ledger facts without allowing a model to rewrite financial numbers."""
import calendar

from app.services.ask_resolver import language


def month_label(month: str) -> str:
    return f"{calendar.month_name[int(month[5:7])]} {month[:4]}"


REASONS = {
    "invalid_month": "Please give a valid calendar month, for example August 2026 or 2026-08.",
    "specify_year": "Please include the year for that month so I do not guess the period.",
    "specify_month": "Please specify one calendar month, not just a year.",
    "future_month": "That month is in the future. I can report recorded sales up to the current month.",
    "daily_period": "This version supports monthly sales, not daily, weekly, quarterly or yearly sales. Please specify a calendar month.",
    "historical_balance": "Customer balances are current and all-time, not historical balances for a requested date. Ask for the current balance instead.",
    "comparison_period": "I can compare a calendar month with its immediately preceding month. Please specify that pair.",
    "customer_comparison": "I cannot compare customers in this version. Ask about one customer's balance at a time.",
    "customer_ranking": "I can identify the highest outstanding customer, not produce other customer rankings or lists yet.",
    "missing_customer": "Which customer do you mean? Please include the customer's recorded name.",
    "one_question": "Please ask one ledger question at a time: a customer balance or monthly sales.",
    "sales_scope": "Monthly sales include cash plus credit sales. Filtered sales, rankings and sample exclusion are not supported chat tools yet.",
}


def render_answer(question: str, tool: str, data: dict) -> str:
    lang = language(question)
    if tool == "unsupported":
        reason = REASONS.get(data.get("reason"), "I can answer current customer balances, total udhaar, the highest outstanding customer, monthly sales and adjacent-month sales comparisons. Expenses, profit, cash balance, reminders and loan eligibility are not chat tools in this version.")
        return ("یہ سوال اس شکل میں دستیاب نہیں ہے۔ " if lang == "ur" else "Maazrat. " if lang == "roman" else "") + reason
    if tool == "total_outstanding":
        money = data["total_outstanding_display"]
        return f"تمام درج شدہ ریکارڈ کے مطابق موجودہ کل ادھار {money} ہے۔" if lang == "ur" else f"Aap ka current total udhaar {money} hai — tamam confirmed history se." if lang == "roman" else f"Current outstanding customer credit is {money}, across the full confirmed history."
    if tool == "top_debtor":
        if not data["name"]:
            return "کوئی ادھار باقی نہیں ہے۔" if lang == "ur" else "Abhi kisi customer ka udhaar pending nahi hai." if lang == "roman" else "No customer has outstanding credit in the confirmed ledger."
        name, money = data["name"], data["outstanding_display"]
        return f"سب سے زیادہ موجودہ ادھار {name} کا ہے: {money}۔" if lang == "ur" else f"Sab se zyada current udhaar {name} ka hai: {money}." if lang == "roman" else f"{name} has the highest current outstanding balance: {money}."
    if tool == "customer_outstanding":
        if data["status"] != "ok":
            choices = ", ".join(data.get("candidates", []))
            if data["status"] == "ambiguous":
                return f"Please choose the exact recorded customer name: {choices}. No balance has been assumed."
            if data["status"] == "missing_name":
                return REASONS["missing_customer"]
            return "No exact customer match was found. " + ("Recorded names: " + choices + "." if choices else "There are no customer records yet.")
        name, money = data["name"], data["outstanding_display"]
        return f"{name} کا موجودہ بقایا ادھار {money} ہے۔" if lang == "ur" else f"{name} ka current outstanding udhaar {money} hai." if lang == "roman" else f"{name}'s current outstanding balance is {money}."
    if tool == "monthly_sales":
        month, money, cash, credit = month_label(data["month"]), data["sales_display"], data["cash_sales_display"], data["credit_sales_display"]
        return f"{month} کی درج شدہ فروخت {money} ہے (نقد {cash} + ادھار فروخت {credit})۔ یہ منافع یا نقد بیلنس نہیں ہے۔" if lang == "ur" else f"{month} ki confirmed sales {money} thi (cash {cash} + credit sales {credit}). Yeh profit ya cash balance nahi hai." if lang == "roman" else f"Recorded sales for {month}: {money} (cash {cash} + credit sales {credit}). This is not profit or cash balance."
    current, previous = data["current"], data["previous"]
    current_month, previous_month = month_label(current["month"]), month_label(previous["month"])
    direction = {"up": "higher", "down": "lower", "same": "unchanged"}[data["direction"]]
    change = data["delta_display"]
    if lang == "ur":
        return f"{current_month} کی فروخت: {current['sales_display']}؛ {previous_month}: {previous['sales_display']}۔ فرق: {change}۔ دونوں اعداد درج شدہ نقد اور ادھار فروخت کا مجموعہ ہیں۔"
    if lang == "roman":
        return f"{current_month} ki sales: {current['sales_display']}; {previous_month}: {previous['sales_display']}. Farq: {change}. Dono totals mein confirmed cash aur credit sales shamil hain."
    return f"Sales for {current_month}: {current['sales_display']}; {previous_month}: {previous['sales_display']}. Change: {change}, {direction}. Both totals include confirmed cash and credit sales."
