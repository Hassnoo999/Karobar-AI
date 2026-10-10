# Karobaar AI regional-round implementation ledger

Last updated: 10 October 2026 (PKT). Regional presentation: 11 October, FAST NUCES Islamabad, per the team.

## Working agreement

The audit and first UI run are complete; the second chatbot/trust run is authorized. Execute in staged checkpoints with focused regression tests. Preserve real credentials, databases, uploaded evidence and unrelated changes. Historical context documents describe earlier phases; their "start from zero" instructions do not authorize deleting or rebuilding this repository.

Budget assumption: two five-hour execution windows, including testing and handoff. Estimates are timeboxes, not guarantees or predictions about a model's speed. Model selection remains under the user's control.

## Checkpoint tracker

| Checkpoint | State | Evidence / exit gate |
|---|---|---|
| A0 Inventory and current baseline | Complete | Initial commit `8570ba0`; existing `frontend/next-env.d.ts` modification preserved; context/backend context copies are identical |
| A1 Context and deck comparison | Complete | Unique historical Markdown, original PDF, organizer email, Claude chat, both decks and current READMEs compared |
| A2 Core flow and chatbot audit | Complete | 74 baseline tests pass; 26 offline question cases, 8 live-provider routing cases, API validation/cache tests and isolated receipt-ownership reproduction |
| A3 Desktop/mobile UI audit | Complete | Seven routes at 1440px and 390px; capture review, suggested-question and reminder interactions; screenshots retained |
| A4 Prioritized one-day plan | Complete | Two 300-minute windows below, hard release gates, optional cuts and booth scenario |
| U1 Shared shell and dashboard redesign | Complete | Scoped dependency patches, shared snapshot/tokens, canonical metrics; production build and responsive routes pass |
| U2 Capture and ledger redesign | Complete | Typed confirmation, provenance, manual fallback, full-history customers, filters/export/pagination; 15 regressions + browser flow pass |
| U3 Ask and evidence redesign | Complete | Phone composer, supported examples, honest failures, transparent metrics, reference-only financing and editable reminder; L1 routing fixes now separately verified |
| L1 Chatbot correctness and trust fixes | Complete (local scope) | 165 backend tests, 26/26 original questions and 27 browser-story checks; deterministic replies, upload-time ownership, free health and honest evidence/financing |
| D1 Deployed real demo | Foundation created / not deployed | Chrome: `karobar-ai` project + GitHub link + private receipt Blob store created; storage adapter/config/secrets/auth/cloud checks remain gates |
| P1 Presentation and three-person rehearsal | Planned | Fresh screenshots, checked claims, scripted live sequence and backup |

## Product contract

Voice/text or receipt → structured draft → merchant review/confirmation → confirmed ledger → dashboard and grounded questions → qualitative evidence/readiness → editable reminder draft.

Four event types: cash sale, credit sale, repayment, expense. Money is authoritative in integer paisa. Financing guidance does not approve loans or score credit. Messages do not send automatically. Supabase authentication exists in the current implementation even though the original narrow local-demo scope excluded it.

## Where the project stood at the audit baseline

The product is a functional prototype, not a blank starting point. The current frontend is Next.js/React/TypeScript/Tailwind with Framer Motion and a cinematic Three.js landing page. FastAPI/Pydantic/SQLAlchemy own the ledger; Supabase handles identity. The current private local configuration uses PostgreSQL with authentication enabled. Audit servers used a separate SQLite database and disabled auth only within the local audit process. No real ledger was seeded, reset or changed.

The architecture's strongest distinction is the separation of proposed AI extraction from merchant-confirmed records and deterministic money calculations. This is worth demonstrating live. It is not yet evidence of bank acceptance, improved loan approval, a verified business identity or a real merchant pilot.

| Capability | Current implementation | Confidence / limitation |
|---|---|---|
| Voice capture | Browser microphone, transcription and event extraction, editable draft | Real microphone/audio-provider flow not revalidated in this audit; demo transcription is canned, not real recognition |
| Receipt capture | Upload, Gemini extraction, review and protected file endpoint | Review UI tested with demo provider; real OCR, cloud persistence and ownership need release checks |
| Confirmed ledger | Four event types, integer paisa, customer association, FIFO settlement, canonical CRUD | Baseline tests pass; permissive frontend bridge and stale cache have gaps |
| Dashboard | Sales/expenses/udhaar, chart and recent activity | Some labels/provenance are wrong; frontend recomputes balances from at most 200 events |
| Ask Karobaar | Five read-only tools: total outstanding, top debtor, customer balance, monthly sales, sales comparison | Routing/date/fallback failures reproduced; UI advertises unsupported queries |
| Evidence/readiness | Qualitative passport and five financing-program references | Internal thresholds are mixed with published eligibility; claims need correction |
| Reminder | Visible copyable template in current product UI; separate grounded backend draft endpoint exists | Current drawer is not editable and does not call that backend; no automatic sending |
| Auth and deployment | Supabase integration, merchant-scoped API queries; prior public frontend reported in context | Real deployed end-to-end flow, live DB RLS/grants and persistent receipt storage not verified this pass |

The Groq provider implements text/audio but its receipt method intentionally fails over. `GROQ_VISION_MODEL` does not make receipt extraction work there. Gemini is the current live receipt path. Groq → Gemini → demo fallback can mask a real-provider failure with a plausible demo response; production must disclose or reject this fallback.

## Original audit evidence and limits

All diagnostic scripts and screenshots are under `D:/Monk Mode/Moxaris/Ali Baba Hackathon/tmp/regional-audit/`, outside the GitHub repository. They contain synthetic/demo inputs, not exported real merchant data or credentials.

| Check | Actual result | Interpretation |
|---|---|---|
| Backend pytest | 74 passed; Starlette/httpx deprecation warning | Useful ledger/API baseline, not comprehensive production security or AI coverage |
| Offline Ask evaluation | 12/26 cases passed; 14 failed | Deliberately adversarial/unsupported question set, NOT a population accuracy measurement |
| Live synthetic AI routing | 7/8 cases passed; August 2026 question fell to demo and lost the requested month | Live providers can improve routing but don't remove the fallback defect; provider reason not established |
| Live synthetic answer composition | Correct PKR 100,000 answer for one supplied tool result | One spot check, not proof that free-form composition can never invent numbers |
| UI route checks | 14 desktop/mobile route checks; no page exceptions or root horizontal overflow | Layout usability still has problems; not an accessibility certification |
| Suggested recovery question | Current UI button produced an unsupported reply | UI promise and tool contract disagree |
| Capture review | Demo extraction with amount 0 and low confidence still offered enabled confirmation | Validation/review-state UX needs a gate; not a real receipt extraction test |
| Invalid bridge input | Unknown event type saved as sale (201); nonnumeric amount returned 500 | Strict canonical schema is bypassed by bridge dictionary parsing |
| Cache test | Canonical write succeeded but combined record count stayed unchanged immediately | Canonical mutation does not invalidate the 30-second combined cache |
| Receipt ownership | Merchant B: 404 before claim, arbitrary filename event accepted (201), file readable (200) after claim | Confirmed authorization design flaw using isolated identities; no real JWT bypass or real receipt access attempted |
| Production npm audit | 3 vulnerable dependencies: Next.js critical, sharp high, source-map-js high | Actual exposure depends on routes/runtime; not evidence of exploitation; September zero-vulnerability claim is stale |
| Frontend production build | Passed; TypeScript passed; 11 static pages generated | Audit used public local-demo environment overrides; real production auth/network is a separate gate |

Reproduction files: `evaluate_questions.py` / `question-report.json`, `evaluate_live_ai.py` / `live-ai-report.json`, `evaluate_ownership.py`, `inspect_ui.cjs`, `inspect_ui_followup.cjs`, `ui/report.json`, `ui/followup-report.json`.

## Ranked corrections

P0 means a release gate, not a request for an architectural rewrite. P1 means essential for a credible booth demonstration. P2 is polish that can be cut.

