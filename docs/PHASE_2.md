# Phase 2 — final-round financing workspace

Started: 23 October 2026 (PKT). Final round: 24 October, Pak-China Friendship Centre, per the team. Baseline: `036dcc9`; local branch: `phase-2`. Main and the deployed release remain the fallback. No push, merge, Vercel changes, credential changes or production-data writes are authorized for this phase before a reviewed checkpoint.

## Outcome and time budget

Give a merchant a credible next step after building a ledger: explore five researched financing references, compare published checks with their own declared details, and ask a question with visible sources. Retain the existing Next.js/FastAPI/provider architecture and deterministic accounting. Budget: two runs, five to six hours total. Estimates below are timeboxes, not guarantees.

| Checkpoint | Timebox | State / acceptance gate |
| --- | --- | --- |
| P2.0 Audit context, pitch/videos, current code and sources | 45 min | Complete for this scope; HTML copy/visual preview, both videos' metadata/sampled frames, Claude fork mismatch and official sources reviewed. Audio not fully transcribed. |
| P2.1 Versioned, validated five-program catalogue and assessments | 65 min | Complete locally; dated sources, typed checks, honest unknowns, no invented sales rules or DB migration |
| P2.2 Financing dashboard and comparison dialog | 75 min | Complete locally; CSS depth/motion, native modal, live ledger context, search/filter, labelled preparation progress; desktop/mobile inspected |
| P2.3 Source-grounded scheme Q&A | 60 min | Complete locally; curated retrieval + optional LLM fact selection, citations, multilingual question matching, provider timeout/source fallback |
| P2.4 Focused tests, build and local walkthrough | 45 min | Local checkpoint passed; 326 backend tests, 5 frontend receipt tests, TypeScript and production build; details below |
| Run 2: user review, bounded fixes and rehearsal | 40–70 min | Reserved; no new architecture/features; deployment needs separate approval |

## Decisions and reasons

1. Claude inspected `Moezulhaq24/Karobar-AI`, an older fork, rather than this current published repository. Its demo-fallback and unsourced-threshold findings describe a stale baseline. Current production fallback rejects unavailable AI rather than generating a fake capture, and the five financing references currently contain manual checks only.
2. Build a separate `/financing` workspace without replacing the evidence passport, ledger or existing financial Ask tools. Both passport and financing link to the same merchant-scoped confirmed data. No unrelated cleanup, provider migration or Alibaba badge is part of tonight's change.
3. Use official sources reviewed on 23 October. A page being accessible does not prove a lender is accepting applications today. Store availability, deadline and missing facts explicitly; show no invented closing date or days-left countdown. Keep the official application route external, with lender confirmation.
4. Progress means preparation items supplied, never approval probability. Applicant facts are user-declared, not bank-verified. Ledger history is not business age, receivables are not debt obligations, attachments are not authenticated statements, and expenses do not establish affordability. Do not introduce a sales floor or receipt-coverage qualification rule without a published source.
5. Curated retrieval is sufficient for five programs. Retrieve topic-specific facts with source/date metadata; keep comparisons and personal-check numbers deterministic. Reuse the existing provider chain only to select allowed fact IDs, not generate financial prose. Retain cited facts if it is unavailable. No vector database, embeddings service, new AI SDK stack or chat-driven ledger writes.
6. Catalogue data gets a strict schema and a local validation workflow so a future n8n job can propose updates. Scraping, scheduled execution, hosting, automatic publishing and unaudited web text entering model instructions are out of scope. Reviewed snapshots remain the source of truth.
7. Use only an isolated local SQLite workspace for realistic synthetic vendor examples. Clearly label sample records/profile inputs; do not restore the removed public demo-login pipeline or inject fixtures into production accounts.

## Research and audit notes

