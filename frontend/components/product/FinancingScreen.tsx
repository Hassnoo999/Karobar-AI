"use client";

import Link from "next/link";
import { ArrowRight, ArrowUpRight, Check, CircleHelp, Clock3, FileCheck2, Landmark, RefreshCw, Search, ShieldCheck, SlidersHorizontal, X } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { getFinancingCatalogue, getFinancingAssessment, type ApplicantProfile, type FinancingAssessment, type FinancingCatalogue, type FinancingScheme, type SchemeAssessment } from "@/lib/api";
import { formatPKR } from "@/lib/product-data";
import { ApplicantDetailsDialog } from "./ApplicantDetailsDialog";
import { FinancingQuestions, FinancingSources } from "./FinancingQuestions";
import { useProductData } from "./useProductData";
import { EmptyState, formatDate, PageHeading } from "./ui";

const labels: Record<SchemeAssessment["status"], string> = {
  details_needed: "Add your details", review_gaps: "Review preparation gaps",
  preparation_complete: "Preparation checks complete", source_review_due: "Source review due",
};

function Progress({ assessment }: { assessment?: SchemeAssessment }) {
  const value = assessment?.preparation_pct ?? 0;
  const complete = assessment?.status === "preparation_complete";
  return <div className="mt-5">
    <div className="mb-2 flex items-center justify-between gap-2 text-xs"><span className="text-[#62796b]">Preparation self-checks</span><span className="font-semibold tabular-nums">{value}%</span></div>
    <div role="progressbar" aria-label="Preparation self-check completion, not loan approval" aria-valuemin={0} aria-valuemax={100} aria-valuenow={value} className="fin-progress-track"><span className={complete ? "is-complete" : ""} style={{width: `${value}%`}} /></div>
    <p className="mt-2 text-[11px] leading-5 text-[#79887d]">{assessment ? `${assessment.declared_matches} of ${assessment.checkable_count} declared checks match · ${assessment.lender_check_count} lender check(s) remain` : "Add your details to compare. No fit is assumed."}</p>
  </div>;
}

function SchemeCard({ program, assessment, onOpen }: { program: FinancingScheme; assessment?: SchemeAssessment; onOpen: () => void }) {
  const amount = program.terms.find(term => term.topic === "amount");
  return <article className="fin-scheme-card">
    <div className="flex items-start justify-between gap-3"><span className="fin-bank-symbol" aria-hidden="true">{program.short_name === "PM Youth" ? "PM" : program.short_name.slice(0, 2).toUpperCase()}</span><span className={"ui-badge " + (assessment?.status === "preparation_complete" ? "badge-green" : assessment?.status === "review_gaps" || assessment?.status === "source_review_due" ? "badge-amber" : "badge-neutral")}>{assessment ? labels[assessment.status] : "Reviewed reference"}</span></div>
    <p className="mt-5 text-[11px] leading-5 text-[#829083]">{program.institution}</p><h2 className="mt-1 min-h-12 !text-lg !font-medium !leading-6">{program.name}</h2>
    <p className="mt-3 min-h-14 text-xs leading-6 text-[#6b7c70]">{program.description}</p>
    <div className="mt-4 border-y border-[#e7ede4] py-4"><p className="text-[10px] font-medium uppercase tracking-wider text-[#81907f]">Published amount</p><p className="mt-2 min-h-16 text-sm leading-6 text-[#30583e]">{amount?.value ?? "Confirm the amount with the institution."}</p></div>
    <Progress assessment={assessment} />
    <div className="mt-auto flex items-end justify-between gap-3 pt-6"><p className="text-[10px] leading-5 text-[#80907e]">Source snapshot<br />{formatDate(program.sources[0].checked_on, {day:"numeric",month:"short",year:"numeric"})}</p><button onClick={onOpen} className="ui-button-secondary !text-xs">View checks <ArrowUpRight size={14} /></button></div>
  </article>;
}

