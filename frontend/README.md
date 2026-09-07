# Karobaar AI frontend

The frontend presents Karobaar as a simple merchant workflow instead of accounting software. It supports desktop and mobile screens for capturing transactions, checking the ledger, asking business questions, and reviewing financial evidence.

## Main routes

| Route | Purpose |
|---|---|
| `/` | Public product story and hackathon landing page |
| `/signin` and `/signup` | Supabase authentication when configured |
| `/dashboard` | Monthly sales, expenses, udhaar and recovery overview |
| `/record` | Voice recording and receipt upload with a review step |
| `/ledger` | Searchable ledger, udhaar filters and CSV export |
| `/ask` | Ledger-grounded business questions |
| `/evidence` | Financial Evidence Passport, financing matches and reminder draft |

## Local setup

Use Node.js 22 or later.

```powershell
npm ci
Copy-Item .env.local.example .env.local
npm run dev
```

Open `http://localhost:3000`. The FastAPI backend should run at `http://localhost:8000`.

For the local single-shop demo, leave the two Supabase values empty. The app will connect to the backend's `demo` merchant. For any shared deployment, configure both values and enable `REQUIRE_AUTH=true` in the backend.

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
```

## Useful commands

```powershell
npm run dev
npm run build
npm start
npm audit --omit=dev
```

## Data behavior

- Product screens request `/api/combined` to avoid repeated database round trips.
- A visible demo fallback keeps the hackathon walkthrough usable when the API is unavailable.
- When Supabase is configured, protected routes wait for the restored session and redirect unauthenticated visitors to `/signin`.
- The frontend displays AI output as a draft. The merchant must confirm it before saving.
- Financing evidence remains qualitative and never presents a numeric credit score.

## Technology

- Next.js 16 and React 19
- TypeScript and Tailwind CSS
- Supabase Auth
- Framer Motion, GSAP and React Three Fiber for the landing experience

See the repository-level [`README.md`](../README.md) for the product story, architecture, complete setup, screenshots and safety boundaries.
