# Deploy both Karobaar apps on Vercel

Checked 10 October 2026. **Project/private storage created and cloud code implemented; hosted end-to-end approval remains pending.** Chrome verifies the intended account; the connector is linked elsewhere. The user restored the paused original Supabase project; connectivity now works. No remote records/policies, original environment files or paid-plan settings were changed by this release work.

## Created and visibly verified

- Project: [`karobar-ai`](https://vercel.com/hassanbinsaqib01-5133s-projects/karobar-ai), in `hassanbinsaqib01-5133's projects`, Hobby plan.
- Project ID: `prj_kYTi4ovRgqXzdJV6ACG5ll9ffT7M` (an identifier, not a credential).
- GitHub connection: `Hassnoo999/Karobar-AI`; Vercel's Git settings show “Connected”. Release commit/push status is recorded in the implementation ledger.
- Private receipt store: `karobar-ai-receipts`, `store_pIxxwbibXeqpr8D5`, Tokyo (`hnd1`). Creation succeeded; dashboard shows **Private**, empty storage and Hobby included quotas. No upgrade was selected. No receipt data was uploaded.
- Store connection created `BLOB_STORE_ID` / `BLOB_WEBHOOK_PUBLIC_KEY` in the project's Production and Preview environments. The optional long-lived read/write-token checkbox was left off; prefer the SDK's rotating OIDC authentication on Vercel. “Not Protected” on the store refers to its optional firewall badge, not public blob access.
- This is **not yet a verified public demo**. Active Services config and the private storage adapter exist; environment provisioning, actual cloud builds and end-to-end checks remain required.

## In simple words

Vercel can run the website and its Python API together. The database must still live in a permanent database service, and receipt photos must live in permanent private storage. Uploading environment variables supplies settings/keys; it does not automatically turn the Python folder into a running backend.

| Part | Recommended location | Reason |
|---|---|---|
| Next.js frontend | Vercel frontend service | Existing UI, one public domain |
| FastAPI backend | Vercel Python service | Existing accounting/API, no framework rewrite |
| Database and authentication | Existing Supabase project, after access checks | Reuse the managed identity/database instead of moving real data |
| Receipts and ownership | Private Vercel Blob store, with a storage adapter | Images and server-recorded ownership must survive function restarts |

[Vercel Services](https://vercel.com/docs/services) supports a single-project frontend/backend arrangement and is currently Beta on all plans. Retain the verified local booth demo as the cloud fallback.

## Implemented safeguards and remaining gates

1. **Private receipts implemented:** uploads, ownership checks, confirmed reads and failed-extraction cleanup use a server-selected merchant namespace in private Blob. Published Python SDK 0.11.6 is RW-token-only; a small transport follows official `vercel/storage` API v12 and uses `vercel.oidc` request credentials. Mocked ownership tests pass. Actual hosted OIDC/Blob/cold-start behavior remains unverified; no long-lived Blob token created.
2. **Database checked read-only:** restored Supabase pooler connects with `verify-full` and its official public CA. Both tables have RLS, no browser policies, and zero visible rows for anon/authenticated probes. Backend role bypasses RLS: retain API merchant checks and schedule a least-privilege role. Cloud startup never creates/seeds tables and blocks reset/seed routes. Use a dedicated test account for hosted checks; never reset existing merchants.
3. **4 MB upload cap implemented** in UI and all voice/receipt endpoints, below the ordinary [Vercel Functions limit](https://vercel.com/docs/functions/limitations). Oversize tests make no model calls. Actual hosted multipart sizes still need checking; larger direct uploads remain deferred.
4. **Freshness/privacy implemented:** cloud snapshots skip process-local cache, API responses use `private, no-store`, and account changes remount private chat/draft state. Verify fresh balances from another browser after a cloud write.
5. **Hosted auth/providers still need proof:** configure the original Supabase public settings, server secrets and auth return URLs; test two-account API isolation. Gemini text and synthetic English receipt extraction passed; Groq text returned 429. Real microphone/dialect/photo quality and hosted capture remain separate gates. Demo output is explicitly labeled.

Keep the existing accounting and five Ask tools. These are deployment gates, not a mandate to rebuild the stack.

## Configuration recipe

Use the GitHub repository root—not only `frontend/`. The active [`vercel.json`](../vercel.json) defines both services, Tokyo routing and backend limits, and validates against Vercel's current schema. The following is a minimal illustration; the repository file is authoritative.

```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "services": {
    "frontend": {
      "root": "frontend/",
      "framework": "nextjs"
    },
    "backend": {
      "root": "Backend/",
      "framework": "fastapi",
      "entrypoint": "app.main:app"
    }
  },
  "rewrites": [
    { "source": "/api/(.*)", "destination": { "service": "backend" } },
    { "source": "/(.*)", "destination": { "service": "frontend" } }
  ]
}
```

Paths are case-sensitive: `Backend/` and `frontend/`. Preserve `/api/...`; FastAPI already includes that prefix. Build/runtime overrides belong inside the relevant service. See the [configuration reference](https://vercel.com/docs/services/config-reference). Pin Python to a supported version such as 3.12; keep Node 22.x. [Vercel's Python runtime](https://vercel.com/docs/functions/runtimes/python) supports the existing FastAPI entrypoint convention.

## Environment settings

Services share project environment settings. Only deliberately public values may use `NEXT_PUBLIC_`. Never paste private values into chat, Markdown, screenshots, GitHub or build logs.

| Variable | Cloud value/purpose |
|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | `/api` for same-domain Services; never localhost |
| `NEXT_PUBLIC_SUPABASE_URL` | Public URL of the intended Supabase project |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Public anon/publishable key, never service-role/JWT secret |
| `SUPABASE_URL` | Same Supabase URL for backend JWT verification |
| `SUPABASE_JWT_SECRET` | Server-only, only if existing HS256 tokens require it; asymmetric tokens use JWKS |
| `DATABASE_URL` | Private pooled PostgreSQL connection string with SSL |
| `ENVIRONMENT` | `production` |
| `REQUIRE_AUTH` | `true` |
| `AUTO_SEED` | `false` |
| `RECEIPT_STORAGE` | `vercel_blob` |
| `BLOB_STORE_ID` | Supplied by the connected private store |
| `CORS_ORIGINS` | Exact trusted site origin(s), no blanket wildcard |
| `AI_PROVIDER` and model names | Existing supported settings, with tested models |
| `GROQ_API_KEY`, `GEMINI_API_KEY` | Backend-only secrets |
| Blob credentials/store settings | Provided by the connected private store and implemented adapter, not a local path |

Prefer separate Preview credentials/data. Preview builds should not write to the real merchant ledger. Importing keys into Vercel's private settings is not itself a leak; public commits or private keys under `NEXT_PUBLIC_` require provider-side rotation, not just deleting the file later.

## Actual deployment order

1. Account/project, GitHub link and private store creation are complete. Check costs/plan requirements before any further paid resources; do not create duplicate projects/stores.
2. Cloud adapter/guards and managed DB checks are implemented. Finish secure environment provisioning. Browser transfer of existing private keys requires explicit team approval; never send values in chat. Prefer Production-only secrets; Preview must not write to the original merchant DB.
3. Services config/Python pin are present. Confirm root, environment scopes, Supabase redirects and deployment protection intentionally.
4. Commit/push as authorized, then inspect the actual Git-triggered build. Missing settings intentionally prevent backend startup. A frontend URL alone is not a successful full-stack deployment; never disable auth to manufacture a live demo.
5. Sign in, save a fresh test entry, reload, and compare dashboard → ledger → Ask → reminder. Confirm a second account cannot read/attach the first account's receipt or records. Test missing/expired tokens.
6. Upload a real small receipt and short voice note; inspect provider/draft labels. Revisit saved data after a fresh deployment/cold start. Test phone layout and actual upload limits.
7. Enable intended judge access only after checks pass; promote the verified deployment and update the deck/QR with its actual URL. Keep the local demo and screenshots.

If account/storage provisioning or real auth cannot be verified in the remaining window, demonstrate the honest local working app and state cloud deployment is unfinished. Do not remove authentication, ownership or persistence to manufacture a live link.

Record outcomes in the [implementation ledger](REGIONAL_ROUND_IMPLEMENTATION_LEDGER.md); rehearse with the [booth runbook](REGIONAL_DEMO_RUNBOOK.md). The regional deck update is a separate checkpoint.
