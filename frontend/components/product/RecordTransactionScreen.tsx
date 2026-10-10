"use client";

import Link from "next/link";
import { AlertTriangle, ArrowRight, Camera, Check, CheckCheck, FileImage, Mic2, PenLine, RotateCcw, ShieldCheck, Square, Upload, X } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { saveLedgerEvent, understandCapture, type LedgerEvent } from "@/lib/api";
import { formatPKR } from "@/lib/product-data";
import { useProductData } from "./useProductData";
import { PageHeading, SourceBadge } from "./ui";

type Status = "idle" | "preparing" | "recording" | "extracting" | "review" | "saving" | "saved" | "error";
type Mode = "voice" | "receipt" | "manual";
function pktDate() { return new Intl.DateTimeFormat("en-CA", {timeZone: "Asia/Karachi", year: "numeric", month: "2-digit", day: "2-digit"}).format(new Date()); }

export function RecordTransactionScreen() {
  const {connection, dashboard, refresh} = useProductData();
  const [mode, setMode] = useState<Mode>("voice");
  const [status, setStatus] = useState<Status>("idle");
  const [draft, setDraft] = useState<LedgerEvent | null>(null);
  const [sourceName, setSourceName] = useState("");
  const [error, setError] = useState("");
  const [duplicateReviewed, setDuplicateReviewed] = useState(false);
  const [preview, setPreview] = useState("");
  const input = useRef<HTMLInputElement>(null);
  const review = useRef<HTMLElement>(null);
  const recorder = useRef<MediaRecorder | null>(null);
  const stream = useRef<MediaStream | null>(null);
  const previewUrl = useRef("");
  const generation = useRef(0);
  const saving = useRef(false);
  const requestingMic = useRef(false);
  const busy = status === "preparing" || status === "recording" || status === "extracting" || status === "saving";
  const today = dashboard?.today ?? pktDate();
  const canCapture = connection === "live" && !busy && status !== "review";
  const validation: string[] = [];
  if (draft) {
    if (!draft.event_type) validation.push("Choose a transaction type.");
    if (draft.amount == null || !Number.isFinite(draft.amount) || draft.amount <= 0) validation.push("Enter a positive amount.");
    else if (!Number.isSafeInteger(Math.round(draft.amount * 100)) || Math.abs(draft.amount * 100 - Math.round(draft.amount * 100)) > 0.00001) validation.push("Use an amount with at most two decimal places.");
    if ((draft.event_type === "credit_given" || draft.event_type === "credit_received") && !draft.customer_name?.trim()) validation.push("A customer name is required for credit or repayment.");
    if (!draft.date || draft.date > today) validation.push("Choose a valid date, not in the future.");
    else if ((Date.parse(today) - Date.parse(draft.date)) / 86400000 > 730) validation.push("The date must be within the last two years.");
    if (draft.possible_duplicate && !duplicateReviewed) validation.push("Review and acknowledge the possible duplicate.");
  }

  useEffect(() => () => {
    generation.current += 1;
    if (recorder.current) recorder.current.onstop = null;
    stream.current?.getTracks().forEach(track => track.stop());
    if (previewUrl.current) URL.revokeObjectURL(previewUrl.current);
  }, []);
  useEffect(() => {
    if ((status === "review" || status === "saved") && window.innerWidth < 1024) review.current?.scrollIntoView({block: "start", behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth"});
  }, [status]);

  function reset(nextMode: Mode = mode) {
    generation.current += 1;
    if (previewUrl.current) URL.revokeObjectURL(previewUrl.current);
    previewUrl.current = "";
    setPreview(""); setSourceName(""); setError(""); setDraft(null); setDuplicateReviewed(false); setStatus("idle"); setMode(nextMode);
    if (input.current) input.current.value = "";
  }
  function manual() {
    reset("manual");
    setDraft({event_type: "sale", payment_type: "cash", customer_name: "", amount: null, currency: "PKR", date: today, confidence: null, source: "manual", raw_input: "Entered manually by merchant", status: "pending_validation", validation_notes: []});
    setSourceName("Manual entry"); setStatus("review");
  }
  async function processFile(kind: "voice" | "receipt", file: File) {
    if (file.size > 4 * 1024 * 1024) {setError(kind === "receipt" ? "Choose a receipt smaller than 4 MB." : "Keep voice notes under 4 MB. Try a shorter recording."); setStatus("error"); return;}
    const request = ++generation.current;
    setStatus("extracting"); setError(""); setDraft(null); setSourceName(file.name); setDuplicateReviewed(false);
    if (kind === "receipt") {
      if (previewUrl.current) URL.revokeObjectURL(previewUrl.current);
      previewUrl.current = URL.createObjectURL(file); setPreview(previewUrl.current);
    }
    try {
      const result = await understandCapture(kind, file);
      if (request !== generation.current) return;
      setDraft({...result.event, ai_provider: result.event.ai_provider ?? result.provider}); setStatus("review");
    } catch (err) {
      if (request !== generation.current) return;
      setError(err instanceof Error ? err.message : "Could not read this capture. Try again or enter it manually."); setStatus("error");
    }
  }
  async function startRecording() {
    if (!canCapture || requestingMic.current) return;
    const request = ++generation.current;
    requestingMic.current = true;
    setError(""); setStatus("preparing");
    try {
      if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === "undefined") throw new Error("Voice recording is not supported in this browser. Use a receipt or manual entry.");
      const audio = await navigator.mediaDevices.getUserMedia({audio: true});
      if (request !== generation.current) {audio.getTracks().forEach(track => track.stop()); return;}
      stream.current = audio;
      const media = new MediaRecorder(audio);
      const chunks: BlobPart[] = [];
      recorder.current = media;
      media.ondataavailable = event => {if (event.data.size) chunks.push(event.data);};
      media.onstop = () => {
        audio.getTracks().forEach(track => track.stop());
        if (request !== generation.current) return;
        const mime = media.mimeType || "audio/webm";
        void processFile("voice", new File(chunks, "voice-note.webm", {type: mime}));
      };
      media.start(); setStatus("recording");
    } catch (err) {
      stream.current?.getTracks().forEach(track => track.stop());
      if (request !== generation.current) return;
      setError(err instanceof Error && err.name !== "NotAllowedError" ? err.message : "Microphone access was denied. Allow it in your browser, or use a receipt/manual entry."); setStatus("error");
    } finally {requestingMic.current = false;}
  }
  async function confirm() {
    if (!draft || validation.length || saving.current || connection !== "live") return;
    saving.current = true; setStatus("saving"); setError("");
    try {
      await saveLedgerEvent({...draft, customer_name: draft.customer_name?.trim() || null, status: "validated"});
      setStatus("saved");
      await refresh();
    } catch (err) {setError(err instanceof Error ? err.message : "Save failed. Your draft is still here."); setStatus("review");}
    finally {saving.current = false;}
  }

  return <div>
    <PageHeading eyebrow="Capture → review → confirm" title="Record a transaction." description="Speak naturally or upload a receipt. You stay in control of every field." />
    <div className="mb-6 flex items-center gap-2 text-xs text-[#627258]" aria-label="Capture progress">
      {[["1", "Capture"], ["2", "Review"], ["3", "Confirmed"]].map(([step, label], index) => <div key={step} className="flex items-center gap-2"><span className={"grid h-6 w-6 place-items-center rounded-full text-[11px] " + ((index === 0 && status !== "review" && status !== "saved") || (index === 1 && status === "review") || (index === 2 && status === "saved") ? "bg-[#2e704c] text-white" : "bg-[#e5ece3] text-[#748570]")}>{step}</span>{label}{index < 2 ? <span className="mx-2 h-px w-5 bg-[#dbe4d8]" /> : null}</div>)}
    </div>
    <div className="grid items-start gap-5 lg:grid-cols-[.82fr_1.18fr]">
      <section className="ui-card overflow-hidden">
        <div className="grid grid-cols-3 gap-1 border-b border-[#e7ede4] p-2" aria-label="Capture method">{(["voice", "receipt", "manual"] as Mode[]).map(item => <button key={item} onClick={() => item === "manual" ? manual() : reset(item)} disabled={busy || status === "review" || connection !== "live"} aria-pressed={mode === item} className={"flex min-h-11 items-center justify-center gap-2 rounded-lg text-xs font-medium " + (mode === item ? "bg-[#e8f2e5] text-[#326c44]" : "text-[#627258]")}>{item === "voice" ? <Mic2 size={16} /> : item === "receipt" ? <Camera size={16} /> : <PenLine size={16} />}{item === "voice" ? "Voice" : item === "receipt" ? "Receipt" : "Manual"}</button>)}</div>
        <div className="px-6 py-7 text-center">
          <h2 className="!text-lg">{mode === "voice" ? "Say it the way you would." : mode === "receipt" ? "Keep the receipt. Capture the details." : "A simple, honest fallback."}</h2>
          <p className="mx-auto mt-2 max-w-xs text-xs leading-6 text-[#627258]">{mode === "voice" ? 'Try: “Naveed ne 5,000 rupay ka saman udhaar liya.” · Short notes, up to 4 MB.' : mode === "receipt" ? "JPEG, PNG, WebP or HEIC · up to 4 MB" : "Enter the facts yourself. No AI confidence is assigned to a manual entry."}</p>
          {mode === "voice" ? <div className="py-8"><button onClick={() => status === "recording" ? recorder.current?.stop() : void startRecording()} disabled={status !== "recording" && !canCapture} className={"mx-auto grid h-28 w-28 place-items-center rounded-full border-8 border-[#edf4e8] text-white shadow-[0_8px_32px_rgba(41,91,58,.1)] " + (status === "recording" ? "record-pulse bg-[#b56049]" : "bg-[#336d48]")} aria-label={status === "recording" ? "Stop recording" : "Start voice recording"}>{status === "recording" ? <Square size={28} fill="currentColor" /> : <Mic2 size={34} strokeWidth={1.5} />}</button><p aria-live="polite" className="mt-4 text-xs font-medium text-[#496b50]">{status === "recording" ? "Listening… tap to stop" : status === "extracting" ? "Reading your capture…" : "Tap to speak · Urdu or Roman Urdu"}</p></div> : mode === "receipt" ? <button onClick={() => input.current?.click()} disabled={!canCapture} className="my-6 flex min-h-[168px] w-full flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed border-[#c6dbc4] bg-[#f7faf3] text-sm text-[#527552]"><Upload size={25} strokeWidth={1.4} /><span>Choose a receipt photo</span><span className="text-xs text-[#627258]">Your original is retained as evidence</span></button> : <div className="my-8 flex justify-center"><PenLine size={35} className="text-[#627258]" strokeWidth={1.3} /></div>}
          <input ref={input} type="file" accept="image/jpeg,image/png,image/webp,image/heic,image/heif" className="hidden" aria-label="Receipt photo" onChange={event => {const file = event.target.files?.[0]; if (file) void processFile("receipt", file);}} />
          {mode === "voice" ? <button onClick={() => {reset("receipt"); input.current?.click();}} disabled={!canCapture} className="ui-button-secondary w-full"><FileImage size={16} /> Use a receipt instead</button> : null}
          {status === "review" ? <p className="mt-4 text-xs text-[#627258]">Finish or discard this draft before another capture.</p> : null}
        </div>
        <div className="flex items-start gap-3 border-t border-[#e7ede4] bg-[#f8faf5] px-6 py-4"><ShieldCheck size={17} className="mt-0.5 shrink-0 text-[#688963]" /><p className="text-xs leading-5 text-[#75866f]">No transaction is recorded until you select <strong>Confirm & save</strong>.</p></div>
      </section>

      <section ref={review} className="ui-card scroll-mt-24 overflow-hidden" aria-labelledby="review-title">
        <div className="ui-section-heading"><div><h2 id="review-title">{status === "saved" ? "Confirmed in your ledger" : "Review your entry"}</h2><p>{status === "saved" ? "The ledger now includes this transaction." : "Correct anything the AI missed."}</p></div><span className={"ui-badge " + (status === "saved" ? "badge-green" : status === "review" ? "badge-amber" : "badge-neutral")}>{status === "saved" ? "Saved" : status === "review" ? "Needs your review" : status === "extracting" ? "Extracting" : "Awaiting capture"}</span></div>
        {error ? <div role="alert" className="m-5 rounded-xl border border-[#edcfc1] bg-[#fff6f0] p-4 text-xs leading-5 text-[#a55e43]">{error}</div> : null}
        {status === "idle" || status === "preparing" || status === "recording" || status === "error" ? <div className="grid min-h-[300px] place-items-center px-6 py-10 text-center"><div><span className="mx-auto grid h-14 w-14 place-items-center rounded-2xl bg-[#f0f5ea] text-[#627258]"><FileImage size={24} strokeWidth={1.3} /></span><p className="mt-5 text-sm font-medium">{status === "error" ? "No entry was saved." : status === "preparing" ? "Waiting for microphone permission…" : "A clear draft, before a real entry."}</p><p className="mx-auto mt-2 max-w-xs text-xs leading-6 text-[#627258]">Customer, amount, date and transaction type will appear here for you to check.</p>{status === "error" ? <button className="ui-button-secondary mt-5" onClick={() => reset()}><RotateCcw size={14} /> Try again</button> : null}</div></div> : null}
        {status === "extracting" || status === "saving" ? <div role="status" className="grid min-h-[300px] place-items-center p-10 text-center"><div><span className="mx-auto block h-9 w-9 animate-spin rounded-full border-2 border-[#deead7] border-t-[#478259]" /><p className="mt-5 text-sm font-medium">{status === "saving" ? "Saving your confirmed entry…" : "Extracting the details…"}</p><p className="mt-2 text-xs text-[#627258]">Your ledger is unchanged until confirmation.</p></div></div> : null}
        {draft && (status === "review" || status === "saved") ? <div className="p-5 md:p-6">
          <div className="mb-5 flex items-center gap-3 rounded-xl bg-[#f6f8f0] p-3">
            {preview ? <img src={preview} alt="Uploaded receipt preview" className="h-14 w-14 rounded-lg border border-[#e0e7d7] object-cover" /> : <span className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-[#e8f0df] text-[#69805a]">{draft.source === "manual" ? <PenLine size={18} /> : <Mic2 size={18} />}</span>}
            <div className="min-w-0 flex-1"><p className="truncate text-xs font-medium">{sourceName}</p><div className="mt-1 flex flex-wrap items-center gap-2"><SourceBadge source={draft.source} provider={draft.ai_provider} />{draft.ai_provider && draft.ai_provider !== "demo" ? <span className="text-[11px] capitalize text-[#627258]">{draft.ai_provider}</span> : null}</div></div>
          </div>
          {draft.raw_input && draft.source !== "manual" ? <blockquote className="mb-5 border-l-2 border-[#acc9a0] pl-3 text-xs leading-6 text-[#708064]">{draft.raw_input}</blockquote> : null}
          {draft.ai_provider === "demo" ? <div role="status" className="mb-5 rounded-xl bg-[#fff6df] p-3 text-xs leading-5 text-[#917037]">Demo AI response, not verified recognition. Check every field yourself before using this entry.</div> : null}
          <div className="grid gap-4 sm:grid-cols-2">
            <label className="ui-field">Transaction type<select className="ui-input" value={draft.event_type ?? ""} disabled={status !== "review"} onChange={event => setDraft({...draft, event_type: event.target.value as LedgerEvent["event_type"]})}><option value="" disabled>Choose a type</option><option value="sale">Cash sale</option><option value="credit_given">Credit sale / udhaar</option><option value="credit_received">Customer repayment</option><option value="expense">Business expense</option></select></label>
            <label className="ui-field">{draft.event_type === "expense" ? "Supplier / description (optional)" : "Customer"}<input className="ui-input" maxLength={120} value={draft.customer_name ?? ""} disabled={status !== "review"} placeholder={draft.event_type === "sale" ? "Walk-in (optional)" : "Customer name"} onChange={event => setDraft({...draft, customer_name: event.target.value})} /></label>
            <label className="ui-field">Amount (PKR)<input className="ui-input tabular-nums" type="number" min="0.01" step="0.01" inputMode="decimal" value={draft.amount ?? ""} disabled={status !== "review"} placeholder="0.00" onChange={event => setDraft({...draft, amount: event.target.value === "" ? null : Number(event.target.value)})} /></label>
            <label className="ui-field">Transaction date<input className="ui-input" type="date" max={today} value={draft.date ?? ""} disabled={status !== "review"} onChange={event => setDraft({...draft, date: event.target.value})} /></label>
          </div>
          {draft.source !== "manual" ? <p className="mt-4 text-xs leading-5 text-[#627258]">Model confidence: {draft.confidence == null ? "not supplied" : Math.round(draft.confidence * 100) + "%"} · An estimate, not proof of accuracy.{draft.confidence != null && draft.confidence < .7 ? " Please review carefully." : ""}</p> : null}
          {draft.possible_duplicate && status === "review" ? <label className="mt-4 flex items-start gap-3 rounded-xl border border-[#e5d3ae] bg-[#fffaec] p-4 text-xs leading-5 text-[#90703b]"><input type="checkbox" className="mt-1 h-4 w-4 shrink-0" checked={duplicateReviewed} onChange={event => setDuplicateReviewed(event.target.checked)} /><span>Possible duplicate of entry #{draft.duplicate_of}. I checked the ledger and this is a separate transaction.</span></label> : null}
          {status === "review" && validation.length ? <ul className="mt-4 space-y-1 text-xs text-[#a47538]" aria-live="polite">{validation.map(note => <li key={note} className="flex items-start gap-2"><AlertTriangle size={13} className="mt-0.5 shrink-0" />{note}</li>)}</ul> : null}
          <div className="mt-6 flex flex-wrap items-center justify-between gap-3 border-t border-[#e6ece0] pt-5"><div><p className="text-[11px] text-[#627258]">{status === "saved" ? "Confirmed amount" : "Amount to record"}</p><p className="mt-1 text-xl font-semibold tabular-nums">{draft.amount == null ? "—" : formatPKR(draft.amount)}</p></div>{status === "review" ? <div className="flex gap-2"><button onClick={() => reset()} className="ui-button-secondary"><X size={15} /> Discard</button><button onClick={() => void confirm()} disabled={validation.length > 0 || connection !== "live"} className="ui-button-primary"><Check size={16} /> Confirm & save</button></div> : <span className="ui-badge badge-green"><CheckCheck size={15} /> Saved once</span>}</div>
          {status === "saved" ? <div className="mt-5 flex flex-wrap gap-3"><Link href="/ledger" className="ui-button-primary">View ledger <ArrowRight size={15} /></Link><button onClick={() => reset("voice")} className="ui-button-secondary">Record another</button></div> : null}
        </div> : null}
      </section>
    </div>
  </div>;
}
