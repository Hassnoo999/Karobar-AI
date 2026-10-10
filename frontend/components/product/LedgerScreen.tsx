"use client";

import { BookOpenCheck, ChevronLeft, ChevronRight, Download, Filter, Search, UsersRound, X } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { formatPKR } from "@/lib/product-data";
import type { StoredLedgerEvent } from "@/lib/api";
import { ReceiptViewer } from "./ReceiptViewer";
import { useProductData } from "./useProductData";
import { EmptyState, eventLabels, formatDate, PageHeading, SourceBadge } from "./ui";

type EventFilter = "all" | keyof typeof eventLabels;
const filters: {value: EventFilter; label: string}[] = [{value: "all", label: "All entries"}, {value: "sale", label: "Cash sales"}, {value: "credit_given", label: "Credit sales"}, {value: "credit_received", label: "Repayments"}, {value: "expense", label: "Expenses"}];
const PAGE_SIZE = 10;

export function LedgerScreen() {
  const {summary, events, customers = [], dashboard, connection} = useProductData();
  const [view, setView] = useState<"transactions" | "customers">("transactions");
  const [type, setType] = useState<EventFilter>("all");
  const [query, setQuery] = useState("");
  const [source, setSource] = useState("all");
  const [overdue, setOverdue] = useState(false);
  const [page, setPage] = useState(1);
  const [receipt, setReceipt] = useState<StoredLedgerEvent | null>(null);
  const ready = connection === "live";

  useEffect(() => {
    const customer = new URLSearchParams(window.location.search).get("customer");
    if (customer) setQuery(customer);
  }, []);

  const filtered = useMemo(() => events.filter(event => {
    const searchText = [event.customer_name, event.raw_input, eventLabels[event.event_type ?? "sale"]].join(" ").toLowerCase();
    const isOverdue = event.event_type === "credit_given" && (event.remaining_amount ?? 0) > 0 && !!event.date && !!dashboard?.today && Date.parse(dashboard.today) - Date.parse(event.date) >= 30 * 86400000;
    return (type === "all" || event.event_type === type) && searchText.includes(query.trim().toLowerCase()) && (source === "all" || source === event.source) && (!overdue || isOverdue);
  }), [events, query, type, source, overdue, dashboard?.today]);
  const filteredCustomers = customers.filter(customer => customer.name.toLowerCase().includes(query.trim().toLowerCase()));
  const total = view === "transactions" ? filtered.length : filteredCustomers.length;
  const pageCount = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const activePage = Math.min(page, pageCount);
  const start = (activePage - 1) * PAGE_SIZE;
  const shownEvents = filtered.slice(start, start + PAGE_SIZE);
  const shownCustomers = filteredCustomers.slice(start, start + PAGE_SIZE);
  const unpaidCustomers = customers.filter(customer => customer.outstanding_paisa > 0).length;
  const hasFilters = !!query || type !== "all" || source !== "all" || overdue;

  function exportReport() {
    const safeCell = (value: unknown) => {
      const text = String(value ?? "");
      const safe = /^[=+\-@\t\r]/.test(text) ? "'" + text : text;
      return '"' + safe.replaceAll('"', '""') + '"';
    };
    const rows = view === "transactions" ? [
      ["Date", "Customer / counterparty", "Type", "Amount (PKR)", "Source", "Provider"],
      ...filtered.map(event => [event.date, event.customer_name, eventLabels[event.event_type ?? "sale"], event.amount, event.source, event.ai_provider]),
    ] : [
      ["Customer", "Outstanding (PKR)", "Oldest unpaid", "Recorded entries"],
      ...filteredCustomers.map(customer => [customer.name, customer.outstanding_paisa / 100, customer.oldest_unpaid, customer.event_count]),
    ];
    const url = URL.createObjectURL(new Blob(["\ufeff" + rows.map(row => row.map(safeCell).join(",")).join("\r\n")], {type: "text/csv;charset=utf-8"}));
    const anchor = document.createElement("a"); anchor.href = url; anchor.download = "karobaar-" + view + ".csv"; anchor.click();
    window.setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  function clearFilters() {setQuery(""); setType("all"); setSource("all"); setOverdue(false); setPage(1);}

  return <div>
    <PageHeading eyebrow="Your confirmed business history" title="Ledger & udhaar." description="Know what happened, who owes you, and which entries still need a follow-up." action={<button onClick={exportReport} disabled={!total || !ready} className="ui-button-secondary"><Download size={15} /> Export filtered {view === "customers" ? "balances" : "entries"}</button>} />
    <section className="ui-card mb-5 grid grid-cols-2 divide-y divide-[#e9eee5] sm:grid-cols-3 sm:divide-x sm:divide-y-0">
      <div className="col-span-2 flex items-center gap-4 p-5 sm:col-span-1"><span className="metric-icon tone-green"><UsersRound size={18} /></span><div><p className="ui-label">Outstanding customer credit</p><p className="mt-1 text-xl font-semibold tabular-nums">{ready ? formatPKR(summary.total_receivables) : "—"}</p><p className="mt-1 text-xs text-[#627258]">{unpaidCustomers} customers · all recorded history</p></div></div>
      <div className="flex items-center gap-4 p-5"><span className="metric-icon tone-coral"><Filter size={18} /></span><div><p className="ui-label">Unpaid for 30+ days</p><p className="mt-1 text-xl font-semibold tabular-nums">{dashboard ? formatPKR(dashboard.overdue_total_paisa / 100) : "—"}</p><p className="mt-1 text-xs text-[#627258]">Unsettled credit, not supplier payables</p></div></div>
      <div className="flex items-center gap-4 p-5"><span className="metric-icon tone-amber"><BookOpenCheck size={18} /></span><div><p className="ui-label">Confirmed entries</p><p className="mt-1 text-xl font-semibold tabular-nums">{ready ? summary.record_count : "—"}</p><p className="mt-1 text-xs text-[#627258]">Merchant-confirmed · sources retained</p></div></div>
    </section>

    <section className="ui-card overflow-hidden">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#e8eee4] px-4 py-3 md:px-6">
        <div className="flex gap-1 rounded-xl bg-[#f0f4eb] p-1" aria-label="Ledger view">{(["transactions", "customers"] as const).map(item => <button key={item} onClick={() => {setView(item); setPage(1);}} aria-pressed={view === item} className={"flex min-h-10 items-center gap-2 rounded-lg px-3 text-xs font-medium " + (view === item ? "bg-white text-[#315e3c] shadow-sm" : "text-[#627258]")}>{item === "transactions" ? <BookOpenCheck size={15} /> : <UsersRound size={15} />}{item === "transactions" ? "Transactions" : "Customers"}<span className="hidden text-[11px] text-[#627258] sm:inline">{item === "transactions" ? events.length : customers.length}</span></button>)}</div>
        <label className="relative w-full sm:w-64"><span className="sr-only">Search ledger</span><Search size={16} className="absolute left-3 top-3.5 text-[#627258]" /><input className="ui-input !mt-0 !min-h-11 pl-9" value={query} onChange={event => {setQuery(event.target.value); setPage(1);}} placeholder="Search customer or entry" /></label>
      </div>
      {view === "transactions" ? <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#edf1e8] p-4 md:px-6">
        <div className="no-scrollbar flex max-w-full gap-1 overflow-x-auto" aria-label="Transaction type">{filters.map(filter => <button key={filter.value} onClick={() => {setType(filter.value); setPage(1);}} aria-pressed={type === filter.value} className={"min-h-10 shrink-0 rounded-lg px-3 text-xs font-medium " + (type === filter.value ? "bg-[#e7f2df] text-[#477343]" : "text-[#627258] hover:bg-[#f5f8ef]")}>{filter.label}</button>)}</div>
        <div className="flex flex-wrap items-center gap-2"><label className="sr-only" htmlFor="source-filter">Entry source</label><select id="source-filter" className="min-h-10 rounded-lg border border-[#e0e7d9] bg-white px-2 text-xs text-[#627258]" value={source} onChange={event => {setSource(event.target.value); setPage(1);}}><option value="all">All sources</option><option value="voice">Voice</option><option value="photo">Receipt</option><option value="manual">Manual</option><option value="seed">Sample</option></select><button onClick={() => {setOverdue(!overdue); setPage(1);}} aria-pressed={overdue} className={"inline-flex min-h-10 items-center gap-1.5 rounded-lg border px-3 text-xs " + (overdue ? "border-[#e5c5af] bg-[#fff4e9] text-[#a06d44]" : "border-[#e0e7d9] text-[#627258]")}><Filter size={13} />30+ days unpaid</button></div>
      </div> : null}
      {hasFilters ? <div className="flex items-center justify-between bg-[#fbfcf8] px-5 py-2 text-xs text-[#627258]"><span>{total} matching {view === "customers" ? "customers" : "loaded entries"}</span><button onClick={clearFilters} className="flex min-h-9 items-center gap-1 text-[#637f53]"><X size={12} /> Clear filters</button></div> : null}
      {view === "transactions" ? <>
        <div className="hidden grid-cols-[1.5fr_1fr_.7fr_.7fr_.8fr] gap-4 border-b border-[#edf1e8] bg-[#fafcf7] px-6 py-3 text-[11px] font-medium uppercase tracking-wide text-[#627258] md:grid"><span>Customer / counterparty</span><span>Entry type</span><span>Date</span><span>Source</span><span className="text-right">Amount (PKR)</span></div>
        <div className="divide-y divide-[#edf1e8]">{shownEvents.map(event => <div key={event.id} className="grid grid-cols-[1fr_auto] items-center gap-x-3 gap-y-2 px-4 py-4 md:grid-cols-[1.5fr_1fr_.7fr_.7fr_.8fr] md:gap-4 md:px-6">
          <div className="min-w-0"><p className="truncate text-xs font-medium">{event.customer_name || "Walk-in"}</p><p className="mt-1 truncate text-[11px] text-[#627258]">Entry #{event.id}{event.ai_provider === "demo" ? " · Demo AI" : ""}</p></div>
          <p className={"col-start-1 row-start-2 text-xs md:col-auto md:row-auto " + (event.event_type === "expense" ? "text-[#a58b51]" : event.event_type === "credit_given" ? "text-[#867246]" : "text-[#588758]")}>{eventLabels[event.event_type ?? "sale"]}</p>
          <p className="col-start-1 row-start-3 text-[11px] text-[#627258] md:col-auto md:row-auto md:text-xs">{formatDate(event.date, {day: "numeric", month: "short", year: "numeric"})}</p>
          <div className="col-start-2 row-start-2 flex flex-col items-end gap-1 md:col-auto md:row-auto md:items-start"><SourceBadge source={event.source} provider={event.ai_provider} />{event.evidence_filename && connection === "live" ? <button onClick={() => setReceipt(event)} disabled={!!receipt} aria-label={`View receipt for entry ${event.id}`} className="min-h-9 text-[11px] font-medium text-[#477343] underline underline-offset-2 hover:text-[#25452d]">View receipt</button> : null}</div>
          <p className="col-start-2 row-start-1 text-right text-xs font-semibold tabular-nums md:col-auto md:row-auto">{formatPKR(event.amount ?? 0)}{overdue && event.remaining_amount != null ? <span className="mt-1 block text-[11px] font-normal text-[#a97b59]">{formatPKR(event.remaining_amount)} unpaid</span> : null}</p>
        </div>)}</div>
      </> : <>
        <div className="hidden grid-cols-[1.5fr_1fr_.7fr_1fr] gap-4 border-b border-[#edf1e8] bg-[#fafcf7] px-6 py-3 text-[11px] font-medium uppercase tracking-wide text-[#627258] md:grid"><span>Customer</span><span>Oldest unpaid</span><span>Entries</span><span className="text-right">Outstanding</span></div>
        <div className="divide-y divide-[#edf1e8]">{shownCustomers.map(customer => <button key={customer.id} onClick={() => {setQuery(customer.name); setView("transactions"); setPage(1);}} className="grid w-full grid-cols-[1fr_auto] items-center gap-2 px-4 py-4 text-left hover:bg-[#f8fbf4] md:grid-cols-[1.5fr_1fr_.7fr_1fr] md:gap-4 md:px-6"><div><p className="text-xs font-medium">{customer.name}</p><p className="mt-1 text-[11px] text-[#627258]">View this customer's entries</p></div><p className="col-start-1 row-start-2 text-xs text-[#627258] md:col-auto md:row-auto">{customer.oldest_unpaid ? "Since " + formatDate(customer.oldest_unpaid) : "Fully settled"}</p><p className="hidden text-xs text-[#627258] md:block">{customer.event_count}</p><p className="col-start-2 row-start-1 text-right text-xs font-semibold tabular-nums md:col-auto md:row-auto">{formatPKR(customer.outstanding_paisa / 100)}</p></button>)}</div>
      </>}
      {!total ? <EmptyState title={connection === "checking" ? "Loading your ledger" : hasFilters ? "No matching records" : "No entries yet"} description={hasFilters ? "Try another customer or clear your filters." : "Record a transaction to begin your business history."} record={!hasFilters && ready} /> : null}
      <div className="flex flex-wrap items-center justify-between gap-3 border-t border-[#e8eee4] px-4 py-3 md:px-6"><p className="text-xs text-[#627258]">{total ? start + 1 : 0}–{Math.min(start + PAGE_SIZE, total)} of {total} {view === "transactions" ? "loaded entries" : "customers"}</p><div className="flex items-center gap-2"><button onClick={() => setPage(activePage - 1)} disabled={activePage <= 1} className="ui-button-secondary !min-h-10 !px-3" aria-label="Previous page"><ChevronLeft size={15} /></button><span className="px-1 text-xs text-[#627258]">{activePage} / {pageCount}</span><button onClick={() => setPage(activePage + 1)} disabled={activePage >= pageCount} className="ui-button-secondary !min-h-10 !px-3" aria-label="Next page"><ChevronRight size={15} /></button></div></div>
    </section>
    <p className="mt-4 text-xs leading-5 text-[#627258]">{summary.record_count > events.length ? "Showing the latest " + events.length + " of " + summary.record_count + " entries. Filters and entry export apply to these loaded rows. " : ""}Customer balances use the full confirmed history and FIFO settlement, not just this page.</p>
    {receipt ? <ReceiptViewer entry={receipt} onClose={() => setReceipt(null)} /> : null}
  </div>;
}
