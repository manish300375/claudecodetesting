# Plan: SubsHub (working name)

Multi-tenant subscription management for small Indian businesses. Three levels: super admin, business admin (web) and customer (WhatsApp only).
Detail: [docs/spec.md](docs/spec.md) for features, [docs/architecture.md](docs/architecture.md) for design, stack, data model, tools and testing.

## Status
- Plan agreed with the product owner on 30 Oct 2026.
- **Now:** Step A, the clickable prototype. No application code until the owner signs it off.

## Decisions
| Topic | Decision |
|---|---|
| Market | India: INR, GST optional per business (non-GST businesses issue a bill of supply), UPI |
| Business types | Daily delivery and fixed-plan services |
| Customer channel | WhatsApp only. The web UI is for the super admin and business admins only |
| Billing mode | One mode per business, never mixed. **MVP is postpaid only**; prepaid comes later |
| Deliveries | Delivered quantity comes from the schedule. Pause, skip and extra are recorded as exceptions |
| Money flow | Platform collects and splits through Razorpay Route. TCS, TDS and chargeback handling are in scope. **Payments are blocked until Razorpay and a CA approve** |
| WhatsApp | One shared platform number, and every message names the business. A business can move to its own number later as a paid upgrade. Platform pays Meta |
| Platform pricing | Per active customer per month (rate not set yet) |
| Roles | Platform: Super Admin, Support, Finance. Business: Owner, Manager, Accountant, Delivery Staff, plus custom roles |
| Cash collection by staff | Later phase. In the MVP, only admins record cash |
| Stack | Next.js + TypeScript, Supabase Postgres with RLS, Drizzle, Inngest, Vercel |
| Builder | Owner with Claude Code, part-time. About 16-20 weeks to pilot |
| Rules | Payments clear the oldest bill first. Customer opt-in is recorded. No invented figures; rates come from the CA, Meta or Razorpay |

## Phases
**Step A: Prototype**
- [ ] Clickable prototype in `prototype/index.html` with three views: super admin, business admin, WhatsApp simulator
- [ ] Owner walkthrough and feedback rounds
- [ ] Owner sign-off

**Phase 0: Setup and approvals (weeks 1-2; approvals take 2-6 weeks)**
- [ ] Go/no-go gate: Razorpay confirms in writing that Route fits this use
- [ ] Go/no-go gate: CA opinion on TCS, TDS, GST on advances and the bill-of-supply format
- [ ] Meta or a BSP confirms that one number may send utility messages for many businesses
- [ ] Meta Business verified, shared number registered, utility templates submitted
- [ ] Razorpay account with Route activated
- [ ] Platform GST registration
- [ ] Merchant terms, DPA and consent wording drafted
- [ ] Repo scaffolded with CI (lint, typecheck, test)

**Phase 1: Core data and admin CRUD (weeks 2-5)**
- [ ] Module skeleton, event outbox and feature flags
- [ ] Schema with RLS, and the tenant-context test
- [ ] Admin login, roles and the `can()` permission check, audit log
- [ ] Super admin can create a business
- [ ] Customers with CSV import, catalogue, subscriptions, delivery sheet and exceptions

**Phase 2: Billing and ledger (weeks 5-9)**
- [ ] Billing engine with unit tests
- [ ] Bill runs with preview and confirm, invoice numbering, PDFs
- [ ] Ledger, manual payments, credit notes, statements

**Phase 3: Payments (weeks 9-11)**
- [ ] Payment links with Route transfers
- [ ] Webhooks that update the ledger, payment receipts
- [ ] Reconciliation, TCS and TDS records

**Phase 4: WhatsApp (weeks 11-14)**
- [ ] Outbox and templates
- [ ] Inbound routing, including "Which business?"
- [ ] Bot menu, pause and skip, tickets, inbox, reminders
- [ ] Protections for the shared number

**Phase 5: Platform billing and dashboards (weeks 14-16)**
- [ ] Usage snapshots and platform invoices
- [ ] Tickets from businesses to the platform
- [ ] Super admin and business dashboards

**Phase 6: Hardening and pilot (weeks 16-20)**
- [ ] Backups, Sentry, rate limits, data export, DPDP notice
- [ ] Pilot with one dairy and one gym, running a month in parallel with their old register

**Later:**
- Own WhatsApp number per business
- Prepaid (advance balance)
- Staff cash collection
- UPI Autopay
- Hindi and regional languages
- Tally export
- AI triage of tickets

## Risks
- **Route and compliance (highest).** This is the Phase 0 gate. If Razorpay or the CA says no, switch the `PaymentGateway` adapter to each business's own Razorpay account.
- **Shared WhatsApp number.** All businesses share one quality rating and one policy position, so one business can hurt all of them. The fallback is each business's own number.
- **Part-time pace.** Each phase must work on its own. If time runs short, cut dashboards before billing correctness.
- **Meta and Razorpay costs.** Their charges feed into the per-customer price. Rates are not set yet.
- **DPDP Act.** Needs consent, a DPA, and data export and deletion.
- **Customers without WhatsApp.** The fallback is cash entry and printed bills. SMS comes later.
