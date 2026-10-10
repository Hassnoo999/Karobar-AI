"use client";

import Link from "next/link";
import { ArrowDownLeft, ArrowRight, ArrowUpRight, BarChart3, ChevronRight, Mic2, ReceiptText, RefreshCw, TrendingUp, UsersRound, WalletCards } from "lucide-react";
import { formatPKR } from "@/lib/product-data";
import { useProductData } from "./useProductData";
import { EmptyState, eventLabels, formatDate, Metric, monthLabel, PageHeading, SourceBadge } from "./ui";

function PerformanceChart({data}: {data: {month: string; sales_paisa: number; expenses_paisa: number}[]}) {
  const max = Math.max(...data.flatMap(point => [point.sales_paisa, point.expenses_paisa]), 1);
  return <div className="px-5 pb-5 pt-7 md:px-6">
    <div className="relative flex h-[220px] gap-3 border-b border-[#dde7de] px-2 pb-7">
      <div aria-hidden="true" className="pointer-events-none absolute inset-x-0 top-0 flex h-[188px] flex-col justify-between">{[1, .5, 0].map(ratio => <div key={ratio} className="border-t border-dashed border-[#e5ece5]" />)}</div>
      {data.map(point => <div key={point.month} className="relative flex min-w-0 flex-1 flex-col justify-end" tabIndex={0} aria-label={monthLabel(point.month) + ": sales " + formatPKR(point.sales_paisa / 100) + ", expenses " + formatPKR(point.expenses_paisa / 100)} title={monthLabel(point.month) + " · Sales " + formatPKR(point.sales_paisa / 100) + " · Expenses " + formatPKR(point.expenses_paisa / 100)}>
        <div className="flex h-[174px] items-end justify-center gap-1.5">
          <div className="w-full max-w-9 rounded-t-md bg-[#39835a]" style={{height: Math.max(point.sales_paisa > 0 ? 3 : 0, point.sales_paisa / max * 160)}} />
          <div className="w-full max-w-9 rounded-t-md bg-[#dac08b]" style={{height: Math.max(point.expenses_paisa > 0 ? 3 : 0, point.expenses_paisa / max * 160)}} />
        </div>
        <p className="absolute -bottom-5 w-full text-center text-xs text-[#738373]">{formatDate(point.month + "-01", {month: "short"})}</p>
      </div>)}
    </div>
    <details className="mt-4 text-xs text-[#68806c]"><summary className="cursor-pointer py-2">View exact monthly values</summary><div className="mt-2 overflow-x-auto"><table className="w-full text-left"><thead><tr><th className="py-2 font-medium">Month</th><th className="py-2 text-right font-medium">Sales</th><th className="py-2 text-right font-medium">Expenses</th></tr></thead><tbody>{data.map(point => <tr key={point.month} className="border-t border-[#edf1ed]"><td className="py-2">{monthLabel(point.month)}</td><td className="py-2 text-right tabular-nums">{formatPKR(point.sales_paisa / 100)}</td><td className="py-2 text-right tabular-nums">{formatPKR(point.expenses_paisa / 100)}</td></tr>)}</tbody></table></div></details>
  </div>;
}

