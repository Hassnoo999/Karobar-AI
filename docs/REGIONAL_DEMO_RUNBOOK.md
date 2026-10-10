# Regional booth demo

Updated 10 October 2026. This is a rehearsal guide for the working prototype, not a production-release sign-off.

## What to open now

The team's local frontend is running at <http://127.0.0.1:3001/dashboard>; the API is at <http://127.0.0.1:8001/api/health> and API documentation at <http://127.0.0.1:8001/docs>.

The current live-test backend uses its own `tmp/regional-audit/run2-live.db` and upload folder outside the repository. Authentication is disabled only in this loopback process. It retains your team's test entries; do not reset it during rehearsal. Your original environment files and PostgreSQL data were not changed. These localhost links work on this computer, not on a judge's phone.

## One story, three people, about 90 seconds

| Person | Show | Say, in your own words |
|---|---|---|
| 1: problem and user | Dashboard | “A small merchant may know the business is active, but the records are scattered across memory, receipts and conversations. Karobaar helps turn those records into a reviewable financial history.” |
| 2: operator | Record → review → confirm | “Let’s record a PKR 5,000 credit sale to Naveed. AI can propose a draft, but nothing is saved until the merchant reviews and confirms it.” |
| 2: operator | Record repayment → ledger → Ask | “Naveed pays PKR 2,000 back. This is a repayment, not another sale. His remaining balance is PKR 3,000. Ask Karobaar gets that amount from the confirmed ledger.” |
| 3: technology and boundary | Evidence & readiness → reminder | “The same records support visible evidence metrics and an editable payment reminder. The financing links are references, not approval or a credit score. AI assists capture; deterministic code computes the totals.” |

Before starting, check that Naveed has no previous entries. If he does, choose a fresh demo customer and use that same name throughout. Do not delete existing entries just to make the story look clean. With an existing customer, narrate the opening balance plus PKR 3,000 instead of claiming the final balance is necessarily PKR 3,000. The total receivable balance should increase by PKR 3,000 from its opening value; PKR 103,000 is only correct when starting from the untouched PKR 100,000 seed.

Use the actual recording/OCR only after testing it on the presentation laptop. Manual entry goes through the same confirmation and accounting rules and is an honest fallback—not a demonstration of speech recognition.

## Useful live questions

- `Total udhaar kitna hai?` — current outstanding balance across confirmed history.
- `Naveed ka udhaar kitna hai?` — that customer's current balance.
- `August 2026 ki sales kitni thi?` — the named month's sales, not the current month.
- `Compare September 2026 and August 2026 sales` — adjacent-month comparison.
- `How much profit this month?` — intentionally unsupported; show the clear boundary instead of an invented answer.

The supported tools are total outstanding, top debtor, customer outstanding, monthly sales and adjacent-month sales comparison. Expense/profit questions, daily/range reports and historical customer balances are not added in this release. Urdu/Roman Urdu support is tested for common phrases, not every spelling or dialect.

## Five-minute preflight

Use short voice notes and receipts below **4 MB**. Gemini passed one text and one synthetic English receipt probe on 10 October; Groq text was rate-limited. These are limited capability checks, not proof of real microphone/Urdu handwriting quality. The cloud release is not signed off until auth, private receipts and saved-data persistence pass on the actual URL.

1. Open the dashboard, check the API connection and note the opening receivables. Verify whether the visible rows are seed/sample entries.
2. Test one short voice note and one small receipt; review the provider label and draft. A Demo AI response is not live recognition. Never confirm a missing/incorrect amount just to finish a demo.
3. Use a fresh test customer for the PKR 5,000 → PKR 2,000 → PKR 3,000 story; confirm the ledger, dashboard, Ask and reminder agree.
4. Check microphone permission, readable browser zoom, clipboard, laptop charger and the presentation file. Close secret/configuration tabs before sharing the screen.
5. Rehearse once with all three people. One person speaks while the operator clicks; avoid three separate introductions.

## Recovery without misrepresenting the product

- Microphone or recognition fails: use Manual, label the fallback and continue the same ledger story.
- Backend fails: the app shows a connection error. Choose the explicit read-only sample preview or use saved screenshots; say which one you are showing. It does not prove deployed writes or live AI.
- Chat wording is unsupported: choose a supported example; explain that the assistant is deliberately bounded rather than claiming general financial intelligence.
- Receipt cannot load: do not show another merchant's evidence or remove ownership checks. Use a pre-checked receipt or switch to voice/manual capture.
- Internet fails: retain the local laptop demo and the downloadable presentation. Do not make a public QR link the only demonstration path.

## What is proven, and what is still pending

Current local checks: 165 backend tests, 26/26 original question-audit cases, 27 browser-story checks, 15 responsive route checks, TypeScript and production build pass. Test data was isolated from your team's live-test ledger.

Still pending before a public demo: real Supabase sign-in and two-account isolation, exposed-database policies, live voice/OCR verification, durable cloud receipts and ownership, cloud upload-size handling, and save/read/reload across a deployment restart. The earlier submission deck still needs the regional screenshots/narrative update. See the [implementation ledger](REGIONAL_ROUND_IMPLEMENTATION_LEDGER.md) and [Vercel deployment plan](VERCEL_DEPLOYMENT_PLAN.md).

## Restarting the local test setup if needed

Do not start duplicate servers if ports 3001 and 8001 already respond. Use Node 22.x and the existing backend virtual environment. These commands are run from the repository root and override settings only in their terminal processes; they do not edit private environment files.

Backend terminal:

```powershell
$repoPath = (Get-Location).Path
$auditPath = Join-Path (Split-Path $repoPath -Parent) 'tmp/regional-audit'
New-Item -ItemType Directory -Force -Path $auditPath | Out-Null
$env:DATABASE_URL = 'sqlite:///' + ((Join-Path $auditPath 'run2-live.db') -replace '\\', '/')
$env:UPLOADS_DIR_PATH = Join-Path $auditPath 'run2-live-uploads'
$env:REQUIRE_AUTH = 'false'
$env:ENVIRONMENT = 'development'
$env:AUTO_SEED = 'true'
$env:CORS_ORIGINS = 'http://127.0.0.1:3001,http://localhost:3001'
Set-Location Backend
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --reload-dir app --host 127.0.0.1 --port 8001
```

Frontend terminal:

```powershell
$env:NEXT_PUBLIC_SUPABASE_URL = ''
$env:NEXT_PUBLIC_SUPABASE_ANON_KEY = ''
$env:NEXT_PUBLIC_API_BASE_URL = 'http://127.0.0.1:8001/api'
Set-Location frontend
npm run dev -- --hostname 127.0.0.1 --port 3001
```

Do not reuse these authentication-off settings in Vercel or any shared/public deployment.
