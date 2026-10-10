import { ArrowRight, Inbox, type LucideIcon } from "lucide-react";
import Link from "next/link";
import type { LedgerEvent } from "@/lib/api";
import { formatPKR } from "@/lib/product-data";

export function PageHeading({eyebrow, title, description, action}: {eyebrow: string; title: string; description: string; action?: React.ReactNode}) {
  return <div className="page-heading"><div className="min-w-0"><p className="ui-eyebrow">{eyebrow}</p><h1>{title}</h1><p className="ui-description">{description}</p></div>{action ? <div className="shrink-0">{action}</div> : null}</div>;
}

export function Metric({label, value, note, icon: Icon, tone = "green", unavailable = false}: {label: string; value: number; note: string; icon: LucideIcon; tone?: "green" | "coral" | "amber" | "blue"; unavailable?: boolean}) {
  return <article className="ui-card metric-card"><div className="flex items-center justify-between gap-3"><p className="ui-label">{label}</p><span className={`metric-icon tone-${tone}`}><Icon size={19} strokeWidth={1.8} /></span></div><p className="metric-value">{unavailable ? "—" : formatPKR(value)}</p><p className="ui-muted text-xs">{note}</p></article>;
}

export function EmptyState({title, description, record = false}: {title: string; description: string; record?: boolean}) {
  return <div className="ui-empty"><span className="grid h-12 w-12 place-items-center rounded-2xl bg-[#edf4f0] text-[#6a8277]"><Inbox size={22} /></span><h3>{title}</h3><p>{description}</p>{record ? <Link className="ui-button-primary mt-4" href="/record">Record a transaction <ArrowRight size={16} /></Link> : null}</div>;
}

export function SourceBadge({source, provider}: {source: LedgerEvent["source"]; provider?: string | null}) {
  const label = source === "seed" ? "Sample" : source === "manual" ? "Manual" : source === "photo" ? "Receipt" : "Voice";
  return <span className={`ui-badge ${source === "seed" || provider === "demo" ? "badge-amber" : "badge-neutral"}`}>{label}{provider === "demo" && source !== "seed" ? " · Demo AI" : ""}</span>;
}

export const eventLabels = {sale: "Cash sale", expense: "Expense", credit_given: "Credit sale", credit_received: "Repayment"};
export function formatDate(value: string | null, options: Intl.DateTimeFormatOptions = {day: "numeric", month: "short"}) {
  if (!value) return "No date";
  return new Intl.DateTimeFormat("en-PK", {...options, timeZone: "UTC"}).format(new Date(`${value.slice(0, 10)}T12:00:00Z`));
}
export function monthLabel(month: string | undefined) {
  return month ? formatDate(`${month}-01`, {month: "long", year: "numeric"}) : "Current month";
}
