"use client";

import { useRef, useState, type RefObject } from "react";
import { ShieldCheck, X } from "lucide-react";
import type { ApplicantProfile } from "@/lib/api";

const numbers = [
  {key: "age_years", label: "Applicant / qualifying owner's age (years)", max: 120},
  {key: "requested_amount_rupees", label: "Amount you want to request (PKR)", min: 1, max: 100000000},
  {key: "business_operating_months", label: "Actual business operating age (months)", max: 1200},
  {key: "bank_statement_months", label: "Certified bank statements prepared (months)", max: 600},
  {key: "bop_relationship_months", label: "BOP banking relationship (months)", max: 600},
] as const;
const declarations = [
  {key: "resident_pakistani", label: "Resident Pakistani applicant"},
  {key: "valid_cnic", label: "Valid CNIC prepared (do not enter the number)"},
  {key: "bop_invited", label: "Received a BOP e-Business application invitation"},
  {key: "two_non_family_guarantors", label: "Two non-family guarantors prepared for Akhuwat"},
  {key: "within_akhuwat_branch_area", label: "Akhuwat branch confirmed you are in its service area"},
  {key: "meezan_existing_relationship", label: "Have an existing Meezan banking relationship"},
  {key: "other_isaaf_financing", label: "Already availing I-SAAF through another bank"},
] as const;

export function ApplicantDetailsDialog({ dialog, profile, onSave }: {
  dialog: RefObject<HTMLDialogElement | null>; profile: ApplicantProfile;
  onSave: (profile: ApplicantProfile) => Promise<void>;
}) {
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const inFlight = useRef(false);
  return <dialog ref={dialog} className="fin-dialog max-w-[850px]" aria-labelledby="applicant-title" onClick={event => {if (event.target === event.currentTarget && !saving) dialog.current?.close();}}>
    <div className="fin-dialog-header"><div><p className="ui-eyebrow !mb-1">Your declarations</p><h2 id="applicant-title">Prepare your applicant details</h2></div><button type="button" onClick={() => dialog.current?.close()} disabled={saving} aria-label="Close applicant details" className="fin-close"><X size={20} /></button></div>
    <form onSubmit={async event => {
      event.preventDefault();
      if (inFlight.current) return;
      const data = new FormData(event.currentTarget);
      const next: Record<string, unknown> = {};
      for (const field of numbers) {
        const raw = String(data.get(field.key) ?? "").trim();
        const value = Number(raw);
        if (raw && !Number.isSafeInteger(value)) {setError("Use whole numbers, or leave the field unknown."); return;}
        next[field.key] = raw ? value : null;
      }
      for (const field of declarations) {
        const raw = data.get(field.key);
        next[field.key] = raw === "true" ? true : raw === "false" ? false : null;
      }
      next.business_sector = data.get("business_sector") || null;
      inFlight.current = true; setSaving(true); setError("");
      try {await onSave(next as ApplicantProfile); dialog.current?.close();}
      catch (cause) {setError(cause instanceof Error ? cause.message : "Could not compare your details. Try again.");}
      finally {inFlight.current = false; setSaving(false);}
    }}>
      <div className="fin-dialog-content">
        <p className="mb-6 rounded-xl border border-[#e5e8d2] bg-[#fffdf1] p-4 text-xs leading-6 text-[#837547]">Leave anything you do not know blank. These details stay in this page's memory and are not saved as a profile or sent to an AI provider. A match is based on your declaration, not verification by a bank.</p>
        <div className="grid gap-5 sm:grid-cols-2">
          {numbers.map(field => <label key={field.key} className="ui-field">{field.label}<input name={field.key} type="number" min={"min" in field ? field.min : 0} max={field.max} step="1" defaultValue={profile[field.key] ?? ""} className="ui-input" placeholder="Unknown" inputMode="numeric" /></label>)}
          <label className="ui-field">Business sector<select name="business_sector" defaultValue={profile.business_sector ?? ""} className="ui-input"><option value="">Unknown</option><option value="retail">Retail / kiryana</option><option value="it_ecommerce">IT / e-commerce</option><option value="other">Other business</option></select></label>
        </div>
        <p className="mt-3 text-xs leading-6 text-[#6f8175]">Business operating age is your actual trading history. Do not copy the calendar span of your Karobaar ledger into this field unless it truly is the business age.</p>
        <div className="mt-7 grid gap-5 sm:grid-cols-2">{declarations.map(field => <label key={field.key} className="ui-field">{field.label}<select name={field.key} defaultValue={profile[field.key] == null ? "" : String(profile[field.key])} className="ui-input"><option value="">Unknown / not checked</option><option value="true">Yes</option><option value="false">No</option></select></label>)}</div>
        {error ? <p role="alert" className="mt-5 text-sm text-[#ac5b40]">{error}</p> : null}
      </div>
      <div className="fin-dialog-footer"><p className="flex max-w-md items-center gap-2 text-xs leading-5 text-[#708374]"><ShieldCheck size={16} className="shrink-0" />No CNIC number, address or bank account details collected.</p><button className="ui-button-primary" disabled={saving}>{saving ? "Comparing…" : "Update preparation checks"}</button></div>
    </form>
  </dialog>;
}
