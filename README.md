# Karobaar AI

**Voice-first financial evidence and decision support for Pakistan's informal merchants.**

![Karobaar AI](frontend/public/karobar-ai-logo.svg)

Karobaar turns a merchant's voice notes and receipt photos into a reviewable financial draft. Nothing reaches the ledger until the merchant confirms it. Once confirmed, deterministic ledger logic—not an LLM—computes sales, expenses, udhaar, recoveries and evidence metrics. Manual entry provides a practical fallback when capture is unavailable.

Built for the Alibaba Cloud AI Hackathon Pakistan 2026, Financial Inclusion track.

## What we built

| Capability | Working implementation |
|---|---|
| Voice and receipt capture | AI produces a structured draft for merchant review |
| Confirmed ledger | Sales, expenses, udhaar and repayments enter only after confirmation; searchable transactions and full-history customer balances |
| Business dashboard | Clearly scoped monthly totals, recorded-month trend, receivables and recovery figures |
| Ask Karobaar | Five read-only ledger tools; guarded intent/month selection, deterministic answers, visible period and interpretation labels |
| Evidence Passport | Recorded evidence metrics with clear gaps and no invented score |
| Financing references | Five official reference links and manual next steps; no invented sales/history/receipt qualification thresholds |
| Reminder action | An editable, ready-to-copy udhaar reminder using the real customer balance |

The application can be explored in deterministic demo mode without external AI credentials. Demo audio transcription is canned and demo receipt extraction requires manual completion—it is not live recognition. Groq handles live text/audio, with Gemini providing the receipt path when configured. Sample data and Demo AI responses are visibly labeled.

## Product preview

![Karobaar AI dashboard](docs/screenshots/dashboard.png)

<details>
<summary>More product screenshots</summary>

### Ask Karobaar

![Ask Karobaar](docs/screenshots/ask-karobaar.png)

### Financial Evidence Passport

![Financial Evidence Passport](docs/screenshots/evidence-passport.png)

</details>

The submission deck is available at [`docs/Karobaar_AI_Hackathon_Presentation.pptx`](docs/Karobaar_AI_Hackathon_Presentation.pptx).

## Why it matters

Many micro-businesses have rich commercial activity, but it lives in memory, paper receipts, and chat threads. Karobaar helps a merchant build a reviewable business history without pretending to make a lending decision.

> **AI proposes a draft. The merchant confirms it. The ledger computes the totals.**

## Demo flow

1. Record a sale, expense, udhaar entry, or repayment by voice, receipt or manual entry.
2. Review the extracted draft and explicitly confirm it.
3. See deterministic dashboard and ledger totals.
4. Ask a natural-language question such as “Total udhaar kitna hai?”
5. Review the Financial Evidence Passport, evidence gaps and official financing reference links.
6. Draft a payment reminder; the merchant chooses whether and where to send it.

Karobaar does **not** calculate a credit score, approve a loan, or send WhatsApp/SMS messages automatically.

## Architecture

```text
Next.js web app
      |
      v
FastAPI API + verified Supabase identity
      |
      +--> AI adapter (Groq -> Gemini -> deterministic demo fallback)
      |
      +--> SQLAlchemy ledger (SQLite locally, Supabase PostgreSQL in cloud)
      +--> Private receipts (local owner registry / merchant-scoped Vercel Blob)
                  |
                  +--> deterministic metrics, Ask tools, passport, readiness
```

## Run locally

Requirements: **Node.js 22.x** and **Python 3.12+**.

### 1. Backend

```powershell
cd Backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload --port 8000
```

With no AI keys, the deterministic demo provider keeps the full flow runnable. API docs are at `http://localhost:8000/docs`.

### 2. Frontend

In a second terminal:

```powershell
cd frontend
npm ci
Copy-Item .env.local.example .env.local
npm run dev
```

Open `http://localhost:3000`.

For the local single-shop demo, leave both Supabase frontend values empty and keep `REQUIRE_AUTH=false` in the backend. For every shared deployment, configure Supabase on both sides and set `REQUIRE_AUTH=true`.