| Priority | Finding | Bounded correction | Acceptance check |
|---|---|---|---|
| P0 | Receipt ownership is inferred from a client-claimable event filename | Bind uploaded evidence to merchant ownership at upload time; validate at every attach/read path; retain legitimate existing files | Other merchant cannot claim/read file, including canonical and bridge endpoints; owner still can |
| P0 | Current dependency audit is critical/high | Scoped Next/sharp/source-map dependency and lockfile update; inspect advisories and patched versions; no blind force-update | TypeScript/build and browser smoke tests pass; audit rerun records actual remaining exposure |
| P0 | Wrong chatbot intent/date; generic answers on errors; hidden demo fallback | Typed intent/date resolution, safe unsupported/clarification handling, deterministic money response renderer, explicit provider/fallback state | Same frozen-clock question cases pass; API/auth failure gives an error, not unrelated totals |
| P0 | Financing thresholds lack source support but look like published requirements | Separate official eligibility, manually supplied facts and internal evidence suggestions; remove unsupported numeric qualification rules | Every published requirement links to a supporting official page; no loan approval/credit-score language |
| P0 | Public deployment boundary unverified | Verify auth required, production CORS, backend-only secrets, exposed-schema RLS/grants, persisted DB/files, provider limits | Two-user isolation, unauthenticated denial, reload/restart persistence and real capture all pass |
| P1 | Bridge silently coerces unknown types and float money | Typed bridge schema; Decimal/paisa conversion through one authoritative path | Unknown type/invalid date/nonpositive or malformed money returns 422; rounding tests pass |
| P1 | Source/confidence misrepresentation | Keep seed/manual/voice/receipt distinct; preserve confidence 0 and unknown; display demo/provider state | Seed rows never say voice verified; missing confidence never becomes 90% |
| P1 | Stale frontend refresh, cache and auth token state | Invalidate all mutation paths; refresh after save/auth change; use authoritative customer totals | New entry appears immediately; account switching cannot retain previous merchant data |
| P1 | All-time debtors/reminders rebuilt from latest 200 events | Consume existing backend customer/FIFO aggregates rather than truncated frontend history | A fixture with >200 entries yields matching dashboard, ledger, Ask and reminder balances |
| P1 | `net_cash` counts credit sales; `total_payables` is overdue receivables | Correct calculation or replace misleading UI labels; do not call sales-minus-expenses cash balance or profit | Cash sale, credit sale, repayment and expense fixture distinguishes sales/receipts/cash movement |
| P1 | Overdue filter is effectively positive-balance filter | Define overdue age consistently and use authoritative unpaid aged entries; otherwise rename to outstanding | Recently issued credit and fully repaid rows do not appear as overdue |
| P1 | Evidence claims infer more than stored records show | Fix concentration denominator/label, active-month wording and recurring-expense claim | Statements can be traced to named fields and a reproducible calculation |
| P1 | Capture loses duplicate/uncertainty flags; invalid draft can be confirmed | Retain required validation, duplicate warning, provider and source metadata; disable invalid save; prevent double-submit | Nothing changes before confirmation; rejection makes no entry; missing amount/customer cannot silently save |
| P1 | Current reminder is non-editable; copy success assumed | Editable grounded draft, awaited clipboard result and explicit merchant-send boundary | Exact current debtor balance, successful edit/copy, no automatic outbound message |
| P1 | Verification health endpoint can invoke paid AI anonymously | Restrict active provider verification to authorized operator or remove it from public runtime; keep cheap health check | Public health never triggers paid model calls or returns sensitive provider details |
| P2 | Signup confirmation, fake search/bell, static September header | Handle email-confirmation state, use real period, remove placeholders or make search work | No silent redirect loop or controls suggesting functionality that does not exist |

Further hardening after the event: upload signature/magic-byte validation and orphan cleanup, request limits/quotas, dependency pins, DB migrations, pagination/query performance, monitored provider retries, accessible automated tests. FIFO treatment of prepayments/backdating is a policy question: preserve current accounting unless a policy and regression fixtures are explicitly agreed.

## UI/UX design brief and screen plan

Keep the existing forest/mint identity. Use an off-white workspace, white cards, forest primary actions, coral only for overdue/error, and amber for uncertainty. One readable sans-serif for the product; serif reserved for short brand/story headlines. Fewer 800-weight labels, comfortable body text, tabular money, consistent spacing/radius/borders, obvious focus, 44px touch targets and reduced-motion support. No new 3D assets or bespoke animation system.

| Screen | Current friction | Target redesign |
|---|---|---|
| Shared shell | Wide fixed sidebar, static month, pretend search/bell, truncated mobile nav | Slim coherent sidebar; real/demo connection state; useful period label; clean five-tab mobile navigation; hide nonfunctional chrome |
| Dashboard | Sparse one-month bars in oversized chart, heavy type, metrics without consistent scope | Clear store/period header and record CTA; four scoped KPIs; use existing six-month trend; compact recent activity and authoritative debtor list |
| Record | Oversized microphone/empty panel; mobile review below fold; uncertain draft looks ready | Compact voice/receipt choice; capture → review → confirmed progress; visible validation/source; mobile auto-focus/scroll to draft; sticky valid-save action |
| Ledger | Duplicate receivable KPIs; 63 rows create ~5k-pixel page; search/filter before any mobile rows | Unified balance strip; customers/transactions tabs; concise searchable table with pagination; mobile cards preserving date/source; honest outstanding/overdue filters |
| Ask | 680px minimum conversation pushes composer below fold; unsupported suggestions; ungrounded error fallback | Viewport-fitting chat; always-visible composer; supported example questions; answer cards showing period, source and exact value; calm unsupported/error state |
| Evidence | Duplicate passport/checklist; mobile page ~4.8k pixels; unnamed criteria chips; reminders detached from authoritative endpoint | One evidence summary; three actionable gaps; collapsible programs with criterion/value/source labels; manual vs observed distinct; editable grounded reminder drawer |
| Landing/auth | Strong existing branding; timed intro adds ~6 seconds locally; sign-in already serviceable | Bypass intro for booth/repeat visits and respect reduced motion; direct app CTA; correct signup feedback; only essential polish |

The redesign is a coordinated refinement of all five screens, not five independent rebuilds. Historical unused workbench/panel components should not absorb today's time. This table describes original friction; the first-run checkpoint below records the actual shipped correction.

## Two-window execution plan

Each window is capped at 300 minutes. Estimates assume the current stack is retained and provider/hosting accounts are accessible. GPT-5.6 Sol with extra-high thinking can be used as requested, but reasoning setting does not guarantee completion time. Stop and reassess at every exit gate.

### Window A — visible product transformation (5 hours)

| Timebox | Work | Exit gate |
|---|---|---|
| 0:00–0:30 | Dependency patch checkpoint and baseline build; read installed Next guidance before changing code | Patched baseline builds, or record blocker and reduce cosmetic scope |
| 0:30–1:10 | U1 shared tokens, typography, shell and responsive navigation | All routes usable at 390/768/1440px, no placeholder controls |
| 1:10–1:55 | U1 dashboard redesign, scoped metrics, available recorded-month chart | Numbers agree with canonical API; empty/loading/error states honest |
| 1:55–2:45 | U2 capture review redesign and typed validation/provenance | Valid confirm works once; invalid/rejected drafts never mutate ledger |
| 2:45–3:30 | U2 ledger, authoritative customers, pagination/filter semantics | Search/export/date/source work; >200-event balances agree |
| 3:30–4:00 | U3 Ask layout and supported suggestions | Composer visible on phone/laptop; unsupported suggestions removed |
| 4:00–4:35 | U3 evidence layout and reminder UX | Gaps readable, criteria named, drawer editable and grounded |
| 4:35–5:00 | UI smoke/keyboard/mobile pass, screenshots, ledger checkpoint | Build + route checks pass; selected before/after evidence saved |

### Window B — trustworthy demo, deployment and narrative (5 hours)

| Timebox | Work | Exit gate |
|---|---|---|
| 0:00–1:10 | L1 intent/date/unsupported handling, deterministic numeric answers, honest fallback | Frozen-clock eval and adversarial cases pass; no wrong current-month substitution |
| 1:10–2:00 | Trust/security checkpoint: filename ownership, source facts, financing criteria, invalidation and provider-health gate | P0 regressions pass; evidence statements reflect data/source limitations |
| 2:00–3:00 | D1 deploy and verify actual frontend → authenticated API → DB/files | Real voice + receipt, confirmation/reload and two-user isolation pass |
| 3:00–4:05 | P1 7–8-slide deck and linked speaking script; fresh product screenshots | Every spoken/visual claim agrees with implemented behavior |
| 4:05–4:40 | Three-person booth rehearsal and fallback recording | 3-minute story, 90-second live sequence, recovery path and judge Q&A |
| 4:40–5:00 | Buffer, final README/env examples, submission links and ledger handoff | Clean scoped diff, no secrets, known limitations documented |

Dependency/order note: layout can proceed without broad feature expansion. Accounting label fixes must land before new KPI screenshots. Security gates precede a public deployment. Deck screenshots follow final UI. Keep a tested local build and short screen recording throughout.

