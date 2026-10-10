# Latest changes — plain-language release notes

Updated: 10 October 2026. This covers the recent release runs and the resumed repair. Code checks, real API checks and hosted checks are recorded separately; a passing test is not a promise of perfect AI accuracy.

## Receipt recognition uses both real APIs

Groq receipt processing was disabled, so a Gemini outage had no second receipt provider to try. The integration now sends the actual image to Groq's Qwen vision model and falls back to Gemini when needed. Both providers correctly read a synthetic PKR 5,000 credit receipt and left a generic transfer's business purpose unknown. Old Compound vision settings are mapped to the supported vision model.

## The reported receipt failure has an identified cause

Vercel logs show that the failed hosted receipt request at 22:01 received Gemini HTTP 503. That was an upstream service failure, not evidence that the image was unreadable. Fresh Groq tests also temporarily hit its token-per-minute limit (429), then passed when capacity became available. Replacing an API key does not necessarily reset account quota or prevent provider outages.

## Clear errors and useful recovery

The app now distinguishes a busy provider, quota limit, timeout, configuration problem and unusable AI output. Messages explain the next action without exposing keys or private provider responses. Retry reuses the same selected capture; choosing another file and manual entry are separate options. No failed recognition creates a ledger entry.

## Receipt file checks happen first

Corrupt files and misleading file types are rejected before private storage or paid recognition. The upload limit remains 4 MB, with a 25-megapixel decoded-image limit. JPEG, PNG and WebP are supported; HEIC must be exported to JPEG first because this server has no HEIC decoder. Small PNG receipts stay lossless, and camera orientation is corrected.

## Voice capture is real, with review before saving

Whisper detects the spoken language rather than forcing every recording into Urdu. The browser preserves the recording format and handles denied microphones, empty recordings and short clips. Digital silent WAVs are rejected before provider calls, and review displays the transcript and actual providers. Generated English speech and Roman Urdu text passed focused checks; real people speaking in booth noise still need rehearsal.

## Ask keeps the input visible

The conversation grid could grow beyond its allotted height and push the question box off-screen. Its message track now shrinks and scrolls independently, while the header and composer keep their space. The right-hand examples panel can scroll on shorter screens. Financial answers still use the five supported ledger tools; unsupported profit or loan questions do not receive invented numbers.

## A cleaner sign-in page

Fields now have one outer border and one accessible focus treatment, not nested green boxes. Labels and input text use calmer weights, with appropriate email/password autocomplete. The background has a subtle receipt-and-voice composition using CSS 3D transforms, not a new graphics library. Reduced-motion preferences stop the animation, and real Supabase authentication is unchanged.

## One real merchant workspace, no public sample pipeline

“Open live demo” now leads to real account creation or sign-in, and the sample-preview option is removed. Missing authentication configuration no longer simulates a successful login. The backend's sample seed/reset routes and automatic startup seeding are removed, so they cannot populate or erase an account through HTTP. Isolated test fixtures remain for repeatable QA; existing merchant records have not been blanket-deleted.

## The backend is on Vercel too

Yes: the repository's Vercel configuration deploys both the Next.js frontend and FastAPI backend in one project. The browser calls `/api` on the same domain; those requests reach FastAPI, which uses Supabase PostgreSQL/Auth and private Vercel Blob receipt storage. This is not a frontend-only deployment. Use `https://project-4ps4k.vercel.app/` as the stable public address.

## What went wrong during deployment, and what was fixed

The Supabase project first needed restoration and production authentication URLs. An unexpected database-driver change was fixed by pinning the tested SQLAlchemy version; overlapping requests were then fixed by releasing database connections before slow AI/storage work, without enlarging the pool. Server-only production secrets and private receipt storage were configured, and saved receipts gained an authenticated viewer. Synthetic ledger records and their balances survived subsequent deployments.

## Why Vercel shows several URLs

The short project domain follows the current production release. The `git-main` address follows the branch, while the random deployment address identifies one particular build. They are aliases/build addresses for the same project, not separate frontend and backend applications. Share the short stable domain; production email redirects and CORS are configured for it.

## Verification and remaining limits

The UI/capture release is Ready on Vercel, and the user-uploaded synthetic receipt returned real Groq/PKR 5,000/credit sale without a ledger confirmation. All five hosted Ask tools matched confirmed records; profit was explicitly unsupported. The final backend suite has 259 passing cases, and the unchanged frontend has a passing 11-page production/TypeScript build. Real microphone/dialect, handwritten-photo quality, full two-account isolation and provider capacity still need their separate checks; perfect AI accuracy is not claimed.

## Optional backup credentials and OpenRouter vision

The fallback order is Groq, a separate Groq backup key, Gemini, then optional OpenRouter; the production release is Ready and reports that exact chain. The extra Groq key passed real receipt recognition and synthetic speech-to-transaction extraction; duplicate keys and repeated SDK throttling retries are skipped. OpenRouter officially supports vision, and its key validated, but both tested free Gemma endpoints returned 429, so it is not counted as guaranteed backup capacity. Its chosen model handles text/receipts, not transcription; safe errors distinguish funding from throttling, and each capability has a 120-second overall deadline.

## Disposable data was removed carefully

Only our earlier QA entries #69, #70 and #71 were removed, together with their now-empty synthetic customer. A read-only inspection first verified their names, amounts, sources, shared owner and absence of other history in that account. Cleanup used one guarded database transaction and saved recovery data outside Git; accounts, real records and original private evidence objects were preserved. The new receipt check remains an unconfirmed draft, not another test transaction.

Detailed checkpoint evidence: [implementation ledger](REGIONAL_ROUND_IMPLEMENTATION_LEDGER.md). The presentation/video remains a separate next step.
