# CLAUDE.md: SubsHub (working name)

Multi-tenant SaaS for Indian subscription businesses. Three levels: super admin, business admin (web), customer (WhatsApp only). MVP: postpaid only, shared WhatsApp number, Razorpay Route collect-and-split.

**Read only the section you need:** `Plan.md` for decisions, phase checkboxes and risks; `docs/spec.md` for features; `docs/architecture.md` for design, data model and testing. Don't load these files with `@`.

## Structure
- `Plan.md`, `docs/`: plan and specs
- `prototype/index.html`: clickable prototype, dummy data
- `src/app/`: Next.js routes (superadmin, business, api/webhooks)
- `src/server/<module>/`: billing, ledger, payments, messaging, iam, …
- `src/db/`: Drizzle schema, migrations
- `tests/`: vitest · `e2e/`: Playwright

## Run and test (once scaffolded)
`npm run dev` · `npm test` · `npm run e2e` · `npm run lint && npm run typecheck`

## Tools
Next.js + TypeScript, Supabase Postgres (RLS), Drizzle, Inngest, Vercel. Razorpay and Meta in **test mode only**.
## Conventions
- Money is integer paise. Never use floats.
- Every tenant query runs with a `business_id` context. Guard actions with `can()`.
- Modules call each other through services or events, never each other's tables.
- Outside services go behind adapters (`PaymentGateway`, `MessagingChannel`).
- Shared-number templates must name the business.
- Never invent figures; use placeholders.
- Run `/code-review` and `/security-review` before merging payment or webhook code.

## Never
- Edit or delete ledger entries. Correct them with reversing entries.
- Edit an applied migration.
- Commit `.env` or keys, or use live payment keys.
- Change Plan.md decisions without asking.
- Touch folders outside `subscription/`.