export function FinancingScreen() {
  const { connection, summary, passport, source_counts, refresh, refreshing } = useProductData();
  const [catalogue, setCatalogue] = useState<FinancingCatalogue | null>(null);
  const [assessment, setAssessment] = useState<FinancingAssessment | null>(null);
  const [profile, setProfile] = useState<ApplicantProfile>({});
  const latestProfile = useRef<ApplicantProfile>({});
  const [error, setError] = useState("");
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState("all");
  const [selectedId, setSelectedId] = useState("");
  const [profileRevision, setProfileRevision] = useState(0);
  const [answerRevision, setAnswerRevision] = useState(0);
  const detailsDialog = useRef<HTMLDialogElement>(null);
  const applicantDialog = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    if (connection !== "live") return;
    const controller = new AbortController();
    Promise.all([getFinancingCatalogue(controller.signal), getFinancingAssessment(latestProfile.current, controller.signal)])
      .then(([data, checked]) => {setCatalogue(data); setAssessment(checked); setError("");})
      .catch(cause => {if (!controller.signal.aborted) setError(cause instanceof Error ? cause.message : "Could not load financing references.");});
    return () => controller.abort();
  }, [connection]);

  useEffect(() => {
    if (profileRevision > 0) applicantDialog.current?.showModal();
  }, [profileRevision]);

  const assessments = assessment?.catalogue_version === catalogue?.version ? assessment?.programs ?? [] : [];
  const selected = catalogue?.programs.find(p => p.id === selectedId);
  const selectedAssessment = assessments.find(a => a.program_id === selectedId);
  const complete = assessments.filter(a => a.status === "preparation_complete").length;
  const programs = catalogue?.programs.filter(program => {
    const text = (program.name + " " + program.institution + " " + program.description).toLowerCase();
    const status = assessments.find(a => a.program_id === program.id)?.status;
    return text.includes(query.toLowerCase().trim()) && (filter === "all" || (filter === "complete" ? status === "preparation_complete" : status !== "preparation_complete"));
  }) ?? [];

  function editApplicant() {
    detailsDialog.current?.close(); setProfileRevision(value => value + 1);
  }
  async function saveProfile(next: ApplicantProfile) {
    const [checked, latest] = await Promise.all([getFinancingAssessment(next), getFinancingCatalogue()]);
    if (checked.catalogue_version !== latest.version) throw new Error("The source snapshot changed. Please compare your details again.");
    latestProfile.current = next;
    setProfile(next); setAssessment(checked); setCatalogue(latest); setError("");
    setAnswerRevision(value => value + 1);
  }
  const connected = connection === "live";
  const ledgerMetrics = [
    {label:"Confirmed records", value: connected ? String(summary.record_count) : "—", note:(source_counts?.seed ?? 0) > 0 ? "Includes labelled synthetic records" : "Your confirmed ledger"},
    {label:"Sales recorded this month", value: connected ? formatPKR(summary.total_sales) : "—", note:"Current PKT month, not audited revenue"},
    {label:"Expenses recorded this month", value: connected ? formatPKR(summary.total_expenses) : "—", note:"Not a lender affordability assessment"},
    {label:"Receipt-linked entries", value: connected && passport ? passport.evidence_coverage_pct + "%" : "—", note:"Attachments are not authenticated documents"},
  ];

  return <div className="fin-workspace">
    <PageHeading eyebrow="Financing, with evidence" title="Know the options. Prepare the next step." description="Explore reviewed sources, compare your declarations and see what the institution still needs to check." action={<button onClick={editApplicant} disabled={!catalogue || !connected} className="ui-button-primary"><SlidersHorizontal size={16} />Your details</button>} />
    <section className="fin-hero">
      <div className="relative z-10 max-w-xl"><p className="text-[10px] font-medium uppercase tracking-[.16em] text-[#9acdb5]">Your ledger is the starting point</p><h2 className="mt-4 !font-display !text-3xl !font-normal !leading-tight md:!text-4xl">A clearer financing conversation.<br /><span className="text-[#8ce0b5]">With the gaps still visible.</span></h2><p className="mt-4 max-w-lg text-sm leading-7 text-[#bfd4c7]">Five institution references. Published requirements beside your own details. A green checklist means preparation, never a promise of a loan.</p><div className="mt-6 flex flex-wrap gap-3"><button onClick={editApplicant} disabled={!catalogue || !connected} className="fin-hero-button">Prepare my details <ArrowRight size={15} /></button><Link href="/evidence" className="inline-flex min-h-11 items-center gap-2 px-2 text-xs text-[#c3dfcb]">See my evidence passport <ArrowUpRight size={14} /></Link></div></div>
      <div className="fin-hero-art" aria-hidden="true"><div className="fin-hero-orbit" /><div className="fin-glass-record"><FileCheck2 size={22} strokeWidth={1.4} /><span>Confirmed records</span><strong>{connected ? summary.record_count : "—"}</strong><small>Merchant-controlled evidence</small></div><div className="fin-glass-checks"><div className="fin-checks-ring" style={{background:`conic-gradient(#91e2b5 ${catalogue ? complete / catalogue.programs.length * 360 : 0}deg, #ffffff17 0)`}}><span>{complete}<small>of {catalogue?.programs.length ?? "—"}</small></span></div><p>Preparation checklists complete</p><small>Institution review remains</small></div></div>
    </section>
    <div className="my-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">{ledgerMetrics.map(metric => <div key={metric.label} className="ui-card px-5 py-4"><p className="text-xs text-[#718373]">{metric.label}</p><p className="mt-2 text-xl font-semibold tabular-nums text-[#385f42]">{metric.value}</p><p className="mt-2 text-[10px] leading-5 text-[#839082]">{metric.note}</p></div>)}</div>
    <div className="mb-6 flex flex-wrap items-start gap-3 rounded-xl border border-[#dae7db] bg-[#edf5eb] px-4 py-3 text-xs leading-6 text-[#59735a]"><ShieldCheck size={17} className="mt-0.5 shrink-0" /><p className="min-w-0 flex-1">Live ledger figures and user declarations are different sources of evidence. No minimum sales or expense threshold was verified for qualification in this catalogue. Your recorded history does not prove business age.</p><button onClick={() => void refresh()} disabled={refreshing} className="inline-flex min-h-9 items-center gap-2 font-medium"><RefreshCw size={13} className={refreshing ? "animate-spin" : ""} />Refresh ledger</button></div>
    {catalogue?.source_review_due ? <p role="alert" className="mb-5 rounded-xl bg-[#fff2d6] p-4 text-sm text-[#896823]">Source review is due. Terms may have changed; no checklist is marked current until the catalogue is reviewed.</p> : null}
    {error ? <div role="alert" className="mb-5 rounded-xl border border-[#efd8bd] bg-[#fff8eb] p-4 text-sm text-[#966b35]">{error}<button onClick={() => void Promise.all([getFinancingCatalogue(), getFinancingAssessment(profile)]).then(([data,checked]) => {setCatalogue(data); setAssessment(checked); setError("");}).catch(cause => setError(cause instanceof Error ? cause.message : "Please retry."))} className="ml-3 underline">Retry references</button></div> : null}
    <section aria-label="Financing catalogue">
      <div className="mb-4 flex flex-wrap items-end justify-between gap-4"><div><h2 className="!text-xl !font-medium">Explore financing programs</h2><p className="mt-2 text-xs leading-6 text-[#7b8a7a]">{catalogue ? `Source snapshot ${formatDate(catalogue.reviewed_on, {day:"numeric",month:"long",year:"numeric"})}. Not a live lender feed.` : "Loading the reviewed source snapshot…"}</p></div><div className="flex flex-wrap gap-2"><label className="relative"><span className="sr-only">Search financing programs</span><Search size={15} className="pointer-events-none absolute left-3 top-[15px] text-[#849584]" /><input className="ui-input !mt-0 !min-h-11 !pl-9 !text-xs" value={query} onChange={e => setQuery(e.target.value)} placeholder="Find an institution…" /></label><label><span className="sr-only">Preparation filter</span><select value={filter} onChange={e => setFilter(e.target.value)} className="ui-input !mt-0 !min-h-11 !text-xs"><option value="all">All programs</option><option value="incomplete">Needs preparation</option><option value="complete">Checks complete</option></select></label></div></div>
      <div className="grid gap-5 md:grid-cols-2 2xl:grid-cols-3">{programs.map(program => <SchemeCard key={program.id} program={program} assessment={assessments.find(a => a.program_id === program.id)} onOpen={() => {setSelectedId(program.id); detailsDialog.current?.showModal();}} />)}</div>
      {!programs.length ? <div className="ui-card"><EmptyState title={catalogue ? "No programs in this view" : "Waiting for reviewed references"} description={catalogue ? "Try another institution name or show all programs." : "Connect the backend to load the source catalogue. No sample loan terms are substituted."} /></div> : null}
    </section>
    <div className="mt-6"><FinancingQuestions key={answerRevision} profile={profile} enabled={connected && !!catalogue} /></div>
    <p className="mt-5 text-xs leading-6 text-[#7b8b7a]">Your applicant details reset when you leave this page or switch accounts. No application is submitted here. Confirm fees, documents, current intake and final terms with the institution.</p>

    <dialog ref={detailsDialog} aria-labelledby="scheme-title" className="fin-dialog max-w-[1120px]" onClick={event => {if (event.target === event.currentTarget) detailsDialog.current?.close();}}>
      <div className="fin-dialog-header"><div><p className="ui-eyebrow !mb-1">Published facts beside your declarations</p><h2 id="scheme-title">{selected?.name ?? "Financing program"}</h2></div><button onClick={() => detailsDialog.current?.close()} aria-label="Close program details" className="fin-close"><X size={20} /></button></div>
      {selected ? <div className="fin-dialog-content">
        <div className="grid gap-6 lg:grid-cols-[.9fr_1.1fr]">
          <section><div className="mb-5 flex items-center gap-3"><span className="fin-bank-symbol"><Landmark size={21} /></span><div><p className="text-sm font-semibold">{selected.institution}</p><p className="mt-1 text-xs text-[#7c8b7b]">Reviewed {formatDate(selected.sources[0].checked_on, {day:"numeric",month:"long",year:"numeric"})}</p></div></div>
            <p className="text-sm leading-7 text-[#5d7561]">{selected.description}</p><dl className="mt-5 divide-y divide-[#e7ede2]">{selected.terms.map(term => <div key={term.id} className="py-4"><dt className="text-xs font-semibold text-[#426448]">{term.label}</dt><dd className="mt-2 text-xs leading-6 text-[#6c7d6c]">{term.value}</dd></div>)}</dl>
            <div className="my-4 rounded-xl border border-[#eddfba] bg-[#fffaf0] p-4"><p className="flex items-center gap-2 text-xs font-semibold text-[#967b3d]"><Clock3 size={15} />Current intake needs confirmation</p><p className="mt-2 text-xs leading-6 text-[#8b805e]">{selected.availability_note}</p><p className="mt-2 text-xs font-medium text-[#7e744d]">{selected.application_deadline ? `Published deadline: ${selected.application_deadline}${selected.deadline_passed ? " (passed)" : ` · ${selected.days_remaining} days remaining`}` : "No verified closing date. No countdown is shown."}</p></div>
            <FinancingSources sources={selected.sources} /><details className="mt-3 text-[11px] leading-6 text-[#7d8978]"><summary className="cursor-pointer">Source verification notes</summary>{selected.sources.map(source => <p key={source.id} className="mt-2">{source.note}</p>)}</details>
            <a href={selected.application_url} target="_blank" rel="noreferrer" className="ui-button-secondary mt-5">Official application information <ArrowUpRight size={14} /></a>
          </section>
          <section className="rounded-2xl border border-[#dfebdb] bg-[#f6faf2] p-4 md:p-5"><div className="flex items-center justify-between gap-3"><div><p className="ui-eyebrow !mb-1">Preparation, not approval</p><h3 className="text-lg font-medium">Your comparison</h3></div><button onClick={editApplicant} className="ui-button-secondary !min-h-10 !px-3 !text-xs">Edit details</button></div><Progress assessment={selectedAssessment} />
            <div className="mt-5 space-y-3">{(selectedAssessment?.checks ?? selected.criteria.map(c => ({...c, state:"unknown", current_display:"Add your details", gap_display:null}))).map(check => <div key={check.id} className="rounded-xl border border-[#e2eadd] bg-white p-4"><div className="flex items-start gap-2"><span className={"mt-0.5 shrink-0 " + (check.state === "declared_match" ? "text-[#379567]" : check.state === "needs_attention" ? "text-[#b78141]" : "text-[#8b9a86]")}>{check.state === "declared_match" ? <Check size={16} /> : check.state === "lender_check" ? <Landmark size={16} /> : <CircleHelp size={16} />}</span><div><p className="text-xs font-semibold">{check.label}</p><p className="mt-1 text-xs leading-6 text-[#74836e]">{check.requirement}</p><p className="mt-2 text-xs font-medium text-[#4e7353]">Your info: {check.current_display}</p>{check.gap_display ? <p className="mt-1 text-xs leading-5 text-[#a07841]">{check.gap_display}</p> : null}<p className="mt-1 text-[10px] text-[#929d87]">{check.state === "declared_match" ? "Declaration matches this check. Institution verification remains." : check.state === "lender_check" ? "Not assessed by Karobaar" : check.state === "needs_attention" ? "A preparation gap, not a rejection decision" : "Unknown, not assumed to pass"}</p></div></div></div>)}</div>
            <p className="mt-4 text-xs leading-6 text-[#7b8a70]">This comparison covers the checks listed here, not every bank condition. Green means the declared preparation checks match. Lender review, documents and current availability remain separate.</p>
          </section>
        </div>
        <div className="mt-7"><FinancingQuestions key={`${selected.id}-${answerRevision}`} programId={selected.id} profile={profile} enabled={connected} /></div>
      </div> : null}
    </dialog>
    <ApplicantDetailsDialog key={profileRevision} dialog={applicantDialog} profile={profile} onSave={saveProfile} />
  </div>;
}