- PM Youth: official portal lists resident Pakistani applicants, general age 21–45 (IT/e-commerce exception starts at 18), tiered amounts/rates. Source: https://pmybals.pmyp.gov.pk/ . Detailed bank/security conditions remain separate.
- Akhuwat: official process describes applicant checks and guarantors. The main product page is JavaScript-only to the research tool; do not invent a loan amount from an unverified secondary site. Source: https://donate.akhuwat.org.pk/programs/loan/process . Resolve product-specific amount before adding any numeric cap.
- BOP: source https://www.bop.com.pk/view.aspx?id=3415 . Existing-customer relationship and invitation are essential, not merely strong ledger sales.
- HBL: source https://www.hbl.com/business/sme-banking/sme-banking/hbl-small-business-finance . Published business operation age must not be compared with the ledger's calendar span.
- Meezan: source https://www.meezanbank.com/sme-banking/ . I-SAAF product text distinguishes existing borrowers/relationships; retain that ambiguity for bank confirmation rather than relaxing the rule.
- Regional HTML has stale proof/technology copy: 74 tests, demo fallback, “every entry voice verified,” “5 programs matched,” and “0 vulnerabilities.” These are not current claims. Record replacements for the final pitch, but do not rewrite the deck or videos without a separate content-edit step.

## Verification record

### Measured local results — 23 October 2026

- Backend final run: **326 passed in 16.54 seconds**, command `python -m pytest -o addopts='' -q`. Includes 54 new Phase 2 cases. The preceding 324-case full run also passed before two additional question phrasings were added.
- Frontend: TypeScript passed; final Next.js 16.3.8 webpack production build passed, including `/financing`. The existing five receipt-review tests passed. No package was added to the app and no lockfile changed.
- Catalogue validator accepted schema v2 / version `2026-10-23.1`, five programs. It changes no files and publishes nothing. Tests reject deceptive/unsafe source URLs, missing citations, duplicate IDs, unsourced deadlines, wrong profile types, invalid rules and stale/future snapshots.
- Actual provider-backed local request, “Compare PM Youth and BOP loan amounts,” returned `ai_assisted_retrieval` with two official citations in about eight seconds. A browser deadline question exercised `source_fallback` with useful cited facts, not a fabricated date. This proves one live AI selection, not every provider's capacity or future availability.
- Browser story: unknown applicant → declared profile → PM Youth/Meezan green preparation, BOP 50% and HBL 60%; BOP eight months showed a four-month gap; twelve months plus invitation changed it to 100%, while lender checks remained. HBL actual operation age and statement coverage were separate declarations, never inferred from ledger dates.
- Native details and applicant dialogs opened; editing retained declared values; Escape dismissed; the blurred backdrop and current facts/check columns were inspected. Search for HBL, complete-only filtering and account/page-memory reset behavior were checked. Changing declarations cleared the old Q&A result before a new answer could appear current.
- Main Ask answered the HBL operating-age question with citations, then returned **Rs 100,000** synthetic udhaar via the unchanged deterministic ledger tool. Browser console error/warning check at that point returned none.
- Responsive check used a temporary 390×844 viewport (375 CSS pixels available after scrollbar); document scroll width equaled client width. Mobile navigation and the long applicant dialog were inspected, with no horizontal clipping. The viewport was reset afterward. Reduced-motion behavior is provided by the existing global CSS rule; no OS preference was changed for this check.
- Final running code's HTTP checks confirmed catalogue version/freshness, five programs, BOP 50% preparation and the sourced PKR 9,500 fee response. `git diff --check` passed (normal Windows LF/CRLF notices only). Main and cached `origin/main` still point to `036dcc9`; no commit, push, merge or deployment was performed.

### Failures found and how they were handled

The first new test pass found a plural “rates” retrieval miss, which was fixed, and an absent pytest-asyncio dependency. Async tests now use the standard `asyncio.run` instead of adding a package. An old unsupported-loan assertion was replaced by a more precise guard: ask which scheme, return no eligibility decision and no unrelated ledger number.

One later full run had **323 pass / 1 fail** in the pre-existing 250-millisecond one-connection stress test (`/api/events`). No Phase 2 endpoint was involved. All 13 concurrency tests passed on immediate focused rerun (2.95 seconds), followed by clean full runs of 324 and 326. No timeout was relaxed and no accounting/database code was changed to mask it. Treat this as an intermittent timing limit to investigate after the finale, not a large-scale performance certification.