## Safety and trust boundaries

- Supabase access tokens are signature-, issuer-, audience-, and expiry-verified in production mode.
- Ledger/customer queries are merchant-scoped; actual deployed two-user isolation and database access policies still need verification.
- Receipt ownership is recorded at upload, then checked before attachment and reading. Local files use a private owner registry; cloud files use a server-selected merchant namespace in private Vercel Blob. Claiming another merchant's filename cannot establish ownership. Actual cloud Blob/OIDC behavior still needs deployment verification.
- Cloud startup requires authentication, managed PostgreSQL, no automatic seeding and private Blob storage. Cloud seed/reset controls are blocked, API responses are private/non-cacheable, and process-local snapshots are disabled. Uploads are capped at 4 MB.
- Cloud database connections verify the server certificate. The original Supabase tables have RLS enabled with no browser-access policies; read-only anonymous/authenticated role checks returned no rows. The backend's database role bypasses RLS, so API merchant filtering remains essential; a least-privilege role is follow-up work.
- Monetary values are stored as integer paisa; confirmed entries drive all metrics.
- Credit repayments settle oldest outstanding sales first (FIFO).
- Financing references do not establish eligibility. Unsupported numeric qualification rules have been removed; recorded history is not verified business age.
- Ask answers render the actual tool values without a model rewriting financial amounts. Invalid periods and unsupported requests get clarification instead of nearby totals; this is not a promise to understand every possible phrasing.
- Public health checks do not make paid model calls. Active provider checks are an explicit backend-operator command.
- Reminder messages remain drafts on screen.

## Repository

- [`frontend/`](frontend/) — Next.js 16, React 19, Tailwind, Supabase Auth
- [`Backend/`](Backend/) — FastAPI, SQLAlchemy, AI adapters, tests, deployment blueprint
- [`frontend/README.md`](frontend/README.md) — frontend setup, routes and authentication behavior
- [`Backend/README.md`](Backend/README.md) — full API contracts, domain rules, configuration, and test commands
- [`docs/`](docs/) — presentation and GitHub showcase screenshots
- [Vercel deployment plan](docs/VERCEL_DEPLOYMENT_PLAN.md) — how to host both apps together, with the remaining release gates clearly marked

## Verification

```powershell
cd Backend
.venv\Scripts\python.exe -m pytest -q

cd ..\frontend
npm run build
npm audit --omit=dev
```

The repository intentionally excludes local databases, uploads, environment secrets, virtual environments, build output, and source archives. Never commit `.env`, `.env.local`, `karobaar.db`, or uploaded receipts.

## Current verification

- 195 backend tests pass, including product-boundary, chatbot, local/cloud upload ownership, release guards and evidence-claim regressions.
- The Next.js production build passes.
- The frontend production dependency audit and installed Python dependency audit report zero known vulnerabilities after compatible patches. Eight frontend development-tool findings remain tracked. These audits are not a security guarantee.
- 15 desktop/tablet/mobile product-route checks and a 27-check browser story pass in an isolated local demo.

Verified on 10 October 2026. The story covers confirm-once, credit/repayment, refreshed balances, named-month and Urdu customer questions, invalid/unsupported requests, editable reminder copy, filters/CSV and honest failure recovery. The original 26-question audit passes 26/26 (previously 12/26). Gemini correctly extracted a PKR 5,000 credit sale from text and a synthetic English receipt; Groq text requests were rate-limited (429). Real microphone/Urdu photo quality, deployed sessions, two-user API isolation and cloud persistence remain release gates. See the [implementation ledger](docs/REGIONAL_ROUND_IMPLEMENTATION_LEDGER.md) and [booth runbook](docs/REGIONAL_DEMO_RUNBOOK.md). The submission deck still reflects the earlier UI and is scheduled for the next presentation checkpoint.

## Scope boundary

Karobaar organizes merchant-confirmed evidence and offers financing reference links. The institution still verifies identity, documents, collateral and final eligibility. The hackathon version does not provide underwriting, a credit score, automatic WhatsApp/SMS delivery, inventory management or banking integrations.
