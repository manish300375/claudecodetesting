# Architecture: SubsHub

Design points, stack, data model, tools and how to verify. Features are in [spec.md](spec.md); decisions and phases in [../Plan.md](../Plan.md).

## Design points

### Multi-tenancy
- One database. Every business-owned row has a `business_id`. Postgres **Row Level Security** policies are keyed on the session's business ID, and the super admin role bypasses them.
- **WhatsApp sender (shared now, own number later):**
  - Each business has a `wa_sender` setting: either `shared` (the platform's number, the default) or `own` (its own WABA ID and phone number ID).
  - Outgoing messages: the `MessagingChannel` looks up the business's sender, so moving a business to its own number is a settings change, not a code change.
  - **Templates on the shared number always name the business**, for example "Your bill from *{{business}}*", with the footer "Sent on behalf of {{business}} via SubsHub".
  - Incoming messages on the shared number are routed by the sender's phone number:
    - One matching customer: route straight to that customer's business.
    - Several matches: the bot asks "Which business?", and the choice sticks for the conversation.
    - No match: a polite "not registered" reply.
  - Incoming messages on an own number are routed by `phone_number_id`.
  - Meta charges are logged per business, so the per-customer fee covers them.
- **Protecting the shared number:**
  - Each business's send volume and the customer blocks and reports it causes are tracked. The super admin can throttle or suspend messaging for one business.
  - Reminders are rate-limited.
  - Marketing broadcasts are **off on the shared number**; only utility messages are sent.
  - A second registered standby number is kept ready for failover.

### Billing engine (the core, built and tested first)
- **Delivery bill** = Σ over days in the period of (scheduled quantity, adjusted by exceptions) × the price on that date. It handles mid-month price changes, pauses and extras.
- **Fixed plan** bills in advance per cycle. Proration is by days when the plan changes or is cancelled.
- Everything uses integer paise, so there are no floats. Tax is computed per line and rounded per invoice.
- The ledger is append-only. Bills, payments, credit notes and adjustments are entries, and the balance is derived from them, so no entry is edited in place. Corrections are made as reversing entries.
- Bill runs are idempotent: each bill is unique on (subscription, period).

### Payments (Razorpay with Route)
- Each business is onboarded as a **Route linked account** (needs its KYC: PAN, bank account, GSTIN).
- Each bill gets a **payment link** with transfer instructions to that business's linked account. The platform fee can be held back on the transfer or billed separately.
- Webhooks (`payment_link.paid`, `payment.captured`, `transfer.processed`, refunds) are verified by signature and stored raw. Each one posts a ledger credit, marks the bill paid or partly paid, and sends a WhatsApp receipt. Webhook handling is idempotent on the payment ID.
- Phase 2 option: **UPI Autopay mandates** (Razorpay Subscriptions or recurring payments) for fixed plans.
- A nightly reconciliation job compares Razorpay payments with ledger credits.
- **Compliance module for collect-and-split:**
  - Records TCS (GST s.52) and TDS (s.194-O) on each settlement to a business, using rates set in configuration and confirmed by your CA.
  - Produces monthly GSTR-8 data and 194-O reports, and gives each business a TCS/TDS certificate statement.
  - Tracks chargebacks and refunds against the business's next settlements.
  - The business's onboarding checklist covers Route linked-account KYC, the merchant agreement and the DPA.

### Platform billing (per active customer)
- An **active customer** is one with at least one subscription active on any day of the month, or with a bill raised that month. This definition is shown to businesses.
- A monthly job writes a usage snapshot, then raises the platform invoice. It is visible in the super admin and business consoles.

### WhatsApp (Meta Cloud API)
- Messages sent by the business (bills, reminders, broadcasts) use **pre-approved templates**, mostly in the *utility* category. Free-form replies are allowed only inside the 24-hour customer-service window. Meta charges per template message; this cost feeds into your per-customer price.
- Templates to submit early: `bill_raised`, `payment_received`, `payment_reminder`, `subscription_update`, `ticket_update`, `delivery_paused`.
- Every outgoing message goes into an outbox table processed by a queue, with retries and delivery-status webhooks (sent, delivered, read, failed).

## Stack
```
Next.js 15 (App Router, TS) ── UI: Tailwind + shadcn/ui (simple, consistent)
  ├─ /admin (super admin)   ├─ /app (business admin)   ├─ /api/webhooks/{razorpay,whatsapp}
Postgres (Supabase) + Drizzle ORM + RLS
Auth: Supabase Auth (email+password / email OTP) for admins; customers = WhatsApp number
Jobs: Inngest (bill runs, reminders, usage snapshot, reconciliation, message outbox)
Files: Supabase Storage (invoice/statement PDFs via @react-pdf/renderer)
Integrations: Razorpay (Payment Links, Route, webhooks), Meta WhatsApp Cloud API
Hosting: Vercel (Mumbai region functions) + Supabase ap-south-1 · Sentry for errors
```
Repo layout (in `claudecodeprojects/subscription/`):
```
src/app/(superadmin)/…  src/app/(business)/…  src/app/api/webhooks/…
src/server/billing/   (pure billing engine + tests)
src/server/ledger/    src/server/payments/razorpay.ts   src/server/whatsapp/{client,bot,templates}.ts
src/server/jobs/      src/db/schema.ts (Drizzle)  src/db/migrations/  src/pdf/
tests/ (vitest unit) e2e/ (Playwright)   CLAUDE.md (project rules)
```

### Built for extension and scale
- **Modular monolith:** one deployable app, split into domain modules: `tenancy`, `iam` (roles and permissions), `catalog`, `subscriptions`, `deliveries`, `billing`, `ledger`, `payments`, `messaging`, `support` and `platform-billing`. Each module exposes a service interface and owns its own tables. Modules never query each other's tables directly. This lets any module become a separate service later without a rewrite.
- **Domain events:** modules talk through events such as `invoice.created`, `payment.received`, `subscription.paused` and `wallet.low_balance`. An outbox table guarantees each event is delivered, and Inngest runs the handlers. New features subscribe to existing events instead of editing core code. For example, an SMS fallback or a Tally sync only needs to listen to `invoice.created`.
- **Adapters for every outside service:** a `PaymentGateway` interface (Razorpay Route now; own-keys Razorpay, Cashfree or Stripe later), a `MessagingChannel` interface (WhatsApp now; SMS or email later) and `PdfRenderer`.
- **Business-type profiles and settings:** a business type such as dairy, newspaper, gym or coaching is a set of defaults: units, billing mode, cycle, menu labels and templates. It is not hard-coded logic. Adding a new vertical then means adding configuration, not code.
- **Feature flags per business and per plan:** for example `wallet`, `autopay` and `delivery_staff`. The super admin turns modules on or off for each business, which also lets you sell premium add-ons.
- **Versioned API:** a public REST API at `/api/v1` with API keys per business, plus outgoing webhooks to the business's own systems. Integrations can then be added without changing the UI.
- **Scaling path:**
  - *Now:* indexes on `business_id`, and all heavy work (bill runs, broadcasts) done in background jobs with batching and per-business concurrency limits.
  - *Next:* read replicas for dashboards, and materialised views for KPIs.
  - *Later:* partition the large tables (`ledger_entries`, `wa_messages`, `delivery_days`) by business or month. Very large businesses can move to a dedicated database, because the code always goes through the tenant context.
- **Quality gates:** typed contracts between modules, a migration for every schema change, a test suite per module, and preview deployments for each PR.

### Core data model
`businesses`, `business_users`, `platform_plans`, `platform_invoices`, `usage_snapshots`
`customers`, `catalog_items` (+ `item_prices` with effective dates), `subscriptions`, `subscription_changes`, `delivery_exceptions`
`bill_runs`, `invoices`, `invoice_lines`, `invoice_sequences`, `ledger_entries`, `payments`, `payment_links`, `webhook_events`
`roles`, `role_permissions`, `user_roles`, `feature_flags`, `business_settings`, `domain_events`
`businesses.billing_mode` (postpaid now, prepaid later) · future tables: `advance_balances`, `balance_rules`
`tickets`, `ticket_messages` (scope: customer→business or business→platform)
`wa_conversations`, `wa_messages`, `wa_templates`, `message_outbox`, `audit_log`

## Tools, MCPs and accounts
**Already available in this Claude Code setup**
- `gh` CLI (GitHub repo, PRs, CI) and Docker (local Postgres if wanted).
- Skills: `run` (launch and check the app), `code-review` and `security-review` (before each phase merges; essential for payment and webhook code), `simplify`, `dataviz` (dashboard charts), `xlsx` (CSV and Excel customer import templates), `pdf` (to check generated invoice PDFs), `claude-api` (only if AI ticket triage is added later).
- The `Playwright/` setup in this workspace can be reused for end-to-end tests of the admin UI.

**MCP servers to add (recommended)**
- **Supabase MCP:** run migrations, inspect tables, check RLS policies.
- **Razorpay MCP** (official `razorpay-mcp-server`): create test payment links and orders, inspect payments and Route transfers in test mode.
- **Vercel MCP:** deployments, logs and environment variables.
- **Context7 (or similar docs MCP):** current docs for Next.js, Drizzle and the Meta Graph API.
- **Sentry MCP** (optional): debug production errors.
- WhatsApp has no reliable official MCP, so Claude calls the Meta Graph API directly from the code and tests it against Meta's test number.

**External accounts and credentials you will need**
- A Razorpay account with Route enabled. Test keys first, live keys after KYC.
- Meta Business Manager with WhatsApp Cloud API: an app, a phone number ID, a permanent access token and a webhook verify token.
- Supabase, Vercel, Inngest and Sentry accounts. A domain name.
- The platform's GSTIN, and a CA to review invoice formats and the Route fund-flow arrangement.

## Verification
- **Unit:** vitest suite for the billing engine (pauses, price change mid-month, proration, GST intra-state vs inter-state, rounding), ledger balance invariants, and webhook idempotency (replaying the same event twice gives one credit).
- **Integration:** Razorpay test mode. Create a bill, pay the link with a test UPI ID, then check the webhook, the ledger credit, the bill marked paid, the Route transfer and the WhatsApp receipt.
- **WhatsApp:** with Meta's test number, run the full bot menu path (subscriptions, bill, pay, ledger, pause, support ticket, then the admin reply arrives in the chat).
- **E2E (Playwright):** super admin creates a business, the business admin imports customers, runs billing and sees the dashboard update.
- **Prototype:** you approve it before Phase 1 starts.
- **Postpaid:** a bill run produces the correct month-end amount and ageing. A business's billing mode cannot be changed while it has open bills.
- **Permissions:** a test matrix checks every role against every protected action. For example, an Accountant cannot delete customers and Delivery Staff cannot see the ledger.
- **Multi-tenancy:** an automated test checks that business A's user can never read business B's rows (RLS).
- **Pilot:** a month of parallel running against a real business's existing register before going live.
