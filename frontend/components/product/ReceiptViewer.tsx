"use client";

import { Download, LoaderCircle, X } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { getReceiptEvidence, type StoredLedgerEvent } from "@/lib/api";
import { formatPKR } from "@/lib/product-data";
import { eventLabels, formatDate } from "./ui";

export function ReceiptViewer({entry, onClose}: {entry: StoredLedgerEvent; onClose: () => void}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [imageUrl, setImageUrl] = useState("");
  const [error, setError] = useState("");
  const [previewError, setPreviewError] = useState(false);
  const filename = entry.evidence_filename;

  useEffect(() => {
    const controller = new AbortController();
    let disposed = false;
    let url = "";
    dialog.current?.showModal();
    setImageUrl(""); setError(""); setPreviewError(false);
    if (filename) {
      void getReceiptEvidence(filename, controller.signal).then(image => {
        if (disposed) return;
        url = URL.createObjectURL(image);
        setImageUrl(url);
      }).catch(err => {
        if (!disposed) setError(err instanceof Error ? err.message : "Could not load this receipt. Close and try again.");
      });
    } else setError("This entry has no receipt attachment.");
    return () => {
      disposed = true;
      controller.abort();
      if (url) URL.revokeObjectURL(url);
    };
  }, [filename]);

  const extension = filename?.split(".").pop() ?? "png";
  return <dialog ref={dialog} aria-labelledby="receipt-title" onClose={onClose} onClick={event => {
    if (event.target === event.currentTarget) dialog.current?.close();
  }} className="fixed inset-0 m-auto max-h-[90dvh] w-[calc(100%_-_2rem)] max-w-[850px] overflow-y-auto rounded-2xl border-0 bg-white p-0 text-[#2c4c32] shadow-2xl backdrop:bg-[#132d20]/50">
    <div className="flex items-center justify-between gap-4 border-b border-[#e4ecd9] px-5 py-4">
      <div className="min-w-0"><p className="ui-eyebrow !mb-1">Source attachment · Entry #{entry.id}</p><h2 id="receipt-title" className="truncate">Receipt for {entry.customer_name || "this entry"}</h2></div>
      <button onClick={() => dialog.current?.close()} aria-label="Close receipt" className="grid h-11 w-11 shrink-0 place-items-center rounded-lg bg-[#f4f7ee] text-[#627258]"><X size={19} /></button>
    </div>
    <div className="p-5">
      <p className="mb-4 text-xs leading-6 text-[#627258]">{eventLabels[entry.event_type ?? "sale"]} · {formatPKR(entry.amount ?? 0)} · {formatDate(entry.date, {day: "numeric", month: "short", year: "numeric"})}{entry.ai_provider ? " · " + entry.ai_provider : ""}</p>
      {error ? <p role="alert" className="rounded-xl bg-[#fff5df] p-4 text-sm leading-6 text-[#986d42]">{error}</p> : imageUrl ? <>
        {previewError ? <p role="status" className="rounded-xl bg-[#f4f7ee] p-4 text-sm leading-6">Your browser cannot preview this image format. You can still download the original.</p> : <img src={imageUrl} alt={"Original receipt attached to entry " + entry.id} onError={() => setPreviewError(true)} className="mx-auto max-h-[58dvh] max-w-full rounded-lg border border-[#e4ecd9] object-contain" />}
        <a href={imageUrl} download={`karobaar-receipt-${entry.id}.${extension}`} className="ui-button-secondary mt-4 w-fit"><Download size={15} /> Download original</a>
      </> : <p role="status" className="flex min-h-[180px] items-center justify-center gap-2 text-sm text-[#627258]"><LoaderCircle size={18} className="animate-spin motion-reduce:animate-none" /> Loading your private receipt…</p>}
      <p className="mt-4 text-xs leading-6 text-[#627258]">Retained source evidence, not an independently authenticated document. The app checks merchant ownership before opening this attachment.</p>
    </div>
  </dialog>;
}
