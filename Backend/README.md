# Karobaar AI — Backend

Voice-first financial evidence and decision support for informal Pakistani merchants
(kiryana stores, tailors, mechanics). Built for the **Alibaba Cloud AI Hackathon
Pakistan 2026** — Financial Inclusion track.

A merchant speaks one sentence in Urdu / Roman Urdu ("Ahmed ne paanch hazaar ka maal
udhaar liya"), snaps a receipt, or asks a question ("Total udhaar kitna hai?") — and
gets reviewable business records plus a **Financial Evidence Passport**
they can show to microfinance lenders.

## Core design rule

> **AI captures and explains. SQL computes every number.**

Ledger arithmetic is deterministic; AI proposes drafts, and financial answers use the actual ledger values:

- Voice/receipt -> AI **draft** -> merchant reviews -> only then `POST /api/events` saves it.
- "Ask Karobaar" -> bounded intent/month guards (model classification only for remaining financial paraphrases) -> existing SQL tool -> **deterministic wording**. A model cannot rewrite the monetary answer.
- Financing provides references and manual checks, not a qualification decision. Unsupported sales/history/receipt thresholds have been removed from the catalogue.

## Tech stack

| Layer | Choice |
|---|---|
| API | FastAPI + Pydantic v2 (OpenAPI at `/docs`) |
| DB | SQLAlchemy 2.0 ORM + SQLite (Postgres-ready via `DATABASE_URL`) |
| AI — first priority | **Groq** — Qwen text/receipt vision and Whisper audio |
| AI — fallback | Optional second **Groq** key, **Gemini** text/vision/audio, optional **OpenRouter** text/vision |
| AI — offline fixture only | **Demo provider** — explicit local test mode; never an automatic fallback or deployed capture provider |

Real-provider chain: `Groq -> optional Groq backup -> Gemini -> optional OpenRouter`.
Speech transcription skips the selected OpenRouter model. Receipt/text processing uses
the same validated extraction contract regardless of provider. Each capability has a
120-second overall deadline; no unlimited key rotation/retry or Demo substitution.
Malformed structured output gets one repair retry; exhausted or unconfigured APIs
return a safe, categorized 503 (service/quota/configuration) or 422 (unusable recognition) and manual-entry guidance, never a fake capture. Whisper detects
the spoken language instead of forcing Urdu. Gemini capture uses nullable structured
fields, corrected image orientation and higher-resolution receipt preparation.
Unknown receipt dates and transfer purposes remain missing for merchant review.
Digital silent WAVs are rejected before paid calls; the browser checks decoded
recordings for empty sound where supported. No automated check proves noisy-room or
dialect accuracy. Capture still needs merchant review; chatbot grammar is bounded.

## Quickstart

```bash
cd Backend
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt

# Put real keys in .env (see .env.example). Without keys, AI capture is unavailable.
uvicorn app.main:app --reload --port 8000
```

- Swagger UI: http://localhost:8000/docs
- Local startup creates an empty database when needed. It no longer inserts sample data.
  Isolated tests explicitly load their own deterministic fixture; existing local data is preserved.

## Configuration (`.env`)

| Variable | Default | Meaning |
|---|---|---|
| `AI_PROVIDER` | `auto` | `auto` \| `groq` \| `gemini` \| `demo` |
| `GROQ_API_KEY` | *(empty)* | Groq key (from console.groq.com) |
| `GROQ_FALLBACK_API_KEY` | *(empty)* | Optional separate Groq key; identical keys are skipped |
| `OPENROUTER_API_KEY` | *(empty)* | Optional server-only text/vision backup |
| `OPENROUTER_MODEL` | `google/gemma-4-26b-a4b-it:free` | Vision/JSON-capable model; free endpoint capacity is not guaranteed |
| `GEMINI_API_KEY` | *(empty)* | Google AI Studio key |
| `GROQ_TEXT_MODEL` | `qwen/qwen3.8-27b` | extraction / remaining question classification; verify provider availability before deploying |
| `GROQ_AUDIO_MODEL` | `whisper-large-v3-turbo` | transcription |
| `GROQ_VISION_MODEL` | `qwen/qwen3.8-27b` | real image extraction; known legacy Compound values migrate to this vision model |
| `GEMINI_MODEL` | `gemini-3.6-flash` | current code default; verify provider availability before deploying |
| `DATABASE_URL` | `sqlite:///./karobaar.db` | any SQLAlchemy URL |
| `UPLOADS_DIR_PATH` | `uploads` | private receipt storage, including `.owners/` metadata; both must persist |
| `RECEIPT_STORAGE` | `local` | cloud deployment requires `vercel_blob`; no filesystem fallback on storage failure |
| `BLOB_STORE_ID` | *(empty)* | connected private Vercel Blob store; cloud uses request-scoped OIDC, not client tokens |
| `CORS_ORIGINS` | `http://localhost:3000,...` | comma-separated frontend origins |
| `AUTO_SEED` | `false` | legacy guard setting; startup no longer seeds data and production requires false |
| `REQUIRE_AUTH` | `false` | set `true` in production to require a verified Supabase access token |
| `SUPABASE_URL` | *(empty)* | Supabase project URL used to validate token issuer/JWKS |
| `SUPABASE_JWT_SECRET` | *(empty)* | legacy HS256 signing secret; keep server-side only |

## API

All routes are under `/api`. Canonical endpoints use **integer paisa**
(1 PKR = 100 paisa) plus ready-to-render `*_display` strings. The frontend bridge accepts decimal PKR, validates at most two decimal places and converts once to integer paisa through the same confirmation service.

| Method & Path | Purpose |
|---|---|
| `GET /api/health` | Cheap liveness/configuration only; `?verify=true` returns 403, with no paid call |
| `POST /api/capture/transcribe` | Audio (multipart) -> transcript (Whisper) |
| `POST /api/capture/extract` | Transcript/text -> reviewable draft event (nothing saved) |
| `POST /api/capture/extract-receipt` | Receipt photo (multipart, max 4 MB) -> draft + private evidence; local owner registry or cloud Blob |
| `POST /api/events` | **Confirm** a draft/manual event into the ledger |
| `GET /api/events` | List with filters: `event_type, customer_id, payment_status, source_type, from, to, limit, offset` |
| `GET /api/events/{id}` / `PATCH` / `DELETE` | Read / edit amount-date-notes / remove |
| `GET /api/customers` / `GET /api/customers/{id}` | Udhaar book (biggest debtor first) / full statement |
| `GET /api/dashboard` | One call for the whole home screen |
| `GET /api/ask/suggestions` | Starter questions + supported tools |
| `POST /api/ask` | Ask Karobaar (guarded interpretation -> SQL tool -> deterministic answer); question length 2–500 after trimming |
| `GET /api/evidence/passport` | Financial Evidence Passport |
| `GET /api/evidence/files/{filename}` | Upload-owner + confirmed-attachment checks; generic 404 on unauthorized or missing files |
| `GET /api/financing/programs` | Five Pakistani financing reference links; numerical loan terms are not asserted |
| `GET /api/financing/readiness` | `reference_only`, no matched/missing numerical thresholds; manual topics to confirm |
| `GET /api/combined` | Shared product snapshot: summary, latest 200 entries, full-history customers, dashboard, passport and source counts |
| `POST /api/ledger/events` | Typed frontend confirmation bridge; decimal PKR → canonical paisa |
| `POST /api/reminders/draft` | AI-drafted payment reminder (merchant edits & sends) |
| Former `/api/demo/seed` / `/api/demo/reset` | Removed; return 404 without changing records |

Error envelope: `{"error": {"type": "not_found" | "validation_error" | "ai_unavailable" | ..., "message": "..."}}`
with status 404 / 422 / 503.

AI failures also include a safe `reason` such as `rate_limit`, `busy`, `timeout`, `configuration` or `invalid_output`. Provider bodies and keys never appear in public messages. Receipt bytes are decoded and format-checked before storage/recognition; corrupt photos get a file-specific 422. JPEG, PNG and WebP are supported; HEIC requires export to JPEG first.

## Deterministic domain rules

- **Money** is stored and computed as integer paisa. Canonical APIs use paisa; the product bridge uses validated decimal PKR. Browser display values are not the accounting authority.
- **FIFO udhaar settlement** — `recompute_customer_settlement()` replays every confirmed
  payment against that customer's credit sales oldest-first. Create/update/delete all
  funnel through it. A "mark paid" button does not exist:
  the merchant records a `payment_received` event instead.
- **Only confirmed events** count in every metric, passport figure, and Ask answer.
- **Duplicates** are flagged (same type + customer + amount + date) before saving.
- **PKT timezone** (UTC+5) drives every "today", month bucket, and overdue decision
  (30 or more days unpaid = overdue).
- **Ask Karobaar tools** are SQL-backed (`total_outstanding`, `top_debtor`,
  `monthly_sales`, `sales_comparison`, `customer_outstanding`). Recognized English/Roman Urdu/Urdu questions use rules; remaining debt paraphrases can use a strictly validated classifier. Invalid/future months are not silently changed to this month. Sales comparisons mean one calendar month versus its immediate predecessor; balances are current/all-time. Unknown customers, unsupported periods and unsupported tools get clarification, not a guessed amount. `answer_source=deterministic_ledger` identifies the bounded renderer; unsupported replies contain no ledger amount.
- The **Passport** reports qualitative labels (recovery pattern, revenue consistency,
  customer concentration) — explicitly not a credit score.

## Project structure

```
Backend/
├── app/
│   ├── main.py            # FastAPI app, lifespan, CORS, error handlers
│   ├── config.py          # env settings + provider chain resolution
│   ├── db.py              # engine, sessions, PKT/month helpers
│   ├── models.py          # Customer, BusinessEvent (integer paisa)
│   ├── errors.py          # domain errors -> HTTP mapping
│   ├── schemas/           # Pydantic contracts (single source of response truth)
│   ├── ai/                # base protocol, prompts, Groq, Gemini, Demo, FallbackAdapter
│   ├── services/          # money, ledger (FIFO), metrics, passport, matching, ask_engine
│   ├── routers/           # health, capture, events, customers, dashboard, ask,
│   │                      # evidence, financing, reminders, demo
│   └── data/              # financing_programs.json + deterministic seed
├── tests/                 # money, FIFO, events/capture/ask/dashboard/financing APIs
├── scripts/eval_extractor.py  # sample-utterance accuracy harness
├── requirements.txt
└── render.yaml            # one-click Render deployment
```

## Testing

```bash
pytest            # 259 tests; offline (explicit fixtures, isolated SQLite, mocked Blob)
python scripts/eval_extractor.py   # extraction accuracy against the live chain
python -m scripts.check_providers  # explicit paid checks; prints no raw provider errors
python -m scripts.release_preflight --database # read-only TLS/RLS/grants inspection
python -m scripts.release_preflight --providers # bounded paid text extraction checks
```

Tests pin the seed dataset's designed outcomes: total outstanding **Rs 100,000**,
top debtor **Ahmed Rs 58,500** (oldest unpaid 45 days = overdue), credit sales
**Rs 198,000**, recovered **Rs 98,000 (~49.5%)**.

The current suite covers ledger precision/provenance, >200-row balances, bounded question tools, upload ownership, evidence claims, safe diagnostics, receipt-byte validation, backup routing/deadlines and overlapping requests with a one-connection pool. All 259 cases pass. Both original real image providers and the additional Groq key passed synthetic receipt checks. OpenRouter's key is valid but its tested free endpoints returned 429; do not count it as proven available capacity. Offline checks do not establish live account isolation or real microphone/Urdu-photo accuracy. See the [implementation ledger](../docs/REGIONAL_ROUND_IMPLEMENTATION_LEDGER.md) for separate hosted evidence.

## Receipt ownership and existing files

In local mode, both upload routes record the merchant in private `uploads/.owners/<filename>.json` before returning a draft. In cloud mode, the server creates an immutable `receipts/<sha256 merchant>/<uuid filename>` namespace in private Vercel Blob. Both confirmation routes check ownership **before any customer/event write**. Reading also requires that owner's confirmed ledger attachment. A guessed or copied filename is not proof of ownership. Browser requests never choose a Blob URL or storage token.

Unregistered legacy images are preserved, but reads/new attachments fail closed. An operator must verify the original uploader from trusted records, then explicitly register one file:

```powershell
python -m scripts.register_evidence_owner --filename ORIGINAL_UUID.png --merchant-id VERIFIED_USER_UUID
# Dry-run by default. Only after checking ownership:
python -m scripts.register_evidence_owner --filename ORIGINAL_UUID.png --merchant-id VERIFIED_USER_UUID --apply
```

This local-only operation never overwrites a registered owner or changes ledger rows. Back up images **together with `.owners`**; do not expose the directory as static public files. Legacy local images are not automatically migrated to Blob. Upload signature validation and general orphan cleanup remain tracked work.

## Deployment

The active repository-root `vercel.json` defines Next.js and FastAPI services under one domain; Python is pinned to 3.12. See the [Vercel deployment plan](../docs/VERCEL_DEPLOYMENT_PLAN.md) for current configuration and remaining release gates. Vercel/production startup rejects authentication-off, SQLite, auto-seeding or local-receipt settings. It never creates/seeds remote tables. The existing Supabase schema must already be provisioned.

SQLAlchemy is pinned to the verified 2.0.52 release to match psycopg2. Do not casually replace this with an unbounded range: SQLAlchemy 2.1 changes the default PostgreSQL driver, and that mismatch caused a real hosted startup failure despite a successful build.

Synchronous database endpoints run in worker threads. Async capture/Ask routes offload their SQL phase; reminder and receipt-download routes release read transactions before waiting for AI/storage. This prevents overlapping requests from blocking the event loop and starving the small cloud pool. Thirteen focused regressions cover overlapping reads, both reminder paths and receipt-download connection release; they are not a large-scale load test.

Cloud Postgres verifies certificates using Supabase's public CA from Database Settings (not a credential), a bounded connection timeout, and a one-connection pool. The read-only preflight confirmed TLS, both tables' RLS, no browser-access policies, and zero visible rows for anon/authenticated roles. The current backend DB role bypasses RLS; replace it with a least-privilege role in follow-up work. No remote policies or records were changed.

Cloud snapshots skip the process-local cache. API responses use `private, no-store`; AI failure responses do not echo provider internals. Voice/receipt uploads are capped at 4 MB to leave multipart headroom below Vercel's request limit. Actual hosted upload sizes and Blob OIDC/persistence still need end-to-end checks. The installed Python dependency audit is clean after PyJWT/urllib3 patches; that is not an overall security certification.

`render.yaml` is an older reference blueprint, not a release-ready alternative: its development SQLite/auto-seed assumptions must not be used for public merchant data. This release targets Vercel; do not deploy that blueprint unchanged. Keep the verified [local booth fallback](../docs/REGIONAL_DEMO_RUNBOOK.md).

## Phase 2 financing — local branch, 23 October 2026

`app/data/financing_catalog_v2.json` contains five official-source references, their review dates, published terms, checkable preparation requirements and lender-only conditions. Unknown product amounts/deadlines stay unknown. This is a reviewed snapshot, not a live lender feed. The old `/financing/programs` and `/financing/readiness` contracts are retained for the evidence passport; new comparisons use only v2.

| Endpoint | Access / behavior |
| --- | --- |
| `GET /api/financing/catalog` | Public facts, freshness flag and a countdown only if a sourced closing date exists |
| `GET /api/financing/catalog/schema` | Public JSON schema for a future proposal workflow; not a write endpoint |
| `POST /api/financing/assessment` | Authenticated; typed applicant declarations → deterministic preparation checks; no DB/profile write |
| `POST /api/financing/questions` | Authenticated; `{question, program_id?, profile?, use_ai?}` → cited facts, optional constrained LLM selection |

Preparation percent is declared matching checks divided by the listed checkable checks, with lender-only checks excluded and still visibly unresolved. It is not approval probability or complete bank eligibility. No sales floor, ledger-history business age or receivables-based debt-burden rule is inferred. Applicant payloads exclude identity numbers and accounts; profiles and ledger figures are not placed into the AI selection payload. The user's typed question is still sent when they enable AI assist, so they should not type private identifiers there.

The existing `/api/ask` now routes financing questions to cited catalogue retrieval before ledger classification. Its five accounting tools are unchanged. Optional AI selection reuses the configured provider chain and existing low-temperature prompts, with a 15-second total selection deadline. Only whitelisted fact IDs can reach the answer; invalid IDs, omitted compared programs, unavailable APIs or timeout fall back to reviewed facts. Raw model prose never becomes a loan term or decision.

Validate a proposed snapshot locally:

```powershell
python scripts/validate_financing_catalog.py
python scripts/validate_financing_catalog.py path/to/proposed-catalogue.json
python -m pytest tests/test_phase2_financing.py -q
```

Validation checks schema/provenance, not whether a bank's published text is true or intake remains open. A future n8n workflow should collect proposals, then require human source review, validation, tests and an approved deployment. No scraper, schedule, hosted n8n, remote write API or auto-publishing was added. Details and known limits: [Phase 2 ledger](../docs/PHASE_2.md).