The UI review caught a dialog remount/open race, corrected it, and then verified repeated edit/open behavior. A data-flow check also caught an incorrect “all recorded history” sales label: the shared totals are current-month figures, so the new page now labels both sales and expenses accordingly. Profile changes invalidate question results to avoid stale comparisons.

### Local review workspace

Frontend: `http://127.0.0.1:3001/financing`. Backend: `http://127.0.0.1:8001`. Both listen only on loopback. The frontend is serving the verified production build with a local API address; these ignored local build files are not a cloud release.

Database: `../../tmp/phase2-review/phase2-vendor-20261023.sqlite3`, relative to the repository root. It was created only after an exact-path/new-file guard, then loaded with 63 explicitly labelled synthetic records and five synthetic customers. No old local database, Supabase row or real account was seeded/reset. The fixture has no receipt attachments, so its evidence coverage is honestly 0%. Do not present sample records/declarations as real merchant evidence.

Screenshots outside Git: `../../tmp/phase2-review/phase2-financing-overview.png` and `../../tmp/phase2-review/phase2-financing-comparison.png`. Temporary video frame montages and ffmpeg tooling also remain outside the repository. The original HTML/MP4 files were not edited.

## What changed, in plain language

### 1. A proper financing workspace

Financing now has its own navigation item and a dedicated page, instead of being only a small reference list. It uses the app's existing forest/mint look, lightweight floating proof cards, institution search, filters and a blurred-background detail window. Your evidence passport remains available and links to it.

### 2. Published facts, declarations and bank checks are separate

Each program now shows what the reviewed source says beside what the applicant declares. Missing answers remain unknown, real numerical gaps are visible, and a green preparation bar still shows that the bank must check the application. Sales, expenses and receipt coverage provide ledger context; they do not secretly become loan eligibility rules.

### 3. Source-cited financing questions

You can ask about amounts, pricing, documents, preparation, fees, deadlines and application routes. The optional AI can choose from retrieved facts only; it cannot invent an amount, closing date or approval message. If its response cannot be checked or the service is unavailable, the reviewed facts and official source links still appear.

### 4. A safe updating contract for later

The five programs are stored in a versioned file with a strict JSON schema, official-source links and review dates. A validation command is ready for future proposed updates. No scraper, scheduler or public write endpoint is running; an update still requires source review, tests and a separately approved deployment.

## Source limits that must stay visible

The catalogue is the team's **reviewed 23 October snapshot**, not real-time lender approval or a bank integration. All five intakes require institution confirmation; no common closing date was verified, so there is no invented countdown. Akhuwat's current product-specific cap remains unverified. PMYP's official indexed text was accessible, but the direct research fetch timed out; the source note records that limit. Meezan's existing-borrower/relationship wording needs bank confirmation, not a permissive interpretation.

This is **curated retrieval with optional LLM fact selection**, not embeddings/vector RAG or free-form financial advice. English/Roman Urdu/Urdu question matching is tested; the source facts themselves are still English. Applicant declarations remain page-memory-only. They are not independently verified or saved as a persistent application profile. The model receives the typed question and public facts—not the structured profile or ledger; users should not type private identifiers into questions.

This run did not re-audit every dependency, test a real Supabase session/two-account hosted isolation, replay human microphone capture or re-test all receipt providers. Existing automated regression checks passed; those separate production/security/voice gates are not claimed complete. No deployment was authorized or attempted in this phase.

## Short booth rehearsal (synthetic example, not a lending claim)

1. Say: “The merchant has a ledger. What should they prepare before approaching an institution?” Open Financing, point out the sample-data badge and dated sources.
2. Enter the invented owner age 30, retail, PKR 500,000 request, resident Pakistani, valid CNIC prepared; operation age 24 months, six months of statements, BOP relationship eight months/no invitation. Mark guarantors unavailable, branch area confirmed, no Meezan relationship and no other I-SAAF. These are declared example facts, not a real applicant.
3. Open BOP: show **50% preparation**, a four-month relationship gap and lender-only DBR/guarantee review. Explain that more sales cannot replace that banking relationship.
4. Hypothetically change BOP relationship to twelve months and invitation to yes: the preparation bar becomes green, but no loan is approved. Do not pretend time actually elapsed or an invitation was issued.
5. Ask “Compare PM Youth and BOP loan amounts,” then “What is the application deadline?” Show citations and the honest absence of a verified closing date. Keep AI assist off if quota/network is unreliable; source retrieval remains available.
6. Return to Ask and ask total udhaar. Explain the distinction: SQL calculates merchant amounts; financing answers retrieve reviewed facts. Close with “We help merchants prepare an evidence-backed conversation; the lender decides.”