If time slips, cut landing animation work, new expense/recovery chat tools, advanced motion, custom charts and optional exports. Keep the existing five-tool contract and say unsupported honestly. Do not sacrifice ownership/auth, accurate numbers, persistent data or rehearsal. If any P0 release gate remains unresolved, use a controlled local demo and a clearly labeled read-only hosted showcase rather than exposing real merchant writes.

## Chatbot test contract and hypothetical booth scenario

Freeze a synthetic ledger and clock for tests. Cover English, Roman Urdu and Urdu; total/customer debt; current, previous and named months; comparisons; empty ledger; unknown/ambiguous names; punctuation; invalid month; unsupported profit/cash/loan approval; provider timeout; auth/API failure; adversarial requests to invent/change numbers. Assert tool, normalized arguments, period, exact paisa result and user-facing reply. Run against both direct API and product chat UI. New expense/recovery tools are optional after the five existing tools pass.

Use a clearly hypothetical shopkeeper scenario, not a fabricated pilot:

1. Begin from a known controlled baseline; show a new demo customer, Naveed, with no balance.
2. Speak: "Naveed ne 5,000 rupay ka saman udhaar liya." Show the proposed customer/type/amount/date and real provider. Ledger is unchanged during review.
3. Confirm once. Naveed balance becomes PKR 5,000; total udhaar rises by exactly PKR 5,000.
4. Record a PKR 2,000 repayment and confirm. Naveed balance becomes PKR 3,000, not another sale.
5. Ask: "Naveed ka udhaar kitna hai?" Show PKR 3,000 sourced from the ledger. Ask a named-month sales question to demonstrate period correctness.
6. Show what the evidence profile can and cannot establish; copy an editable PKR 3,000 reminder. Explicitly say no message is sent and no loan is approved.

If the baseline total is PKR 100,000, expected total after both events is PKR 103,000. Don't hardcode that total in narration if using a different deployed dataset. A QR/live link is useful only after the deployed path is genuinely verified.

## Presentation comparison and narrative decisions

The original nine-slide submission deck is cautious about scope. Claude's eleven-slide deck has a better visual story and a useful merchant-centered problem hook, but spends too long on macro context before the working product. Reuse its forest/mint/coral style and problem-to-proof framing, not every statistic or claim. Enlarge product screenshots and sources for a projector. A booth deck needs no lengthy table of contents.

Proposed 7–8 slides: (1) one shopkeeper/problem hook, (2) records-to-evidence solution flow, (3) live capture/review demonstration, (4) ledger and exact Ask response, (5) evidence/readiness and action, (6) technology/trust boundary, (7) built today vs limitations/next validation, (8 optional) close/live QR. A three-person split: problem and user; operate the live flow; explain technology, boundaries and next steps. Rehearse handoffs without repeating the introduction.

Corrections before using Claude's deck:

