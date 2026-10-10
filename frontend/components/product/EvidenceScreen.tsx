"use client";

import Link from "next/link";
import { ArrowRight, ArrowUpRight, Check, ChevronDown, ClipboardCopy, FileCheck2, FileText, MessageSquareText, ShieldCheck, X } from "lucide-react";
import { useRef, useState } from "react";
import type { ProductCustomer } from "@/lib/api";
import { formatPKR } from "@/lib/product-data";
import { useProductData } from "./useProductData";
import { EmptyState, formatDate, PageHeading } from "./ui";

function reminderFor(customer: ProductCustomer | undefined) {
  return customer ? "Assalam o alaikum " + customer.name + ". Aap ka " + formatPKR(customer.outstanding_paisa / 100) + " udhaar pending hai. Jab mumkin ho payment update kar dein. Shukriya." : "";
}

export function EvidenceScreen() {
  const {intelligence, summary, passport, dashboard, customers = [], source_counts, connection} = useProductData();
  const debtors = customers.filter(customer => customer.outstanding_paisa > 0);
  const dialog = useRef<HTMLDialogElement>(null);
  const [customerId, setCustomerId] = useState<number | null>(null);
  const [message, setMessage] = useState("");
  const [draftBalance, setDraftBalance] = useState<number | null>(null);
  const [copied, setCopied] = useState(false);
  const [copyError, setCopyError] = useState("");
  const selected = debtors.find(customer => customer.id === customerId);
  const staleDraft = !!selected && draftBalance !== selected.outstanding_paisa;
  const hasRecords = summary.record_count > 0;
  const sampleCount = source_counts?.seed ?? 0;
  const salesMonths = passport?.monthly_sales?.filter(point => point.sales_paisa > 0).length;
  const metrics = [
    {label: "Confirmed entries", value: passport ? String(passport.total_recorded_events) : "—", detail: sampleCount ? sampleCount + " sample entries included" : "Reviewed by the merchant"},
    {label: "Receipt-linked coverage", value: passport ? passport.evidence_coverage_pct + "%" : "—", detail: "Confirmed entries with an attachment"},
    {label: "Recorded history", value: passport ? passport.history_months + " months" : "—", detail: "Calendar span, not verified trading age"},
    {label: "Credit recovered", value: passport?.recovery_rate_pct != null ? passport.recovery_rate_pct + "%" : "—", detail: "Repayments ÷ recorded credit sales"},
  ];
  function selectCustomer(id: number) {
    const customer = debtors.find(item => item.id === id);
    setCustomerId(id); setMessage(reminderFor(customer)); setDraftBalance(customer?.outstanding_paisa ?? null); setCopied(false); setCopyError("");
  }
  function openReminder() {selectCustomer(debtors[0]?.id ?? 0); dialog.current?.showModal();}
  async function copyReminder() {
    try {
      if (!navigator.clipboard) throw new Error("Clipboard is not available. Select the text and copy it manually.");
      await navigator.clipboard.writeText(message); setCopied(true); setCopyError("");
    } catch {setCopied(false); setCopyError("Could not copy automatically. Select the message text and copy it manually.");}
  }

  return <div>
    <PageHeading eyebrow="Financial evidence passport" title="Better records. A stronger conversation." description="See what your ledger contains, what is missing, and what still needs a human check." action={<button onClick={openReminder} disabled={!debtors.length} className="ui-button-primary"><MessageSquareText size={16} /> Draft reminder</button>} />
    <section className="mb-5 flex flex-wrap items-center justify-between gap-5 rounded-2xl bg-[#1a402b] p-6 text-white">
      <div className="flex items-center gap-4"><span className="grid h-14 w-14 shrink-0 place-items-center rounded-2xl border border-[#91b788]/25 bg-white/[.04]"><ShieldCheck size={27} className="text-[#c2e4b8]" strokeWidth={1.4} /></span><div><p className="text-[11px] uppercase tracking-[.14em] text-[#c2d7bb]">An explainable business record</p><h2 className="mt-1 !text-xl !font-medium">Evidence, not a credit score.</h2><p className="mt-2 max-w-lg text-xs leading-5 text-[#d3e2cd]">Merchant-confirmed activity can support a financing discussion. It does not verify income externally or guarantee approval.</p></div></div>
      <div className="text-xs text-[#c2d7bb]"><p>Generated from the ledger</p><p className="mt-1 font-medium text-[#d3e2cd]">{dashboard ? formatDate(dashboard.today, {day: "numeric", month: "short", year: "numeric"}) : "Awaiting connection"}</p></div>
    </section>
    <div className="grid gap-5 xl:grid-cols-[1.35fr_1fr]">
      <section className="ui-card overflow-hidden">
        <div className="ui-section-heading"><div><h2>What is recorded</h2><p>Transparent metrics, without an eligibility verdict</p></div><FileCheck2 size={20} className="text-[#627258]" /></div>
        <div className="grid grid-cols-2 gap-x-5 gap-y-6 p-5 md:p-6">{metrics.map(metric => <div key={metric.label}><p className="text-xs text-[#627258]">{metric.label}</p><p className="mt-2 text-2xl font-semibold tabular-nums text-[#49693b]">{metric.value}</p><p className="mt-2 text-[11px] leading-5 text-[#627258]">{metric.detail}</p></div>)}</div>
        <div className="border-t border-[#e8eee1] px-5 py-4 md:px-6"><p className="text-xs font-medium">Sales history, with context</p><p className="mt-2 text-xs leading-6 text-[#627258]">{passport && hasRecords ? formatPKR(passport.total_sales_paisa / 100) + " total recorded sales" + (salesMonths != null ? " in " + salesMonths + " month(s) with sales activity." : ".") + " This is recorded activity, not audited revenue." : "Add confirmed transactions to build a financial history."}</p><p className="mt-2 text-xs leading-5 text-[#627258]">{passport?.customer_concentration_pct != null ? "The largest customer's share of all recorded credit sales is " + passport.customer_concentration_pct + "%." : "No recorded credit sales to assess customer concentration."}</p></div>
        <div className="flex flex-wrap gap-2 border-t border-[#e8eee1] px-5 py-3 md:px-6">{Object.entries(source_counts ?? {}).filter(([, count]) => count > 0).map(([source, count]) => <span key={source} className="ui-badge badge-neutral">{source === "seed" ? "Sample" : source[0].toUpperCase() + source.slice(1)} · {count}</span>)}</div>
      </section>
      <section className="ui-card overflow-hidden">
        <div className="ui-section-heading"><div><h2>Your next useful steps</h2><p>Separate recorded facts from manual checks</p></div><ArrowUpRight size={19} className="text-[#627258]" /></div>
        <div className="divide-y divide-[#eaf0e3] px-5">
          <div className="flex items-start gap-3 py-5"><span className="mt-0.5 grid h-7 w-7 shrink-0 place-items-center rounded-lg bg-[#f8efd9] text-[#a3874e]"><FileText size={15} /></span><div><p className="text-xs font-semibold">{passport?.evidence_coverage_pct ? "Keep adding source evidence" : "Add supporting receipts"}</p><p className="mt-1.5 text-xs leading-6 text-[#627258]">Attachments help trace an entry. They are not independently authenticated documents.</p><Link href="/record" className="mt-2 inline-flex items-center gap-1.5 text-xs font-medium text-[#6a8d52]">Record with a receipt <ArrowRight size={13} /></Link></div></div>
          <div className="flex items-start gap-3 py-5"><span className="mt-0.5 grid h-7 w-7 shrink-0 place-items-center rounded-lg bg-[#f1f4e9] text-[#627258]"><ShieldCheck size={15} /></span><div><p className="flex items-center gap-2 text-xs font-semibold">Identity documents <span className="ui-badge badge-amber">Manual check</span></p><p className="mt-1.5 text-xs leading-6 text-[#627258]">Prepare identity and business details for the institution. Karobaar has not verified your CNIC or legal status.</p></div></div>
          <div className="flex items-start gap-3 py-5"><span className="mt-0.5 grid h-7 w-7 shrink-0 place-items-center rounded-lg bg-[#f1f4e9] text-[#627258]"><FileText size={15} /></span><div><p className="flex items-center gap-2 text-xs font-semibold">Banking evidence <span className="ui-badge badge-amber">Manual check</span></p><p className="mt-1.5 text-xs leading-6 text-[#627258]">Check bank-statement, security and guarantor requirements directly. The ledger cannot establish these facts.</p></div></div>
        </div>
      </section>
    </div>

    <section className="mt-7">
      <div className="mb-4 flex flex-wrap items-end justify-between gap-2"><div><h2 className="!text-lg">Explore financing references</h2><p className="mt-1 text-xs leading-6 text-[#627258]">Reference links, not personalized eligibility or lending recommendations.</p></div><span className="ui-badge badge-neutral">Institution decides</span></div>
      <div className="ui-card divide-y divide-[#e6edde] overflow-hidden">{intelligence.financing_matches.length ? intelligence.financing_matches.slice(0, 5).map(match => <details key={match.program.id} className="group">
        <summary className="flex min-h-[82px] cursor-pointer list-none items-center gap-4 px-5 py-4 md:px-6"><span className="hidden h-10 w-10 shrink-0 place-items-center rounded-xl border border-[#dce6d1] bg-[#f6f9ef] text-[#627258] sm:grid"><FileText size={18} strokeWidth={1.4} /></span><div className="min-w-0 flex-1"><h3 className="text-xs font-semibold leading-6">{match.program.name}</h3><p className="mt-1 text-xs text-[#627258]">{match.program.institution}</p></div><ChevronDown size={17} className="shrink-0 text-[#627258] transition-transform group-open:rotate-180" /></summary>
        <div className="border-t border-[#eef2e8] bg-[#fafcf7] px-5 py-5 md:pl-20 md:pr-6">
          <p className="text-xs leading-6 text-[#627258]">Check the official source for current eligibility, documents, amounts and terms. No approval or fit is inferred from this ledger.</p>
          <div className="mt-3 rounded-lg border border-[#e6e7d2] bg-[#fffdf2] p-3 text-xs leading-6 text-[#96916a]">Recorded history is not verified business age. No sales or receipt-percentage threshold is used to infer qualification.</div>
          <div className="mt-4 flex flex-wrap items-center justify-between gap-3"><p className="text-[11px] text-[#627258]">{match.program.last_checked ? "Reference page reviewed: " + match.program.last_checked : "Current terms not verified"} · Reconfirm with institution</p><a href={match.program.source_url} target="_blank" rel="noreferrer" className="ui-button-secondary !min-h-10 !text-xs">Official source <ArrowUpRight size={13} /></a></div>
        </div>
      </details>) : <EmptyState title={connection === "checking" ? "Loading references" : "No references in this view"} description={connection === "demo" ? "The read-only preview does not simulate financing matches." : "References will appear when the updated backend is connected."} />}</div>
    </section>
    <p className="mt-4 text-xs leading-5 text-[#627258]">Karobaar helps organize evidence. It does not calculate a credit score, approve financing, or send reminders automatically.</p>

    <dialog ref={dialog} aria-labelledby="reminder-title" className="fixed inset-y-0 right-0 m-0 ml-auto h-[100dvh] max-h-none w-full max-w-[460px] border-0 bg-white p-0 text-[#2c4c32] shadow-2xl backdrop:bg-[#132d20]/45">
      <div className="flex h-full flex-col"><div className="flex items-center justify-between gap-3 border-b border-[#e4ecd9] px-6 py-5"><div><p className="ui-eyebrow !mb-1">Ledger-based template</p><h2 id="reminder-title">A reminder, in your words.</h2></div><button onClick={() => dialog.current?.close()} aria-label="Close reminder" className="grid h-11 w-11 place-items-center rounded-lg bg-[#f4f7ee] text-[#627258]"><X size={19} /></button></div>
        <div className="flex-1 overflow-y-auto p-6">
          <label className="ui-field">Customer<select className="ui-input" value={customerId ?? ""} onChange={event => selectCustomer(Number(event.target.value))}>{debtors.map(customer => <option key={customer.id} value={customer.id}>{customer.name}</option>)}</select></label>
          <div className="my-5 flex items-center justify-between rounded-xl bg-[#f1f7e9] p-4"><p className="text-xs text-[#627258]">Recorded outstanding</p><p className="text-sm font-semibold tabular-nums">{selected ? formatPKR(selected.outstanding_paisa / 100) : "—"}</p></div>
          <label className="ui-field">Edit your message<textarea className="ui-input min-h-[190px] resize-y !leading-7" value={message} onChange={event => {setMessage(event.target.value); setCopied(false);}} /></label>
          <p className="mt-3 text-xs leading-6 text-[#627258]">A deterministic template using the confirmed customer balance. Review the wording before copying.</p>
          {staleDraft ? <div role="alert" className="mt-4 rounded-xl bg-[#fff5df] p-4 text-xs text-[#9d824d]">The balance has changed. <button onClick={() => selectCustomer(customerId ?? 0)} className="underline">Regenerate this draft</button> before copying.</div> : null}
          <div className="mt-5 flex items-start gap-2 rounded-xl border border-[#e5e8ce] bg-[#fffdf0] p-4 text-xs leading-6 text-[#989064]"><ShieldCheck size={16} className="mt-1 shrink-0" /><p>Draft only. Copying does not send WhatsApp or SMS. You decide whether, where and to whom it is sent.</p></div>
          {connection === "demo" ? <p className="mt-3 text-xs text-[#9d824d]">Illustrative sample balance, not a real customer's debt.</p> : null}
          {copyError ? <p role="alert" className="mt-4 text-xs leading-6 text-[#a47550]">{copyError}</p> : null}
        </div>
        <div className="border-t border-[#e4ecd9] p-5"><button onClick={() => void copyReminder()} disabled={!message.trim() || !selected || staleDraft} className="ui-button-primary w-full">{copied ? <Check size={16} /> : <ClipboardCopy size={16} />}{copied ? "Message copied" : "Copy drafted message"}</button></div>
      </div>
    </dialog>
  </div>;
}