## Proposed run 2 (40–70 minutes, no new feature sprawl)

- 15–20 minutes: team reviews this local workspace and rehearses the above scenario; fix only concrete blockers.
- 15–25 minutes: align the final pitch/script with actual behavior and date-check any statistic used. Remove old demo-fallback, every-entry-voice-verified, five-programs-matched and zero-vulnerability claims. Videos and HTML also disagree on SME GDP/jobs figures; choose one directly sourced measure with its definition/year or omit it. Video review in this run covered metadata and sampled visuals, not a complete audio transcript.
- 10–25 minutes: only after separate approval, create the release commit, review it, deploy, test authenticated hosted flows and preserve the known-good rollback. No Vercel/environment/account change has happened in run 1.

## Future n8n proposal flow (not installed or scheduled)

Collect only allowlisted official pages → save a candidate JSON snapshot with source URLs and checked dates → flag changed facts for a human reviewer → validate against `/api/financing/catalog/schema` and `scripts/validate_financing_catalog.py` → run focused tests → publish through an approved Git/deployment change. Use the oldest source date to trigger review; schema validity alone does not prove accuracy. Start monthly with an additional pre-presentation manual check, then choose a cadence based on actual scheme changes. Do not automatically overwrite verified terms from scraped text.

## Deferred after the finale

Scheduled n8n collection with reviewer approval, richer scheme-document retrieval/vector search if the corpus grows, persistent application profiles and encrypted document storage, lender integrations/eCIB/KYC, production rate limiting and observability, independent two-account security rehearsal, multilingual human voice testing, current dependency/advisory review, and a refreshed pitch/video with source-checked statistics. No automated loan decisions or submission.

## Final-round release window — 24 October 2026

The team requested a 15-minute release/checkpoint with synthetic applicant details, the same QR-code URL and a recoverable prior deployment. This supersedes the run-1 no-publish boundary for the checked Phase 2 changes only. No database migration, production seed, credential change or auth change is part of this release.

Fresh offline regression: **326 tests passed in 19.54 seconds**. The existing verified production build is available locally; Vercel must rebuild from committed source with its existing Production settings, never upload the local build containing loopback API settings. New-source credential-pattern scan returned no matching private key/connection string; tracked environment files remain example templates only.

### Rollback recorded before publishing

- Stable QR-code origin: `https://project-4ps4k.vercel.app/`.
- Dashboard-verified previous Production deployment: `C1oz7FiAkikJSB7EPLBqtEBSLHpA`, Ready, source `036dcc9ec6d4efc08f58c939c8ee90da6efa1344`.
- Previous deployment hostname: `karobar-jewcs9jwf-hassanbinsaqib01-5133s-projects.vercel.app`.
- Project: `karobar-ai`, `prj_kYTi4ovRgqXzdJV6ACG5ll9ffT7M`, team `hassanbinsaqib01-5133s-projects`.
- Recover the previous release from its Vercel deployment page: `https://vercel.com/hassanbinsaqib01-5133s-projects/karobar-ai/C1oz7FiAkikJSB7EPLBqtEBSLHpA` → deployment menu / Instant Rollback. Verify that the stable domain points back to that deployment. Do not delete either deployment.
- Local Git fallback tag: `final-round-fallback-2026-10-24` at `036dcc9`. A Vercel rollback changes served code, not database contents; this phase introduces no database migration or profile write. Future pushes may need explicit promotion after a rollback.

Hosted results must be appended after observation. No claim of complete hosted functionality is made merely from a Ready build.