- Pakistan's 2.1% bank-loan/credit-line figure comes from the 2022 World Bank Enterprise Survey of formal private firms with five or more employees, not all informal merchants. Its current country-profile regional comparator differs from the deck's 31.6%; avoid mixing years/definitions. [World Bank primary profile](https://www.enterprisesurveys.org/content/dam/enterprisesurveys/documents/country/Pakistan-2022.pdf).
- PBS HIES 2024–25 reports 63% literacy for people aged 10+, not adult 15+ literacy. It does not prove that most merchants cannot type or use English. [PBS primary social report](https://www.pbs.gov.pk/wp-content/uploads/2020/07/PSLM_Report_2024-25-janurary-26-Social-Reportupdated.pdf).
- The 800,000 retailers / 5,000 digitized statement is a secondary industry estimate with unclear digitization definition/date; omit unless primary evidence is established. The global USD 5.7tn finance-gap claim and other SME percentages were not independently established in this pass; don't reuse them as verified facts.
- Financing exclusion has multiple causes. Pitch better records as support for a financing conversation, not a proven sole cause or a guaranteed route to credit.
- "Every entry is voice verified" is false for seed/manual/receipt data. "AI never writes a number" is also imprecise: AI proposes extracted amounts; deterministic ledger code computes totals.
- Alibaba integration remains future work. There is no implemented Alibaba adapter; switching to it is not merely an environment-variable change. The supplied organizer email permits any toolchain, so a rushed migration is not justified by the available rules.
- 74 baseline tests still pass. "Zero vulnerabilities" is no longer true of today's npm audit. No real merchant adoption, bank partnership or measurable approval impact is established.

Official financing checks found PM Youth supports new and existing businesses; a six-month business-history eligibility floor in our data is not supported by that fact. BOP's page describes bank relationship, invitation and borrower criteria, not our invented receipt/revenue cutoffs. Meezan's page likewise does not support our percentage-based receipt requirements. Verify the remaining HBL/Akhuwat entries before presentation; otherwise show reference links/manual next steps without numeric eligibility claims. Sources: [PM Youth](https://pmybals.pmyp.gov.pk/), [application requirements](https://pmybals.pmyp.gov.pk/BankForm/newApplicantForm), [BOP](https://www.bop.com.pk/view.aspx?id=3415), [Meezan](https://www.meezanbank.com/sme-banking/).

## Production configuration reminders

Importing secrets into a hosting dashboard is not itself public disclosure. But secrets belong only to the project/runtime that needs them; a frontend deployment does not automatically deploy the FastAPI backend. Never put database passwords, AI keys, JWT secrets or service-role keys under `NEXT_PUBLIC_`: those variables reach browser code. Public Supabase URL/anon (publishable) configuration is different from a service-role secret. [Next.js environment rules](https://nextjs.org/docs/pages/guides/environment-variables), [Vercel sensitive variables](https://vercel.com/docs/environment-variables/sensitive-environment-variables).

Backend merchant filtering does not prove that direct database APIs are protected. Inspect actual exposed schemas, grants and RLS policies; no remote policy change was made during this audit. [Supabase security guidance](https://supabase.com/docs/guides/database/secure-data).

Deployment target choice follows a read-only check of the existing working host. Keep Vercel for frontend if already linked. Put FastAPI where the current runtime, database and persistent receipt storage can be verified quickly; don't assume an ephemeral function filesystem is durable storage. Auth enabled, seed/reset controlled, exact CORS and backend URL, provider timeouts/fallback disclosure, and safe demo account are release gates. No deployment or remote project settings were changed in this phase.

## Checkpoint log

- First implementation run authorized: prioritize visible UI improvement and focused regression checks. Decisions: retain stack and forest/mint brand; patch Next within 16.3; reuse canonical dashboard/customer aggregates; never fabricate answers on network errors; do not deploy with unresolved P0s. Defer exhaustive backend/security/performance work to L1/D1 or post-regional backlog, not silently abandon it.

- 10 October: A0–A4 audit/plan completed. Created this ledger and synthetic diagnostic artifacts only. Production build/TypeScript passed. Build regenerated `next-env.d.ts`; restored its pre-audit dev-type import state to preserve the user's existing modification. No business logic/UI/deck changes, Git commit, remote database write, email/message or deployment performed. Audit-only local servers stopped after checks.
- First-run checkpoint: U1/U2/U3 completed on 10 October; details below. Next: L1 chatbot and security gates, then D1 deployment and P1 narrative. No public deployment sign-off yet.

## First implementation run — completed 10 October 2026

### Outcome and main decisions

| Decision | Reason and result |
|---|---|
| Retain Next/React/FastAPI and the existing forest/mint brand | One coherent redesign across all five product screens; no framework, AI SDK or accounting migration in the presentation-day window |
| Use shared tokens and small common primitives | Consistent typography, cards, spacing, focus and controls; narrower sidebar, meaningful header and usable mobile navigation; removed fake search/bell |
| Expose existing canonical aggregates through `/combined` | Dashboard, customers and reminders use full confirmed history; >200-row fixture proves the limited entry window does not corrupt balances |
| Keep chart history honest | Show the available recorded-month trend (four months in the seed), with exact values accessible in a table; do not manufacture six months |
| Add strict bridge validation, not new accounting | Decimal PKR is validated before exact conversion to paisa and passed to the existing confirmation/FIFO service. Unknown type, malformed/nonpositive money and invalid date are rejected |
| Preserve uncertainty and require review | Missing type/date/amount stay missing; zero confidence stays zero; source, provider and duplicate flags survive. Invalid saves are blocked, double confirmation saves once, failed saves retain the draft |
| Provide manual entry through the same contract | A practical booth fallback for denied microphone access or failed recognition; explicitly labeled Manual with no fake confidence; not a second ledger implementation |
| Share and invalidate snapshots | One provider owns route data; save/refresh reloads it, account changes clear it, canonical mutations and demo controls invalidate the process-local cache. Browser requests read Supabase's current session rather than a separate stale token cache |
| Make offline/demo states explicit | No automatic sample substitution after API failure. Opt-in preview is coherent and read-only; seeded rows and Demo AI are separately labeled; API connected does not claim live AI availability |
| Withhold unsupported financing judgments | Evidence metrics and manual gaps are readable; five financing references remain available but unverified match badges, numerical thresholds and loan ranges are not presented as eligibility evidence |
| Keep Ask changes bounded to UI honesty | Four supported example questions, tool/period/provider labels, clear errors and a visible phone composer. No new tools or claim that existing intent/date defects are fixed |
| Keep reminders deterministic and editable | Full-history customer balance → template → merchant edit → awaited clipboard result. No WhatsApp/SMS send, no AI-generated monetary amount |
| Patch scoped production dependencies | Next 16.3.8, patched sharp/source-map-js lockfile, declared Node 22.x. A portable Node 22 runtime was used for validation; system Node was not replaced |
| Defer unrelated work explicitly | No rushed landing/3D rebuild, schema migration, new chat tools, live account/policy change, infrastructure migration or deck redesign during this UI checkpoint |

### Changed areas

- Frontend: product layout/provider, shell, all five screens, shared `ui.tsx`, global product styles, API types/session/error handling and one coherent `demo-fixture.ts`. The prior hook `.ts` is replaced with the context provider `.tsx`; the legacy capture component now handles nullable confidence.
- Backend: typed `schemas/product.py`, bridge display/aggregate/confirmation contract, shared `services/product_cache.py`, canonical mutation/demo invalidation, and `tests/test_product_bridge.py`. Existing FIFO and arithmetic algorithms are unchanged.
- Handoff: root/frontend/backend READMEs describe the current UI and actual limits; root `.gitignore` excludes TypeScript incremental build output. Showcase screenshots are refreshed from the isolated UI checks. The earlier submission deck is intentionally not edited yet.

### Verification actually performed

| Gate | Result | Scope/limit |
|---|---|---|
| Backend suite | 89 tests pass (74 existing + 15 new) | Offline in-memory fixtures; one existing Starlette/httpx deprecation warning |
| Product-bridge regressions | 15 pass | Invalid input, exact paisa, uncertainty/provenance, >200-entry customer totals and canonical/demo cache invalidation |
| Production build + TypeScript | Pass, 11 static pages generated | Node 22.23.3 / Next 16.3.8; isolated public demo env overrides, not real auth/provider verification |
| Responsive browser routes | 15 pass | Five routes at 1440×1000, 768×1024 and 390×844; no browser exceptions/root horizontal overflow; Ask send control above mobile navigation |
| Browser scenario/recovery | 19 checks pass | Draft leaves ledger unchanged; PKR 5,000 credit → PKR 2,000 repayment → Naveed PKR 3,000; total PKR 103,000. Dashboard/ledger/question/reminder agree; filters/CSV/pagination, save/API failures, sample preview/reconnect, clipboard and Escape tested |
| Production dependency audit | 0 known vulnerabilities | `npm audit --omit=dev`; not an overall security certification |
| Dev-inclusive dependency audit | 8 remain: 2 moderate, 6 high | Tailwind/PostCSS/globbing build-tool dependency chain. Record separately; no forced Tailwind major migration. Review bounded compatible patches at D1 before claiming an all-dependency clean audit |
| React/UI quality checklist | Reviewed; relevant checks pass | Client boundaries/hooks, stable keys, IME submission, duplicate-submit guards, async stale-response guards, microphone/object-URL cleanup, native dialogs/focus, labels/current navigation, reduced motion and filtered CSV escaping; not an accessibility certification |
| Git/diff and ignore checks | Pass | No whitespace errors; local `.env`/`.env.local`, databases and `.tsbuildinfo` excluded. Pre-existing `next-env.d.ts` dev-type imports restored after build; no commit/push |

The first browser runs encountered two test-harness locator issues, not app defects; corrected selectors then passed. Responsive QA found and fixed a real phone composer obstruction and an over-broad muted-text color change on dark hero cards. Microphone permission denial was simulated; actual live audio/OCR remains unverified.

Evidence: `tmp/regional-audit/run1-ui/smoke-report.json`, `story-report.json`, 15 screen PNGs, `dashboard-story-desktop.png`, `filtered-ledger.csv`, and `run1_ui_smoke.cjs` / `run1_ui_story.cjs` outside the repo. Test writes/reset/seed were only against the owned loopback server using `tmp/regional-audit/run1.db`, never the real PostgreSQL ledger. The story script assumes the 63-event seed baseline and is not a general production test runner.

Elapsed-time note: a start-of-turn timer was not captured, so no precise measured run duration is claimed. This was one continuous implementation run with focused checks, not a new five-hour backend audit. The local frontend was stopped for its successful production build; restarting the preview was blocked by the app execution policy. Screenshots and test evidence remain available. The backend was then stopped at handoff; no audit server is left active.

### Next run and deferred gates

1. **L1 first:** fix the reproduced chatbot intent/date/fallback defects and enforce deterministic monetary wording. Re-run the existing frozen-clock adversarial cases; test both API and product chat. The one supported Naveed query passing does not resolve the 14 failing audit cases.
2. **Before public merchant writes:** bind receipt ownership at upload and validate every attach/read path; restrict paid `health?verify=true`; check real Supabase sessions and exposed-schema RLS/grants, exact CORS/secrets, production seed/reset controls and persistent DB/receipts. These P0s remain open.
3. Correct unsupported financing rules and legacy bridge evidence claims (recurring expenses, "verified" records, concentration denominator). New UI avoids those assertions; legacy API payloads still contain them until corrected.
4. D1: verify the actual deployed frontend → authenticated backend → data flow, real voice/receipt extraction, refresh/reload/restart and two-user isolation. Check process-local cache freshness if running multiple workers. Do not rely on this local demo as deployment evidence.
5. P1: update the deck with the new screens, checked claims and three-person speaking/demo script; rehearse a short fallback sequence.

**After the regional round:** full server-side entry pagination and scalable query/cache behavior; upload magic-byte checks/orphan cleanup; quotas/rate limits and provider observability; migrations/backup strategy; expanded automated accessibility/auth tests and smaller-phone/Safari/virtual-keyboard checks; landing intro/signup-feedback polish; unused legacy-component cleanup. New expense/profit/chat tools, inventory and banking integrations remain out of this run's scope.

No real credentials, remote database policies, Vercel/Render configuration, presentation or GitHub repository state were changed by this run. UI completion is not a public-release or chatbot-correctness sign-off.

## Second implementation run — completed local checkpoint, 10 October 2026

### Outcome and decisions

| Decision | Reason and verified outcome |
|---|---|
| Keep five read-only tools and existing FIFO/paisa accounting | No new profit/expense tool or accounting migration before the booth; query correctness improved without expanding the product promise |
| Resolve supported intent/date patterns before using an AI classifier | Named months, English/Roman Urdu/Urdu customer questions, adjacent-month comparisons and January rollover retain their actual period. Ambiguous, invalid or unsupported requests are clarified, not silently mapped to nearby totals |
| Render financial answers from tool results, not an LLM | Supported API answers contain deterministic ledger values; a classifier cannot rewrite the amount. UI shows the source and interpretation method. No blanket claim to understand every possible phrasing |
| Bound unknown classifier arguments | Reject extra/unrecognized keys, nonliteral customer names and invalid months. No arbitrary SQL or model-defined accounting tools |
| Establish receipt ownership at upload | A private server-written owner registry is checked before any attachment or read. Both canonical and product confirmation paths reject another merchant's filename before writing a customer/event |
| Fail closed on old unregistered receipts | Existing files are preserved, not automatically assigned to whichever ledger claims them. An explicit operator command can register an independently verified owner; durable backup must include `.owners` metadata |
| Remove publicly triggerable paid health/startup calls | `/health` checks configuration cheaply; `?verify=true` returns 403. Active provider probing is an explicit operator command, not an unauthenticated URL or each reload |
| Remove unsupported financing qualification rules at the source | All five catalog entries are manual reference links, with no invented sales/history/receipt thresholds or inferred fit. BOP/Meezan pages reviewed today; inaccessible PM/Akhuwat/HBL terms are not marked freshly verified |
| Correct bridge evidence claims | Recorded history is not verified business age; attachment is not audited authenticity; event counts do not prove recurring expenses; customer sales concentration uses all recorded credit sales as denominator |
| Preserve the team's live testing while automating checks | Servers 3001/8001 use the separate live-test ledger. Automated browser writes used a different owned API/database on 8002; no reset or synthetic write touched the team's live ledger or original PostgreSQL |
| Research the requested all-Vercel path before activating it | Current Services Beta supports Next + FastAPI in one project. Private permanent receipt storage, cloud request limits, real auth and multi-instance cache behavior remain release gates; do not call an environment import a deployed backend |

### Changed areas

- Backend: `ask_resolver.py`, `ask_answers.py`, Ask router/schema/engine guards, upload-time `evidence_storage.py`, capture/read/confirmation checks, cheap health/startup behavior, financing data/matching and common evidence/reference bridge mapping. Added operator-only ownership registration and provider-check scripts.
- Regressions: `test_ask_guards.py` (59 cases), `test_evidence_security.py` (14), `test_evidence_claims.py` (2), and one additional financing-catalog test; existing Ask/health/financing expectations updated. These add 76 tests to the first run's 89, for 165 total.
- Frontend: Ask response/source labels, bounded question length, Urdu text direction and evidence/source-verification wording. No second visual redesign or framework migration.
- Handoff: all three READMEs updated to this checkpoint; [booth runbook](REGIONAL_DEMO_RUNBOOK.md) and [Vercel plan](VERCEL_DEPLOYMENT_PLAN.md) added. `.vercel/` excluded before any project linking. Build-generated Next imports restored to their pre-audit dev-type state.

### Checks actually performed

| Gate | Result | Limit |
|---|---|---|
| Full backend suite | 165 passed | Offline isolated fixtures; existing Starlette/httpx warning remains; not live Supabase/RLS proof |
| Original frozen-clock question audit | 26/26 passed, previously 12/26 | Finite adversarial regression set, not a population accuracy statistic or new live-provider benchmark |
| Browser story | 27 checks passed | UI → API → actual fixture ledger → exact answer; 5,000 credit/2,000 repayment/3,000 customer balance; 8 extra date/language/unsupported cases, recovery/CSV/reminder/capture guards |
| Responsive routes | 15 passed | Five routes × desktop/tablet/phone; no root horizontal overflow, runtime errors or hidden phone composer |
| TypeScript + production build | Passed, 11 static pages | Node 22.23.3 / Next 16.3.8, local-demo configuration; dev server kept running during build |
| Ownership/cost regressions | Passed in suite | Cross-merchant attachment/read, forged legacy claim, traversal, both upload/confirm paths, failure cleanup and zero model calls from public health |
| Working-tree whitespace | Passed | Local secrets/databases remain ignored; no commit/push or real DB policy changes |

Evidence outside the repo: `tmp/regional-audit/run2-question-report.json`, `run2-ui/story-report.json`, `run2-ui/smoke-report.json`, route PNGs and isolated `run2_ui_story.cjs` / `run2_ui_smoke.cjs`. The question script now writes a run-specific report; historical 12/26 results are retained in this ledger. The complete browser story used the deterministic demo provider and preserves the distinction between SQL correctness and real recognition. Production dependency audit was clean in U1; dependencies were not changed in L1, and the eight development-tool findings remain tracked rather than claimed resolved.

### Next checkpoint and deliberate deferrals

**D1 next:** the user confirms the backend has never been deployed and explicitly authorizes a new Vercel project using the logged-in Chrome account. Verified the correct `Hassnoo999/Karobar-AI` repository in Vercel; its import screen detects both services but requires a repository-root `vercel.json`. Prepare the project without shipping the older uncommitted code or authentication-off local environment. Complete private storage/ownership adapter, managed DB access checks, cloud upload cap and cache freshness before a real cloud write/read/receipt/restart sign-off. Account/project creation results are recorded below when visibly verified.

**P1 after verified screenshots/demo:** regional deck with the merchant-centered hook, exact live flow, technology boundary and three-person speaking script. Runbook exists, but the old PPT is not yet updated.

**After regional:** full pagination/scalable queries; magic-byte verification and general orphan cleanup; rate limits/quota controls; migration/backup/observability strategy; expanded phrasing/dialect coverage, identity-switch clearing of local drafts/chats, live auth/accessibility/Safari/keyboard testing and development-tool dependency updates. Receipt ownership fixes do not replace these checks. No new inventory/profit/banking/automatic-message features in this window.

### D1 foundation — created with explicit team authorization

Created [`karobar-ai`](https://vercel.com/hassanbinsaqib01-5133s-projects/karobar-ai) in the team's logged-in Chrome account, Hobby plan, project ID `prj_kYTi4ovRgqXzdJV6ACG5ll9ffT7M`. Git settings visibly confirm `Hassnoo999/Karobar-AI` is connected. The first connection attempt did not show success; after a page refresh and a targeted second attempt, the page showed “Connected”. No claim was made from the click alone.

Created and connected `karobar-ai-receipts`, private Blob store `store_pIxxwbibXeqpr8D5`, Tokyo (`hnd1`). Dashboard verifies Private, empty storage and included Hobby quotas; no paid upgrade or long-lived read/write token selected. Vercel generated store-ID/public-webhook-key settings, but no existing `.env` secret was copied and no receipt was uploaded. These resource identifiers are not secrets. Screenshot proof is retained outside the repo in `tmp/regional-audit/vercel-project-connected.jpg` and `vercel-private-store.jpg`.

The correct import screen detects Next/FastAPI but requires the active root Services config in GitHub. Created a project shell rather than deploying stale code. **Application deployment is still pending**: cloud storage/ownership adapter, conservative upload limits, multi-instance freshness, private environment settings and approved DB scope, real Supabase isolation and actual cloud capture/restart checks. Continue with this existing project/store, not a duplicate. No Git commit/push, cloud application deployment or remote DB mutation occurred.

Handoff check: frontend dashboard returned HTTP 200; cheap backend health returned `ok`. Only the owned automated-fixture server on 8002 was stopped after verification. The team's 3001/8001 servers remain running; all live-test entries and isolated test files are preserved. Final diff/ignore checks pass. The evidence showcase screenshot now reflects the corrected recorded-history/concentration wording.

## D1 cloud implementation and release preparation — 10 October 2026

### Decisions and reasons

| Decision | Reason and result |
|---|---|
| Keep Next/FastAPI and five existing Ask tools | No framework/accounting rewrite; active Services config and Python 3.12 pin now exist and pass the current official schema |
| Fail closed on cloud development defaults | Validate at module import AND lifespan: serverless adapters may omit startup hooks. Require auth/Postgres/no auto-seed/private Blob; skip remote `create_all`; seed/reset return 403. Missing settings cannot publish a writable shared demo |
| Request-scoped OIDC for private Blob | Published Python SDK 0.11.6 lacks Blob OIDC support. Bounded transport follows official API v12; no long-lived RW credential created; hosted protocol still unverified |
| Server-selected immutable merchant namespace | Upload ownership survives function restarts without new DB tables. Check both confirmation paths before customer/event writes and require a confirmed attachment to read |
| 4 MB cap on every voice/receipt path | Multipart headroom below hosted request limit; reject before paid/storage work. Larger direct uploads deferred |
| Disable cloud process-local cache; mark responses private/no-store | One instance cannot invalidate another. Hosted second-browser freshness remains a gate |
| Remount private screens on identity change | Clear chat/draft state as well as snapshot; build/code reviewed, hosted two-account switch test pending |
| Thread-pool synchronous receipt confirmation | Avoid blocking unrelated requests while checking private storage |
| Safe provider/Blob failure messages | Do not echo upstream URLs/credentials. Invalid Blob metadata returns a controlled storage error |
| Reject cloud CORS wildcards and remove empty-to-wildcard fallback | Empty now means no cross-origin access; DB warmup also logs only exception class, not connection details |
| Restore original Supabase project | User restored paused project. Connection works again; no remote records/policies or original `.env` changed |
| Verify TLS with official Supabase public CA | Generic CA bundle did not trust this pooler. Downloaded from Database Settings, content matched, verified TLS passes. Public certificate is not a key; verification was not disabled |
| Bound cloud DB connections | One connection, no overflow, pre-ping and 12-second connect/acquisition limits; avoids per-instance default connection fan-out |
| Compatible dependency patches | Initial Python audit: 29 advisories in pip/PyJWT/urllib3. Pin PyJWT 2.15.0/urllib3 2.8.0, patch local pip 26.2.1; final installed audit clean. No forced frontend build-tool migration |

### Checks actually performed

| Gate | Result | Limit |
|---|---|---|
| Backend suite | **196 passed**, `pip check` clean | Offline SQLite/demo/mock Blob; 31 new cloud regressions over L1's 165, including import-time guard |
| Frontend build | **Pass**, declared webpack build, 11 pages; default Turbopack also passed | Node 22.23.3/Next 16.3.8; not hosted auth proof |
| Vercel config | Current official schema validates | Actual build/routing still pending |
| Installed Python dependencies | **0 known vulnerabilities** after patches | Not a penetration test; check fresh cloud resolution |
| Frontend production dependencies | **0 known vulnerabilities** | Eight dev-inclusive Tailwind/PostCSS/globbing findings remain tracked |
| Managed DB preflight | **Verified TLS**, both tables RLS enabled, no policies; anon/authenticated see zero rows | Read-only. Backend role bypasses RLS; API filtering essential, least-privilege role deferred |
| Live text extraction | Gemini: PKR 5,000 credit-sale correct | One synthetic Roman Urdu sentence; Groq text HTTP 429 |
| Live receipt extraction | Gemini: Naveed/PKR 5,000/credit-sale correct | One generated English receipt, no merchant data/ledger writes; camera/Urdu quality unverified |
| Known-secret scan | No matches in 151 candidate paths at scan time | Current DB/password/JWT/Groq/Gemini values only; not every possible historical credential |
| Current local UI smoke | Total udhaar returned PKR 100,000; unsupported profit request clarified; no browser warnings/errors | Read-only browser interaction against the team's preserved 3001/8001 servers |

Evidence outside Git: `backend-dependency-audit.json`, `backend-dependency-audit-patched.json`, `release_secret_scan.py`, `live_receipt_probe.py`, and handoff screenshots in `tmp/regional-audit/`. Earlier 26/26 questions, 27 browser-story and 15 responsive-route results remain the previous local checkpoint, not cloud results.

### Remaining release gates

- The user explicitly approved transferring the existing DB/JWT/Groq/Gemini values to this project. All four are now visibly verified as **Production-only Secret variables**. No private values printed, committed or added to `NEXT_PUBLIC_`.
- Eight non-secret Production settings, the validated public anon/publishable key and exact production CORS origin are saved. Actual hosted sign-in/database/receipt verification remains pending.
- Verify deployed unauthenticated rejection, two-account API isolation, private upload/confirm/read, fresh balances and persistence after cold start/redeployment. A frontend-only URL is not a working full-stack demo.
- Real microphone/Urdu photo quality and Groq quota remain open. Verified local servers/manual entry remain the booth fallback.
- Post-regional: least-privilege DB role, API/provider quotas/rate limits, magic-byte validation/orphan cleanup, migrations/backups/observability, expanded auth/accessibility/dialect checks, eight frontend dev-tool advisories. No inventory/profit/banking/automatic-message scope expansion.

Presentation is still the earlier deck; update it/video script after a verified demo URL. Append commit/push and hosted outcomes only once observed.

### GitHub release and first hosted build

Release `252123017a1e24e0d3c4c6172349edb4db9524f3` committed/pushed to `Hassnoo999/Karobar-AI` main (68 changed files). Local/remote SHAs match. Current `.env` files, databases/WAL files, receipts and `.vercel` metadata remain ignored. The shared data hook's old `.ts` implementation is replaced by its `.tsx` provider; the old source remains recoverable in Git history.

Git triggered Vercel deployment `2pvw7DkNkDC8U3aWSL4v5s9eyanN`. Dashboard reports **Ready**, duration 1m 34s, both services built. The landing page renders at `https://project-4ps4k.vercel.app/`, but `/api/health` and `/api/combined` returned **500** with cloud credentials still unconfigured. This is **not a usable full-stack demo** and must not be handed off for video recording yet. The import-time safeguard follow-up is committed separately; production credentials and actual API/auth/Blob verification remain the next boundary.

### Approved configuration and rebuild

Follow-up `daad3acea8454cd395d5f7be6c30c61066dfb8db` is pushed to main; its Git-triggered build also reported Ready. With the user's explicit approval, existing private credentials were transferred to the intended Vercel project. Bulk `.env` entry unexpectedly reset type/scope and initially saved four values as Config in Production/Preview. Each was corrected to Secret/Production, with visible saved-list verification **before** requesting the credential-enabled rebuild. No Preview deployment was requested. Original source keys were not rotated or changed; no values entered logs, screenshots or Git.

Frontend public key was validated as anon/publishable, then saved individually as Production Config. Exact `https://project-4ps4k.vercel.app` CORS origin is saved. Requested a clean Production redeploy of `daad3ac` with current settings, without reused build cache. Screenshot proof of the final four Secret/Production entries is outside Git at `tmp/regional-audit/vercel-production-secrets.jpg`. Hosted outcomes are appended only after observation.

Credential-enabled deployment `FTGSMEqAVb9YTh4tfnTNeSqNqKSV` built Ready, but both API probes still returned 500. Runtime logs identify `ModuleNotFoundError: psycopg`: the unbounded SQLAlchemy dependency resolved to a newer default PostgreSQL driver, whereas this app installs psycopg2. Pin SQLAlchemy to the locally tested **2.0.52**; do not change DB credentials or install a second driver solely to mask this mismatch. The signup screen also now checks for an issued session and shows an accessible email-confirmation notice instead of incorrectly redirecting an unconfirmed account. Retest/build and Git-triggered deployment follow.

After the driver pin/signup fix: all 196 backend cases passed again, `pip check` is clean, and the frontend production/TypeScript build passed (11 pages) with Node 22 selected for child processes. Known-secret scan found no matches in 150 candidate paths; whitespace checks pass. Supabase Site URL is still localhost with no redirect allowlist; requested approval for the exact production URLs and asked the user to sign in to the live app for the authenticated gate. These are not yet verified hosted sessions or confirmation-email delivery.

Fix commit `03a2a2e16bbb9a4c10741346c59ebcb3dbe36d68` is pushed; deployment `62ckvvXdUUdcPU5748ZTrMD9UauJ` reports Ready (1m 35s). Actual public probes: health **200/production**, combined without token **401**, invalid token **401**, HTTP provider verification **403**; each carries `no-store, private`. User created/signed into a new account themselves; retry in the authenticated browser loaded a genuinely empty cloud ledger. With separate explicit approval, exact production Supabase Site URL and sole `/signin` redirect were saved and visibly verified, without weakening email-confirmation policy. Auth screenshot is outside Git.

Hosted receipt test is still in progress. Browser extension file access blocked both automated attempts (the user reported enabling it between attempts); requested a manual upload of the clearly synthetic PNG into this new test account. Do not confuse this browser-permission failure with tested Blob behavior. No original merchant data or token was exported from the browser.

In the real hosted new account, `Total udhaar kitna hai?` returned **Rs 0**, labeled all-time confirmed history / ledger-calculated / rule-based. Asking for this month's profit returned the supported-tool boundary, not an invented profit figure. The separate QA tab has no browser warnings/errors. These are actual cloud checks, but not a broad phrasing-accuracy benchmark.

Production CORS probe allows the exact app origin, not an unrelated test origin; `nosniff` is present. Month-sales Ask returned Rs 0 explicitly for October 2026, not profit/cash balance. A user-uploaded draft was visibly named `receipt.png` and marked Demo AI with no extracted amount; it was **not confirmed**. The local image appears to contain personal bank-transfer details, so it was not used as the synthetic booth fixture. Cleared only the unconfirmed UI draft (not the original image/private uploaded object) and requested the generated, clearly labeled test image. Do not claim live hosted recognition from the Demo AI draft.

Added minimal safe fallback diagnostics after reviewing the existing Python integration: provider/capability/exception category/numeric HTTP status only, never exception text, merchant inputs or response bodies. Two regressions prove sensitive upstream/model text stays out of logs. **198 backend cases now pass**. No provider routing/model/accounting rewrite or new SDK migration was introduced during this release window.

### Hosted write exposed a concurrency defect — fix prepared

The agent confirmed one synthetic **PKR 500 cash sale**, `Regional QA Cash Test`, in the user's newly created test account. The screen reported Saved once. Overlapping `/api/combined` reloads then returned 500; Vercel runtime logs identify **QueuePool size 1 / overflow 0 / 12-second timeout**, not a missing record or JSON serialization error. The row and all other merchant data were preserved.

**Decision:** retain the bounded pool, accounting, auth filters and response contracts. Follow FastAPI's synchronous-I/O guidance: plain `def` for DB-only routes; offload the SQL phase of async Ask/capture routes. Reminder routes snapshot scalar ledger facts and close their read transaction before awaiting AI; receipt reads release the connection before private storage download. No concurrent sharing of a Session, new framework or larger connection fan-out.

**Evidence:** the new file-backed SQLite/QueuePool regression first reproduced **200/500/500/500** from four overlapping combined requests. After the fix, ten endpoint variants all return 200 and release their sole connection. Both reminder paths allow another ledger read during the mock provider wait; receipt download starts with no checked-out connection. Full isolated suite: **211 passed in 7.73 seconds** (13 new cases). This is a focused concurrency check, not a production load benchmark. Log: `tmp/regional-audit/cloud-concurrency-pytest.txt` outside Git. Hosted reloading of the original PKR 500 row after the next deployment remains the exit gate.

### Hosted core story passes; receipt viewer prepared

Pushed concurrency fix **`af53841b769938aef1faf69a5dd62d59b1185387`**; deployment `CzsXyjUJ3ZCDRb51LH4CPsFAezgr` visibly Ready, 1m 29s. Missing/invalid-token 401, health 200, paid-health 403 and private/no-store/nosniff checks still pass. The original cash entry **#69 / PKR 500** survives deployment; intentionally overlapping authenticated dashboard/ledger tabs both load correctly. This closes the specific reproduced pool-starvation gate, not large-scale load testing.

The user uploaded the correct `cloud-test-receipt.png` through the actual production website. Draft: **Gemini**, Regional Demo Customer, **PKR 5,000 credit sale**, 10 October 2026. Confirmed once as **#70**. A manual **PKR 2,000 repayment #71** also saved once. Cloud ledger now has three entries and **PKR 3,000 outstanding**; Ask returns that exact customer balance. Monthly sales answer correctly reports **PKR 5,500 = cash 500 + credit 5,000**, not profit/cash balance or sales plus repayment. These are actual Supabase-authenticated API/DB checks with synthetic test data, not demo-provider simulations. Screenshots: `cloud-receipt-gemini-draft.jpg`, `cloud-ask-customer-balance.jpg`, `cloud-ledger-persistent.jpg` outside Git.

**Small scope-fit improvement:** saved receipt evidence existed behind a protected API but had no product UI action. Added an on-demand native-dialog viewer to receipt-linked ledger rows. Authenticated binary fetch, supported-image MIME guard, loading/error/download states, abort on close/unmount and object-URL cleanup; no private storage URL or credential is exposed. Account remount also clears it. Reviewed against the installed Next client-boundary guide and React effect/accessibility guidance. Corrected the shared storage failure wording so a failed read does not falsely claim an already-saved entry was not saved. Backend storage/ownership/concurrency subset: **58 passed**. Fresh Node 22 TypeScript/production build: **11 pages passed**. Hosted original-image read across the next deployment is the remaining viewer exit gate; real microphone/Urdu-photo and two-account proof remain separate human rehearsal gates.

### Capture priority change — real APIs, no silent Demo substitution (10 October 2026)

User priority: fix voice/receipt output first, using existing APIs; postpone further unrelated improvements.

| Decision | Reason / outcome |
|---|---|
| Remove Demo from automatic and empty-provider fallback | A failed API must not fabricate recognition. Auto/Groq/Gemini modes contain real configured providers only; explicit Demo is local-test-only and unavailable on deployed environments. Product capture defensively rejects Demo results |
| Route receipts directly to the implemented Gemini capability | The configured Groq integration does not implement vision; skip that capability rather than log a misleading outage. Provider/config response now identifies Gemini truthfully |
| Do not force every recording into Urdu | Groq Whisper auto-detects language with deterministic temperature; preserve actual browser MIME and file extension. Voice review exposes both speech and extraction providers |
| Preserve receipt detail and require clarification | Apply EXIF rotation; retain small PNGs losslessly; cap larger photos at 2048px / JPEG 92. Gemini capture requests a nullable schema. Missing dates/purpose remain missing; a bank transfer is not automatically a repayment |
| Show AI notes in review | Uncertainty was returned by the backend but hidden by the product. Merchant now sees it beside the transcript/provider before confirming |
| Check empty recording and digital silence | Real Whisper returned `The` / `Thank you` for zero-signal audio. Reject digital silent PCM WAVs before paid calls; browser also checks decodable recorded audio for zero signal. Empty/short clips and recorder errors have explicit recovery. This is not a guarantee against noisy-room hallucinations |
| Keep accounting and merchant confirmation unchanged | No new event types, auto-save, balance arithmetic or existing-record rewrites. Existing local team data and cloud test entries preserved |

**Checks:** 26 new offline capture-boundary regressions; full suite **237 passed in 9.97s**, `pip check` clean. Fresh Node 22 webpack/TypeScript production build passes all 11 pages. Known-secret scan: **154 candidate paths, zero matches** before final documentation edits; private `.env` and generated fixtures remain outside Git. Tests use explicit mock/Demo fixtures; they are not paid-model accuracy measurements.

**Real API evidence:** Groq correctly extracted a PKR 5,000 Roman Urdu credit sale, PKR 2,000 previous-udhaar repayment, and left a generic PKR 5,000 incoming transfer unclassified. Gemini correctly extracted a PKR 2,500 cash sale and PKR 5,000 credit receipt; generic transfer preserved amount but left type/date unknown with review notes. The credit image initially received upstream **503 UNAVAILABLE** on multiple calls; a later structured-schema call succeeded. No Demo draft was substituted. A generated English WAV through the running `/api/understand/voice` pipeline returned Groq transcript + Groq cash-sale extraction for **PKR 2,500**. Local ledger count remained **63 → 63**: drafts were not confirmed. These synthetic probes are outside Git in `tmp/regional-audit/real_capture_probe.py`, `real_capture_followup.py` and `capture_diagnostic.py`. Do not claim real human Urdu/Punjabi microphone or handwritten receipt accuracy from them.

Previous receipt-viewer deployment **f70e56a / 73DRhxpEKVUYbZw5k14apJZqYxuL** is visibly Ready (1m24s), but hosted receipt reopening remains unverified. New capture changes are not hosted until a subsequent successful Git build is observed. Remaining capture exit gates: local silence rejection after the fix, live deployed provider chain and merchant voice/photo rehearsal. Provider capacity/quota remains an external reliability risk; manual entry is the honest fallback. A failed private-receipt extraction still cleans up its just-uploaded object.

### Capture release observed

Capture code **a714a6542676736e8df99870bf86a9ff00abd4a4** is pushed to main. Vercel Production deployment **3zTEUiTdXeXHvaqSuLdLhoD7BU77** visibly Ready (1m21s), assigned to `https://project-4ps4k.vercel.app`. Hosted config now reports **Groq → Gemini**, voice `[groq, gemini]`, receipts `[gemini]`, no Demo. Health 200/private-no-store; missing-auth voice and receipt requests both 401. Signed-in `/record` shows updated mixed-language guidance and API connected. No microphone permission was accepted or real recording made by automation.

Post-fix zero-signal WAV probe now rejects before provider work. Existing cloud entries #69/#70/#71 and **PKR 3,000 outstanding** survive this deployment. The receipt viewer opens the original synthetic #70 image from private storage, with Gemini source label and original download available; screenshot visually verified at `tmp/regional-audit/hosted-private-receipt-open.jpg`. This closes the previous hosted receipt-reopening gate. Release screenshot: `capture-release-ready.jpg`. No new hosted ledger entries were added during this capture-fix pass.

Exit status: focused implementation, full offline suite/build, real-provider synthetic recognition and deployed no-Demo routing **verified**. Real merchant microphone/dialect/handwritten-photo accuracy and two-account isolation remain separate rehearsal/security gates. Gemini returned intermittent upstream 503s in synthetic probes; no guarantee of API availability or perfect OCR/STT is claimed. Documentation follow-up records these observed results without changing capture code or cloud configuration.

## Resumed release repair — 10 October 2026

Baseline: working tree clean at `5ac3349`; requested Vercel deployment `jEACLmzRp98m1LDDEnmVhzFHD2H9` is Ready/Production at that same commit. No unfinished code change was found. Previous human microphone, two-account and provider-availability gates remain open; earlier test counts are not new verification.

Execute in order, with no accounting or feature expansion:

1. Receipt/voice reliability: diagnose numeric provider failures, enable and verify the existing Groq Qwen vision capability, keep Gemini fallback, provide safe actionable errors and retain the file for retry. Preserve unknown transfer purpose for merchant review; do not force it into sales or repayment.
2. Ask: reproduce composer clipping, repair viewport/grid sizing, verify supported ledger questions and unsupported boundaries.
3. Sign-in: single clean field border, calmer typography, CSS-only evidence-themed 3D decoration with reduced-motion support; keep real Supabase authentication.
4. Remove public sample-preview/session bypass entry points. Real data remains authoritative; offline test fixtures are not production recognition.
5. Run focused and full regressions/build, check secrets, commit/push and observe the actual production release. Record cloud verification separately from mocks.
6. Only after hosted verification, identify disposable test rows and request exact scope if mixed with merchant data. Never blanket-delete account history. Write a short plain-language changes report including deployment history and unresolved gates.

Screenshot finding: the successful personal-transfer image has ambiguous business purpose, so its blank transaction type is correct. The failure screenshot is a generic service error; the failed image is unspecified. Historical logs/real probes showed Gemini 503s, but the screenshot alone cannot establish the precise upstream cause. The current Groq integration explicitly disables receipt vision despite current Groq documentation supporting the configured Qwen family; verify a real call before releasing it.

### Resumed checkpoints prepared and checked

- Receipt cause confirmed in the requested deployment's actual Vercel warning log: `22:01:29`, `/api/understand/receipt`, Gemini `ServerError`, numeric **503**. No image-readability diagnosis is inferred from that provider outage. Proof is outside Git at `resumed-receipt-503-cause.jpg`.
- Groq now sends actual image bytes to Qwen vision with JSON output and a bounded 1,024-token completion; Gemini remains the real fallback. Legacy `groq/compound`/Compound-mini settings migrate only to the verified Qwen vision default. Fresh-key synthetic tests initially hit **429 / tokens per minute**, then **both Groq and Gemini passed credit PKR 5,000 and unclassified-transfer PKR 5,000 checks**. Generated English voice returned a PKR 2,500 cash sale through Groq. No ledger confirmations in these direct-provider tests.
- Categorized, application-owned failure messages propagate through both capture API shapes without upstream bodies. Corrupt/mismatched photos are rejected before storage/AI; HEIC conversion is explicitly required rather than pretending a decoder exists. Browser retry retains its file. New focused capture subset: **37 passed**; complete suite/build passed before final documentation and small follow-up edits, to be rerun before push.
- Ask layout measured on the old hosted build: textarea bottom **767px** on a **639px** viewport, proving clipping rather than a missing input component. Explicit `minmax(0,1fr)` grid rows, nonshrinking header/composer and scrolling examples panel repair it. New local screenshot shows the input within the viewport. Desktop local auth screenshot verifies no nested borders and input weight **400**; CSS-only proof animation is behind the content, respects reduced motion and introduces no library.
- Public sample-preview/session fallback, seed/reset HTTP routes and startup seed mutation removed. Seed-based regression fixtures remain isolated. Existing local/live merchant rows are preserved. Old sample fixture/router source removals are recoverable in Git history, not merchant-data deletion. Landing reminder example stays visibly illustrative; account/workspace links no longer advertise a sample bypass.
- Plain-language report created at `docs/LATEST_CHANGES.md`; frontend/backend/root READMEs updated for actual supported formats, real vision and removed sample controls. Remaining: final focused responsive/hosted verification, commit/push/Ready observation, then exact-scope disposable-data cleanup.

### Final local release gates

Full isolated backend suite: **249 passed in 15.90s**; `pip check` reports no broken requirements. Final Node 22 webpack/TypeScript production build compiles and generates all **11 pages**. These include the removed public sample routes/preview and the new receipt-validation/recovery contracts, not only the earlier capture subset.

Local desktop and narrow-screen browser checks: the Ask composer stays visible before and after a PKR 100,000 fixture-balance answer; messages scroll separately. Narrow viewport has no horizontal document overflow. Sign-in input has no inner border/outline and computed weight 400, with one wrapper focus treatment. Reduced-motion support remains enabled. Screenshots are outside Git (`resumed-chat-local-fixed.jpg`, `resumed-signin-local.jpg`). Hosted release and disposable-data cleanup are still pending at this checkpoint.

### Resumed hosted gates and scoped cleanup

Pushed **9fae755b2db0c37155c85bcc553ada9119061c60**. Vercel Production deployment **DG3RDDotx3YcQ18EXBdXkNZSkPBR** is visibly Ready, **1m05s**, assigned to the stable project domain. Actual probes: health 200/production; no-token combined/voice/receipt 401; paid HTTP health 403; removed sample seed/reset 404; private/no-store/nosniff and exact-origin CORS verified. Hosted config reports real Groq/Gemini vision, no Demo.

Hosted Ask textarea bottom **549px in a 639px viewport**, versus 767px before. All five queries returned the account's confirmed PKR 5,000 balance/customer/monthly sales and September→October comparison; profit returned the supported boundary. Sign-in screenshot/computed styles verify clean fields at weight 400 and CSS scene. Landing has account/workspace CTAs, not sample entry. Chrome automated file selection remains permission-blocked; the user manually selected the synthetic PNG. Actual hosted draft: **Groq / PKR 5,000 / credit sale / 10 October / Regional Demo Customer**, with an explicit synthetic-image note. Not confirmed; existing account's two rows remain unchanged. Proof: `resumed-production-ready.jpg`, `resumed-chat-hosted-fixed.jpg`, `resumed-signin-hosted.jpg`, `resumed-receipt-groq-hosted.jpg` outside Git.

After this receipt gate, exact QA IDs **69/70/71** were revalidated by read-only SQL: all synthetic fields matched, one owner with exactly three events. A SERIALIZABLE transaction backed up full target rows, removed only those events and one now-empty test customer, and checked global event count decreased by exactly three. Accounts/other rows/local 63-entry workspace/private Blob evidence preserved. Recovery artifact: `tmp/regional-audit/disposable-cloud-qa-backup.json` outside Git. No blanket deletion or Supabase auth/schema/permission changes.

### User-requested additional API backups

User supplied a separate Groq key and OpenRouter key; saved only in ignored backend `.env` and individually as **Secret / Production** in the same Vercel project, with visible saved-list verification. Warned that chat-disclosed keys should be rotated by the owner; no credential printed or committed. Primary credentials untouched. Official OpenRouter multimodal documentation and live model catalog confirm selected free Gemma model accepts images/JSON; key check 200/free tier. Separate Groq image test returned the synthetic PKR 5,000 credit sale. Both tested OpenRouter free Gemma endpoints returned **429**, so OpenRouter is configured but not signed off as available capacity.

Decisions: retain existing Python/httpx stack and validated extraction contract; no new AI SDK/accounting path. Auto order: Groq → separate Groq backup → Gemini → OpenRouter. Duplicate Groq keys skipped; Groq SDK automatic retries disabled in favor of adapter routing. OpenRouter is skipped for transcription, but can extract from its resulting text. Safe 402 funding/quota category added. Each capability bounded to 120s (voice has two phases, below the configured 300s cloud duration). Ten new routing/privacy/deadline/payload regressions; complete suite **259 passed in 15.86s**. No frontend source changes in this backup follow-up; prior final Node 22 build remains applicable. Backup release/hosted configuration observation follows after push.

Remaining: owner rotates chat-disclosed backup keys; OpenRouter free-endpoint capacity; human microphone/Urdu/Punjabi/handwritten-photo rehearsal; full two-account cloud isolation; tracked post-regional least-privilege DB role/rate limits/orphan object cleanup and eight development-tool dependency findings. No claim of 100% API availability or arbitrary-model accuracy.

## Update protocol

Second-run startup: frontend `127.0.0.1:3001` and backend `127.0.0.1:8001` are running for the team's live testing. The backend uses separate `tmp/regional-audit/run2-live.db` / `run2-live-uploads`, with existing configured AI providers; authentication is disabled only in this loopback test process. Original `.env` files/PostgreSQL are unchanged. Dashboard returned 200 with no browser errors and the known 63-entry seed totals. Preserve the team's new test entries; subsequent automated regression fixtures must not reset this live-test database. Next milestones: bounded Ask resolver/renderer, upload-time ownership, health/readiness trust corrections, focused end-to-end tests, then deployment/presentation gates.

After each checkpoint, record date, changed files, checks actually run, actual result, remaining risk and next checkpoint. Mark complete only after its exit gate passes. Do not reuse September verification claims as current measurements.
