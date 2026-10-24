export type HealthResponse = {
  status: string;
  service: string;
  module: string;
};

export type ProviderResponse = {
  selected_provider: "alibaba" | "groq" | "gemini" | "demo" | "unavailable";
  mode: string;
  configured: {
    alibaba: boolean;
    groq: boolean;
    gemini?: boolean;
  };
  models: {
    alibaba: string | null;
    groq_text: string | null;
    groq_vision: string | null;
    groq_transcribe: string | null;
  };
  missing_required_env: string[];
  message: string;
};

export type CaptureResponse = {
  capture_id: string;
  kind: "voice" | "receipt";
  filename: string | null;
  content_type: string | null;
  size_bytes: number;
  stored: boolean;
  received_at: string;
  path?: string;
  next_step: string;
};

export type LedgerEvent = {
  event_type: "sale" | "expense" | "credit_given" | "credit_received" | null;
  payment_type: "cash" | "credit" | null;
  customer_name: string | null;
  sender_name?: string | null;
  recipient_name?: string | null;
  transfer_purpose?: string | null;
  amount: number | null;
  currency: string;
  date: string | null;
  confidence: number | null;
  source: "voice" | "photo" | "manual" | "seed";
  raw_input: string;
  status: "validated" | "pending_validation";
  validation_notes: string[];
  evidence_filename?: string | null;
  ai_provider?: string | null;
  transcript_provider?: string | null;
  possible_duplicate?: boolean;
  duplicate_of?: number | null;
  notes?: string | null;
  customer_id?: number | null;
  remaining_amount?: number | null;
};

export type StoredLedgerEvent = LedgerEvent & {
  id: number;
  created_at: string;
};

export type LedgerSummary = {
  total_sales: number;
  total_expenses: number;
  total_receivables: number;
  total_payables: number;
  total_recovered: number;
  net_cash: number;
  record_count: number;
  recent_events: StoredLedgerEvent[];
};

export type CustomerBalance = {
  customer_name: string;
  receivable_balance: number;
  currency: string;
  event_count: number;
};

export type ReminderDraftResponse = {
  command_text: string;
  customer_name: string | null;
  balance: CustomerBalance | null;
  draft_message: string | null;
  status: "drafted" | "not_found" | "no_balance" | "pending_validation";
  channel: "draft_on_screen";
  notes: string[];
};

export type EvidenceProfile = {
  documentation_coverage: string;
  income_consistency: string;
  receivable_discipline: string;
  expense_pattern: string;
  customer_concentration: string;
  ledger_depth: string;
  trust_notes: string[];
};

export type FinancingProgram = {
  id: string;
  name: string;
  institution: string;
  product_type: string;
  target_customer: string;
  eligibility_notes: string;
  loan_range: string;
  required_documents: string[];
  source_url: string;
  last_checked: string;
  matching_hints: string[];
};

export type FinancingMatch = {
  program: FinancingProgram;
  relevance: "high" | "medium" | "low";
  match_reasons: string[];
  gaps: string[];
  grounded_summary: string;
};

export type IntelligenceResponse = {
  evidence_profile: EvidenceProfile;
  financing_matches: FinancingMatch[];
  summary: LedgerSummary;
};

export type AskResponse = {
  answer: string;
  tool_used: string;
  provider: string;
  answer_source?: string;
  data: Record<string, unknown>;
};

export type CombinedDataResponse = {
  summary: LedgerSummary;
  events: StoredLedgerEvent[];
  intelligence: {
    evidence_profile: EvidenceProfile;
    financing_matches: FinancingMatch[];
  };
  dashboard?: ProductDashboard;
  customers?: ProductCustomer[];
  passport?: ProductPassport;
  source_counts?: Record<string, number>;
};

export type ProductCustomer = {
  id: number;
  name: string;
  outstanding_paisa: number;
  oldest_unpaid: string | null;
  event_count: number;
};

export type ProductDashboard = {
  today: string;
  month: string;
  overdue_total_paisa: number;
  monthly_trend: { month: string; sales_paisa: number; expenses_paisa: number }[];
};

export type ProductPassport = {
  history_months: number;
  total_recorded_events: number;
  total_sales_paisa: number;
  total_recovered_paisa: number;
  credit_sales_total_paisa: number;
  recovery_rate_pct: number | null;
  evidence_coverage_pct: number;
  documentation_gaps: number;
  customer_concentration_pct: number | null;
  revenue_consistency: string;
  monthly_sales?: {month: string; sales_paisa: number}[];
};

export type UnderstandingResponse = {
  capture: CaptureResponse;
  provider: "alibaba" | "groq" | "gemini" | "demo";
  event: LedgerEvent;
};

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") || "http://localhost:8000/api";

