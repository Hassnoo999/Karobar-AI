# Karobaar AI

**Voice-first financial evidence and decision support for Pakistan's informal merchants.**

![Karobaar AI](frontend/public/karobar-ai-logo.svg)

Karobaar turns a merchant's voice notes and receipt photos into a reviewable financial draft. Nothing reaches the ledger until the merchant confirms it. Once confirmed, deterministic ledger logic—not an LLM—computes sales, expenses, udhaar, recoveries, evidence quality, and financing-readiness signals.

Built for the Alibaba Cloud AI Hackathon Pakistan 2026, Financial Inclusion track.

## What we built

| Capability | Working implementation |
|---|---|
| Voice and receipt capture | AI produces a structured draft for merchant review |
| Trusted ledger | Sales, expenses, udhaar and repayments enter only after confirmation |
| Business dashboard | Deterministic monthly totals, receivables and recovery figures |
| Ask Karobaar | Five supported questions retrieve answers from ledger-backed tools |
| Evidence Passport | Qualitative business evidence with clear gaps and no invented score |
| Financing readiness | Five source-backed Pakistani programs with matched and missing requirements |
| Reminder action | An editable, ready-to-copy udhaar reminder using the real customer balance |

The complete application runs in deterministic demo mode without external AI credentials, while Groq and Gemini adapters support real voice, text and receipt extraction when configured.

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

Many viable micro-businesses already have rich commercial activity, but it lives in memory, paper receipts, and chat threads. Karobaar helps a merchant build a trustworthy financial history without pretending to make a lending decision.

> **AI captures and explains. SQL computes every number.**

## Demo flow

1. Record a sale, expense, udhaar entry, or repayment by voice—or upload a receipt.
2. Review the extracted draft and explicitly confirm it.
3. See deterministic dashboard and ledger totals.
4. Ask a natural-language question such as “Total udhaar kitna hai?”
5. Review a qualitative Financial Evidence Passport and source-backed financing next steps.
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
      +--> SQLAlchemy ledger (SQLite locally, PostgreSQL-ready)
                  |
                  +--> deterministic metrics, Ask tools, passport, readiness
```

## Run locally

Requirements: **Node.js 22+** and **Python 3.12+**.

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
- Every customer, event, dashboard, receipt, and question is merchant-scoped.
- Receipt files are served through an authenticated ownership check.
- Monetary values are stored as integer paisa; confirmed entries drive all metrics.
- Credit repayments settle oldest outstanding sales first (FIFO).
- Financing results distinguish matched evidence, missing evidence, and requirements that need manual verification.
- Reminder messages remain drafts on screen.

## Repository

- [`frontend/`](frontend/) — Next.js 16, React 19, Tailwind, Supabase Auth
- [`Backend/`](Backend/) — FastAPI, SQLAlchemy, AI adapters, tests, deployment blueprint
- [`frontend/README.md`](frontend/README.md) — frontend setup, routes and authentication behavior
- [`Backend/README.md`](Backend/README.md) — full API contracts, domain rules, configuration, and test commands
- [`docs/`](docs/) — presentation and GitHub showcase screenshots

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

- 74 backend tests pass.
- The Next.js production build passes.
- The production dependency audit reports zero vulnerabilities.
- Desktop and mobile journeys pass from dashboard through ledger, Ask Karobaar and Evidence Passport.

## Scope boundary

Karobaar organizes merchant-confirmed evidence and compares it with published financing requirements. The financing institution still verifies identity, documents, collateral and final eligibility. The hackathon version does not provide underwriting, a credit score, automatic WhatsApp/SMS delivery, inventory management or banking integrations.
