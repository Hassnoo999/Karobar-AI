import type { CombinedDataResponse, StoredLedgerEvent } from "./api";

// Explicit read-only preview. All screens share this one coherent sample ledger.
const sample = (id: number, event_type: StoredLedgerEvent["event_type"], amount: number, name: string): StoredLedgerEvent => ({
  id, event_type, amount, customer_name: name, customer_id: name === "Naveed" ? 1 : null,
  payment_type: event_type === "credit_given" ? "credit" : "cash", currency: "PKR", date: "2026-10-10",
  confidence: null, source: "seed", ai_provider: "demo", raw_input: "Illustrative sample entry",
  status: "validated", validation_notes: [], created_at: `2026-10-10T10:0${id}:00`,
  remaining_amount: event_type === "credit_given" ? 3000 : null,
});
const events = [sample(4, "credit_received", 2000, "Naveed"), sample(3, "expense", 1200, "Supplies"), sample(2, "credit_given", 5000, "Naveed"), sample(1, "sale", 8000, "Walk-in")];
const summary = { total_sales: 13000, total_expenses: 1200, total_receivables: 3000, total_payables: 0, total_recovered: 2000, net_cash: 11800, record_count: 4, recent_events: events };

export const demoProductData: CombinedDataResponse = {
  summary, events,
  dashboard: {today: "2026-10-10", month: "2026-10", overdue_total_paisa: 0, monthly_trend: [{month: "2026-10", sales_paisa: 1300000, expenses_paisa: 120000}]},
  customers: [{id: 1, name: "Naveed", outstanding_paisa: 300000, oldest_unpaid: "2026-10-10", event_count: 2}],
  passport: { history_months: 1, total_recorded_events: 4, total_sales_paisa: 1300000, total_recovered_paisa: 200000, credit_sales_total_paisa: 500000, recovery_rate_pct: 40, evidence_coverage_pct: 0, documentation_gaps: 1, customer_concentration_pct: 100, revenue_consistency: "insufficient data" },
  source_counts: {seed: 4, manual: 0, voice: 0, receipt: 0},
  intelligence: { evidence_profile: {documentation_coverage: "No receipt attachments", income_consistency: "One illustrative month", receivable_discipline: "PKR 2,000 repaid out of PKR 5,000 credit", expense_pattern: "One sample expense", customer_concentration: "One credit customer", ledger_depth: "4 sample entries", trust_notes: ["Illustrative data only", "Read-only preview", "Not a credit score"]}, financing_matches: [] },
};
