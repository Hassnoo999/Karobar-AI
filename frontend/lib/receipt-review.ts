import type { LedgerEvent } from "./api";

export type TransferDirection = "received" | "sent";

/** The same validation is used by both the chooser and the drop zone. */
export function receiptFileError(files: readonly Pick<File, "name" | "type" | "size">[]): string | null {
  if (files.length !== 1) return "Choose one receipt photo at a time.";
  const file = files[0];
  if (!file.size) return "This photo is empty. Choose another receipt.";
  if (file.size > 4 * 1024 * 1024) return "Choose a receipt smaller than 4 MB.";
  if (file.type ? !["image/jpeg", "image/png", "image/webp"].includes(file.type) : !/\.(jpe?g|png|webp)$/i.test(file.name)) {
    return "Choose a JPEG, PNG or WebP photo. Export HEIC as JPEG first.";
  }
  return null;
}

export function receiptMime(file: Pick<File, "name" | "type">): string {
  return file.type || (/\.png$/i.test(file.name) ? "image/png" : /\.webp$/i.test(file.name) ? "image/webp" : "image/jpeg");
}

/** Money direction alone never determines sale/expense/repayment. */
export function withTransferDirection(draft: LedgerEvent, direction: TransferDirection): LedgerEvent {
  const name = direction === "received" ? draft.sender_name : draft.recipient_name;
  const incompatible = direction === "sent"
    ? draft.event_type === "sale" || draft.event_type === "credit_received"
    : draft.event_type === "expense";
  return {
    ...draft,
    customer_name: name ?? "",
    customer_id: null,
    event_type: incompatible ? null : draft.event_type,
    payment_type: incompatible ? null : draft.payment_type,
  };
}