export function DashboardScreen() {
  const {summary, events, customers = [], dashboard, passport, source_counts, connection, refreshing, refresh} = useProductData();
  const unavailable = connection === "checking" || (connection === "error" && summary.record_count === 0);
  const debtors = customers.filter(customer => customer.outstanding_paisa > 0);
  const seedCount = source_counts?.seed ?? 0;
  const trend = dashboard?.monthly_trend ?? [];
  const recovery = passport?.recovery_rate_pct;

  return <div>
    <PageHeading eyebrow="Business overview" title="A clearer picture of your business." description="Your confirmed sales, expenses and customer balances, in one place." action={<button onClick={() => void refresh()} disabled={refreshing} className="ui-button-secondary"><RefreshCw size={15} className={refreshing ? "animate-spin" : ""} /> {refreshing ? "Refreshing" : "Refresh"}</button>} />
    <section className="mb-5 flex flex-wrap items-center justify-between gap-5 overflow-hidden rounded-2xl bg-[#173e2c] px-6 py-6 text-white md:px-7">
      <div className="max-w-lg"><p className="mb-2 text-[11px] font-medium uppercase tracking-[.16em] text-[#c2d7bb]">Less typing. More clarity.</p><h2 className="!text-xl !font-medium text-white">Turn today's activity into tomorrow's evidence.</h2><p className="mt-2 text-xs leading-5 text-[#d3e2cd]">Speak or upload a receipt. Review the details. Only then does it count.</p></div>
      <Link href="/record" className="inline-flex min-h-12 items-center gap-3 rounded-xl border border-[#a6c9aa]/30 bg-[#d6edc9] px-5 text-sm font-semibold text-[#1b422e]"><Mic2 size={19} /> Record a transaction <ArrowUpRight size={17} /></Link>
    </section>
    <div className="mb-3 flex flex-wrap items-center justify-between gap-2"><p className="text-xs font-medium text-[#617562]">{monthLabel(dashboard?.month)} <span className="ml-2 font-normal text-[#627258]">· Confirmed entries only</span></p>{seedCount > 0 ? <span className="ui-badge badge-amber">{seedCount} sample entries included</span> : null}</div>
    <section className="grid grid-cols-2 gap-3 xl:grid-cols-4" aria-label="Business metrics">
      <Metric label="Sales this month" value={summary.total_sales} note="Cash + credit sales" icon={TrendingUp} unavailable={unavailable} />
      <Metric label="Expenses this month" value={summary.total_expenses} note="Recorded business costs" icon={ReceiptText} tone="amber" unavailable={unavailable} />
      <Metric label="Outstanding udhaar" value={summary.total_receivables} note="All-time unpaid customer credit" icon={UsersRound} tone="blue" unavailable={unavailable} />
      <Metric label="Repaid this month" value={summary.total_recovered} note="Payments received, not new sales" icon={ArrowDownLeft} unavailable={unavailable} />
    </section>

    <div className="mt-5 grid gap-5 xl:grid-cols-[1.65fr_1fr]">
      <section className="ui-card min-w-0">
        <div className="ui-section-heading"><div><h2>Sales & expenses</h2><p>Last {trend.length || "six"} recorded months · PKR</p></div><div className="flex gap-3 text-xs text-[#677b6a]"><span className="flex items-center gap-1.5"><i className="h-2 w-2 rounded-sm bg-[#39835a]" />Sales</span><span className="flex items-center gap-1.5"><i className="h-2 w-2 rounded-sm bg-[#dac08b]" />Expenses</span></div></div>
        {trend.length ? <PerformanceChart data={trend} /> : <EmptyState title={unavailable ? "Loading your trend" : "Your story starts with one entry"} description={unavailable ? "Waiting for the ledger connection." : "Recorded sales and expenses will appear here."} record={!unavailable} />}
      </section>
      <section className="ui-card p-6">
        <div className="flex items-center gap-2"><WalletCards size={19} className="text-[#528460]" /><h2>Customer credit, explained</h2></div>
        <div className="mt-6 flex items-center gap-5">
          <div className="grid h-24 w-24 shrink-0 place-items-center rounded-full" style={{background: "conic-gradient(#39835a " + Math.min(100, recovery ?? 0) * 3.6 + "deg, #eaf0e8 0)"}}><div className="grid h-[76px] w-[76px] place-items-center rounded-full bg-white"><span className="text-lg font-semibold tabular-nums">{recovery == null ? "—" : Math.round(recovery) + "%"}</span></div></div>
          <div><p className="text-sm font-semibold">Recovery rate</p><p className="mt-1 text-xs leading-5 text-[#778b7b]">All recorded repayments<br />÷ all recorded credit sales</p></div>
        </div>
        <dl className="mt-6 space-y-3 border-t border-[#edf1ea] pt-4 text-xs">
          <div className="flex justify-between gap-3"><dt className="text-[#718373]">Recovered over recorded history</dt><dd className="font-semibold tabular-nums">{passport ? formatPKR(passport.total_recovered_paisa / 100) : "—"}</dd></div>
          <div className="flex justify-between gap-3"><dt className="text-[#718373]">Unpaid for 30+ days</dt><dd className="font-semibold tabular-nums text-[#ac634b]">{dashboard ? formatPKR(dashboard.overdue_total_paisa / 100) : "—"}</dd></div>
        </dl>
        <Link href="/ledger" className="mt-5 flex items-center justify-between text-xs font-semibold text-[#326947]">Review customer balances <ArrowRight size={15} /></Link>
      </section>
    </div>

    <div className="mt-5 grid gap-5 xl:grid-cols-[1.65fr_1fr]">
      <section className="ui-card overflow-hidden">
        <div className="ui-section-heading"><div><h2>Recent activity</h2><p>The latest confirmed entries</p></div><Link href="/ledger" className="text-xs font-semibold text-[#3e7450]">View all <ChevronRight className="inline" size={14} /></Link></div>
        {events.length ? <div className="divide-y divide-[#edf1ed]">{events.slice(0, 4).map(event => <div key={event.id} className="flex items-center gap-3 px-5 py-4">
          <span className={"grid h-9 w-9 shrink-0 place-items-center rounded-xl " + (event.event_type === "expense" ? "bg-[#f7f1e4] text-[#9c7b39]" : "bg-[#eaf3e9] text-[#4c8058]")}>{event.event_type === "credit_received" ? <ArrowDownLeft size={17} /> : <ReceiptText size={17} />}</span>
          <div className="min-w-0 flex-1"><p className="truncate text-xs font-semibold">{event.customer_name || eventLabels[event.event_type ?? "sale"]}</p><div className="mt-1 flex flex-wrap items-center gap-2 text-[11px] text-[#627258]"><span>{eventLabels[event.event_type ?? "sale"]} · {formatDate(event.date)}</span><SourceBadge source={event.source} provider={event.ai_provider} /></div></div>
          <p className="text-xs font-semibold tabular-nums">{formatPKR(event.amount ?? 0)}</p>
        </div>)}</div> : <EmptyState title={unavailable ? "Loading activity" : "No activity yet"} description="Confirmed entries will appear here." />}
      </section>
      <section className="ui-card overflow-hidden">
        <div className="ui-section-heading"><div><h2>Follow up with confidence</h2><p>Highest outstanding balances first</p></div><UsersRound size={18} className="text-[#759879]" /></div>
        {debtors.length ? <div className="divide-y divide-[#edf1ed]">{debtors.slice(0, 4).map((customer, index) => <Link key={customer.id} href={"/ledger?customer=" + encodeURIComponent(customer.name)} className="flex items-center gap-3 px-5 py-4 hover:bg-[#f7faf6]"><span className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-[#edf3e9] text-xs font-medium text-[#618061]">{index + 1}</span><div className="min-w-0 flex-1"><p className="truncate text-xs font-semibold">{customer.name}</p><p className="mt-1 text-[11px] text-[#627258]">Unpaid since {formatDate(customer.oldest_unpaid)}</p></div><p className="text-xs font-semibold tabular-nums">{formatPKR(customer.outstanding_paisa / 100)}</p><ChevronRight size={14} className="text-[#627258]" /></Link>)}</div> : <EmptyState title={unavailable ? "Loading balances" : "No outstanding customers"} description="Customer credit will appear after a confirmed credit sale." />}
      </section>
    </div>
    <p className="mt-5 flex items-center gap-2 text-xs text-[#627258]"><BarChart3 size={14} /> Sales are not cash balance or profit. All figures reflect recorded activity only.</p>
  </div>;
}
