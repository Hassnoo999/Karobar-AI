"use client";

import { ArrowUpRight, BookOpenCheck, LoaderCircle, Send } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { askFinancingQuestion, type ApplicantProfile, type AskResponse, type FinancingSource } from "@/lib/api";
import { formatDate } from "./ui";

export function financingSources(data: Record<string, unknown>): FinancingSource[] {
  return Array.isArray(data.sources) ? data.sources.filter((source): source is FinancingSource =>
    !!source && typeof source === "object" && typeof source.url === "string" &&
    source.url.startsWith("https://") && typeof source.title === "string" && typeof source.checked_on === "string") : [];
}

export function FinancingSources({ sources }: { sources: FinancingSource[] }) {
  return <div className="mt-4 flex flex-wrap gap-2" aria-label="Answer sources">
    {sources.map(source => <a key={source.id} href={source.url} target="_blank" rel="noreferrer" className="fin-source-link">
      <BookOpenCheck size={14} className="shrink-0" /><span>{source.title}<small>Reviewed {formatDate(source.checked_on, {day: "numeric", month: "short", year: "numeric"})}</small></span><ArrowUpRight size={12} />
    </a>)}
  </div>;
}

export function FinancingQuestions({ programId, profile, enabled = true }: {
  programId?: string; profile: ApplicantProfile; enabled?: boolean;
}) {
  const [question, setQuestion] = useState("");
  const [useAi, setUseAi] = useState(true);
  const [result, setResult] = useState<AskResponse | null>(null);
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);
  const request = useRef<AbortController | null>(null);

  useEffect(() => () => request.current?.abort(), []);

  async function ask(text: string) {
    const clean = text.trim();
    if (!enabled || clean.length < 2 || clean.length > 500 || request.current) return;
    const controller = new AbortController();
    request.current = controller;
    setPending(true); setError(""); setResult(null); setQuestion(clean);
    try {
      const answer = await askFinancingQuestion(clean, programId, profile, useAi, controller.signal);
      if (!controller.signal.aborted) setResult(answer);
    } catch (cause) {
      if (!controller.signal.aborted) setError(cause instanceof Error ? cause.message : "Could not reach the scheme information. Try again.");
    } finally {
      if (!controller.signal.aborted) setPending(false);
      if (request.current === controller) request.current = null;
    }
  }

  const examples = programId ? ["What documents and applicant checks are needed?", "Kitna loan milta hai?", "What is the application deadline?"] :
    ["Compare PM Youth and BOP loan amounts", "Akhuwat ke liye guarantor chahiye?", "HBL business age requirement?"];

  return <section className="fin-question-box" aria-label="Financing scheme questions">
    <div className="flex flex-wrap items-center justify-between gap-3"><div><p className="ui-eyebrow !mb-1">Ask with sources</p><h3 className="font-semibold">A question before the next step?</h3></div>
      <label className="flex min-h-11 items-center gap-2 text-xs text-[#62786b]"><input type="checkbox" checked={useAi} onChange={e => setUseAi(e.target.checked)} disabled={pending} className="h-4 w-4 accent-[#0c6b4a]" />AI relevance assist</label>
    </div>
    <p className="mt-2 text-xs leading-6 text-[#6a7d71]">Answers use the reviewed catalogue. AI can choose relevant facts, not invent loan terms. Your profile and ledger are not sent to the model.</p>
    <div className="my-4 flex flex-wrap gap-2">{examples.map(text => <button key={text} disabled={!enabled || pending} onClick={() => void ask(text)} className="fin-example">{text}<ArrowUpRight size={12} /></button>)}</div>
    <form onSubmit={event => {event.preventDefault(); void ask(question);}} className="flex items-end gap-2">
      <label className="min-w-0 flex-1"><span className="sr-only">Question about financing</span><textarea value={question} onChange={event => setQuestion(event.target.value)} rows={2} maxLength={500} disabled={!enabled || pending} className="ui-input !mt-0 resize-y" placeholder="Ask about amounts, requirements, documents or applying…" /></label>
      <button className="ui-button-primary !h-[72px] !px-4" disabled={!enabled || pending || question.trim().length < 2} aria-label="Ask scheme question">{pending ? <LoaderCircle size={18} className="animate-spin" /> : <Send size={18} />}</button>
    </form>
    {pending ? <p role="status" className="mt-4 text-xs text-[#617b6a]">Retrieving reviewed facts. If AI is unavailable, the sources still answer.</p> : null}
    {error ? <p role="alert" className="mt-4 rounded-xl bg-[#fff2e4] p-4 text-sm text-[#946333]">{error} No records were changed.</p> : null}
    {result ? <div className="mt-5 rounded-xl border border-[#d8e8db] bg-[#f9fcf7] p-4 md:p-5" aria-live="polite">
      <p className="mb-3 flex items-center gap-2 text-xs font-semibold text-[#3d6a50]"><BookOpenCheck size={16} />Reviewed source answer</p>
      <p dir="auto" className="whitespace-pre-wrap break-words text-sm leading-7 text-[#34533f]">{result.answer}</p>
      {result.data.retrieval_mode === "source_fallback" ? <p className="mt-3 text-xs text-[#8a7241]">AI assist was unavailable or its selection could not be verified. The reviewed source facts are shown directly.</p> : null}
      <FinancingSources sources={financingSources(result.data)} />
    </div> : null}
  </section>;
}