/** Read Supabase's current in-memory session; do not maintain a second token cache. */
async function getAuthToken(): Promise<string | null> {
  // Supabase already keeps the browser session in memory. Read the current
  // session so account switches / token refreshes cannot reuse a stale token.
  try {
    const { supabase } = await import("@/lib/supabase");
    if (!supabase) return null;
    const { data } = await supabase.auth.getSession();
    return data.session?.access_token ?? null;
  } catch {
    return null;
  }
}

async function requestError(response: Response, action: string): Promise<Error> {
  if (response.status === 401) return new Error("Your session has expired. Please sign in again.");
  if (response.status === 403) return new Error("You do not have access to this record.");
  let detail = "";
  try {
    const body = await response.json();
    const candidate = body.detail ?? body.message ?? body.error?.message;
    if (typeof candidate === "string") detail = candidate;
    else if (Array.isArray(candidate)) detail = candidate.map((item: { msg?: string }) => item.msg).filter(Boolean).join(". ");
  } catch { /* Response may not be JSON. */ }
  return new Error(detail || `${action} (${response.status}). Please try again.`);
}

/** Build common headers (auth + content-type). */
async function authHeaders(extra?: Record<string, string>): Promise<Record<string, string>> {
  const headers: Record<string, string> = { ...extra };
  const token = await getAuthToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;
  return headers;
}

async function getJson<T>(path: string, signal?: AbortSignal): Promise<T> {
  const headers = await authHeaders();
  const response = await fetch(`${API_BASE_URL}${path}`, {
    cache: "no-store",
    headers,
    signal,
  });

  if (!response.ok) {
    throw await requestError(response, "Could not load your ledger");
  }

  return response.json() as Promise<T>;
}

export async function getHealth(): Promise<HealthResponse> {
  return getJson<HealthResponse>("/health");
}

export async function getProviderConfig(): Promise<ProviderResponse> {
  return getJson<ProviderResponse>("/config/ai-provider");
}

export async function uploadCapture(kind: "voice" | "receipt", file: File): Promise<CaptureResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const headers = await authHeaders();
  const response = await fetch(`${API_BASE_URL}/capture/${kind}`, {
    method: "POST",
    headers,
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`Upload failed: ${response.status}`);
  }

  return response.json() as Promise<CaptureResponse>;
}

export async function understandCapture(
  kind: "voice" | "receipt",
  file: File,
): Promise<UnderstandingResponse> {
  if (file.size > 4 * 1024 * 1024) throw new Error("Captures must be under 4 MB. Use a smaller receipt or shorter voice note.");
  const formData = new FormData();
  formData.append("file", file);

  const headers = await authHeaders();
  const response = await fetch(`${API_BASE_URL}/understand/${kind}`, {
    method: "POST",
    headers,
    body: formData,
  });

  if (!response.ok) {
    throw await requestError(response, "Could not understand this capture");
  }

  return response.json() as Promise<UnderstandingResponse>;
}

export async function getLedgerSummary(): Promise<LedgerSummary> {
  return getJson<LedgerSummary>("/ledger/summary");
}

export async function getLedgerEvents(): Promise<StoredLedgerEvent[]> {
  return getJson<StoredLedgerEvent[]>("/ledger/events");
}

/** Fetch through the authenticated API, never expose a private storage URL. */
export async function getReceiptEvidence(filename: string, signal?: AbortSignal): Promise<Blob> {
  const response = await fetch(`${API_BASE_URL}/evidence/files/${encodeURIComponent(filename)}`, {
    cache: "no-store", headers: await authHeaders(), signal,
  });
  if (!response.ok) throw await requestError(response, "Could not load this receipt");
  const mime = response.headers.get("Content-Type")?.split(";")[0].trim().toLowerCase();
  if (!mime || !["image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"].includes(mime)) {
    throw new Error("The receipt returned an unsupported file type.");
  }
  return response.blob();
}

export async function saveLedgerEvent(event: LedgerEvent): Promise<StoredLedgerEvent> {
  const headers = await authHeaders({ "Content-Type": "application/json" });
  const response = await fetch(`${API_BASE_URL}/ledger/events`, {
    method: "POST",
    headers,
    body: JSON.stringify(event),
  });

  if (!response.ok) {
    throw await requestError(response, "Could not save this entry");
  }

  return response.json() as Promise<StoredLedgerEvent>;
}

export async function getIntelligence(): Promise<IntelligenceResponse> {
  return getJson<IntelligenceResponse>("/intelligence");
}

export async function getCombinedData(): Promise<CombinedDataResponse> {
  return getJson<CombinedDataResponse>("/combined");
}

export async function draftReminder(file: File): Promise<ReminderDraftResponse> {
  if (file.size > 4 * 1024 * 1024) throw new Error("Voice notes must be under 4 MB. Try a shorter recording.");
  const formData = new FormData();
  formData.append("file", file);

  const headers = await authHeaders();
  const response = await fetch(`${API_BASE_URL}/actions/reminder/draft`, {
    method: "POST",
    headers,
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`Reminder draft failed: ${response.status}`);
  }

  return response.json() as Promise<ReminderDraftResponse>;
}

export async function askQuestion(question: string): Promise<AskResponse> {
  const headers = await authHeaders({ "Content-Type": "application/json" });
  const response = await fetch(`${API_BASE_URL}/ask`, {
    method: "POST",
    headers,
    body: JSON.stringify({ question }),
  });

  if (!response.ok) {
    throw await requestError(response, "Could not answer this question");
  }

  return response.json() as Promise<AskResponse>;
}

export async function seedDemoLedger(): Promise<StoredLedgerEvent[]> {
  // Historical, unrouted components still import this function. No sample
  // mutation is allowed: its server route and product entry point are removed.
  throw new Error("Sample data controls have been removed. Use your signed-in ledger.");
}

// Phase 2: public reviewed facts and ephemeral, authenticated preparation checks.
export type FinancingSource = { id: string; title: string; url: string; checked_on: string; note: string };
export type SchemeTerm = { id: string; label: string; value: string; source_id: string; topic: string };
export type SchemeCriterion = { id: string; label: string; requirement: string; source_id: string; kind: "range" | "boolean" | "lender" };
export type FinancingScheme = {
  id: string; short_name: string; name: string; institution: string; aliases: string[];
  description: string; application_url: string; availability: "confirm_with_institution" | "open" | "closed";
  availability_note: string; application_deadline: string | null; days_remaining: number | null;
  deadline_passed: boolean; sources: FinancingSource[]; terms: SchemeTerm[]; criteria: SchemeCriterion[];
};
export type FinancingCatalogue = {
  schema_version: 2; version: string; reviewed_on: string; generated_on: string;
  review_after_days: number; source_review_due: boolean; programs: FinancingScheme[];
};
export type ApplicantProfile = {
  age_years?: number | null; business_sector?: "retail" | "it_ecommerce" | "other" | null;
  resident_pakistani?: boolean | null; valid_cnic?: boolean | null;
  business_operating_months?: number | null; bank_statement_months?: number | null;
  bop_relationship_months?: number | null; bop_invited?: boolean | null;
  two_non_family_guarantors?: boolean | null; within_akhuwat_branch_area?: boolean | null;
  acceptable_property?: boolean | null; meezan_existing_relationship?: boolean | null;
  other_isaaf_financing?: boolean | null; requested_amount_rupees?: number | null;
};
export type PreparationCheck = {
  id: string; label: string; requirement: string; source_id: string;
  state: "declared_match" | "needs_attention" | "unknown" | "lender_check";
  current_display: string; gap_display: string | null;
};
export type SchemeAssessment = {
  program_id: string; preparation_pct: number; declared_matches: number; checkable_count: number;
  unknown_count: number; attention_count: number; lender_check_count: number;
  status: "details_needed" | "review_gaps" | "preparation_complete" | "source_review_due";
  checks: PreparationCheck[];
};
export type FinancingAssessment = {
  catalogue_version: string; source_review_due: boolean; generated_on: string;
  programs: SchemeAssessment[]; disclosure: string;
};

async function financingPost<T>(path: string, body: unknown, signal?: AbortSignal): Promise<T> {
  const response = await fetch(`${API_BASE_URL}/financing/${path}`, {
    method: "POST", cache: "no-store", signal,
    headers: await authHeaders({ "Content-Type": "application/json" }), body: JSON.stringify(body),
  });
  if (!response.ok) throw await requestError(response, "Could not check the financing information");
  return response.json() as Promise<T>;
}

export function getFinancingCatalogue(signal?: AbortSignal) {
  return getJson<FinancingCatalogue>("/financing/catalog", signal);
}
export function getFinancingAssessment(profile: ApplicantProfile, signal?: AbortSignal) {
  return financingPost<FinancingAssessment>("assessment", profile, signal);
}
export function askFinancingQuestion(question: string, programId: string | undefined, profile: ApplicantProfile, useAi: boolean, signal?: AbortSignal) {
  return financingPost<AskResponse>("questions", { question, program_id: programId, profile, use_ai: useAi }, signal);
}
