# Feature spec: SubsHub

What each user level can do. Decisions and phases are in [../Plan.md](../Plan.md); design is in [architecture.md](architecture.md).

### 1.1 Super admin console
- **Instances:** create a business (name, GSTIN, address, logo, business type, WhatsApp number, Route linked account), suspend or reactivate it, log in as its admin for support (logged in the audit trail).
- **Cross-tenant view:** see every business's customers, bills, payments and tickets, with a global search.
- **Platform billing:** price plan per business (rate per active customer, minimum fee, free customers). A monthly job counts active customers and raises a GST invoice to the business. The fee is collected by deducting it from Route settlements, or by payment link if settlements don't cover it. Shows a platform ledger for each business.
- **Complaint tickets (business to platform):** businesses raise tickets from their admin panel. The super admin sees a queue with status, priority, assignee, SLA and replies.
- **Platform dashboard:** active businesses, active customers, GMV collected, platform revenue, overdue platform invoices, open tickets.
- **Settings:** WhatsApp template library, GST rates, Razorpay keys, staff super-admin users.

### 1.2 Business admin web app (simple, mobile-friendly)
Navigation is kept to 7 items: **Dashboard · Customers · Catalogue · Deliveries · Billing · Messages · Support**.

- **Customers (CRUD):** name, WhatsApp number (unique per business), address, area or route, opening balance, notes and tags. Bulk import from CSV or Excel. Each customer has a profile with tabs for subscriptions, ledger, bills, messages and tickets.
- **Catalogue:** products and plans.
  - *Delivery item:* unit (litre, packet, can), price per unit, GST rate or HSN code, and optional date-ranged price changes.
  - *Fixed plan:* price, billing cycle (monthly, quarterly, yearly), GST rate or SAC code.
- **Subscriptions:**
  - *Delivery:* item, quantity per day, frequency (daily, alternate days, chosen weekdays), start and end dates.
  - *Fixed:* plan, start date and next bill date.
  - Actions: pause, resume, change quantity or plan from a date, and cancel.
- **Deliveries:** a daily sheet per route generated from the schedule. Edit exceptions (skip, extra, pause range) for one customer or in bulk, for example a holiday. Prints or exports a route list for the delivery staff.
- **Billing:**
  - A bill run, monthly or on a cycle date, for all customers or a selection.
  - Delivery bills are calculated from the actual deliveries in the period. Fixed plans bill in advance, with proration on mid-cycle changes.
  - GST tax invoices (CGST and SGST, or IGST) or a bill of supply for non-GST businesses and exempt items. Sequential numbering per business per financial year.
  - Preview, then confirm. Bills send on WhatsApp with a PDF and a Razorpay payment link.
  - One-off bills or charges, credit notes, discounts and late fees.
- **Ledger per customer:** a running statement of debits (bills, charges) and credits (payments, credit notes, adjustments) with the balance. Payments update it automatically from the Razorpay webhook. Admins can record **cash or direct-UPI payments** manually. Statement PDF.
- **Messages (WhatsApp):** automatic messages for a new bill, payment received, payment reminders (for example 3 days, due date, then 7 days overdue), subscription paused or resumed, and ticket updates. Manual broadcasts to a segment use approved templates. A shared inbox shows customer replies.
- **Support (customer tickets):** tickets raised from WhatsApp land here. Admins assign, reply (the reply goes out on WhatsApp) and close. The admin can also raise their own ticket to the super admin.
- **Dashboard:** active customers, this month's billed vs collected, outstanding and ageing buckets (0-30, 31-60, 60+), today's delivery totals per item, open tickets, top defaulters, new and churned customers.
- **Staff users:** the owner adds staff and gives each a role (see 1.4).

### 1.3 Customer (WhatsApp bot)
On any message, the customer gets an interactive list menu:
1. **My subscriptions:** current items or plans, quantity, next bill date.
2. **Latest bill:** bill summary, invoice PDF and a **Pay now** link (Razorpay payment link: UPI, card or netbanking).
3. **Pay dues:** total outstanding with a pay link.
4. **My ledger:** last 10 entries as text, plus a statement PDF.
5. **Pause / skip delivery:** date picker through WhatsApp Flows, or quick buttons ("Skip tomorrow", "Pause from... to..."). Each business sets a cut-off time.
6. **Support:** pick a category, type the issue, get a ticket number. Admin replies arrive in the same chat.
7. **Talk to business:** hand the conversation to a human in the admin inbox.

Customers are identified by their WhatsApp number. On the shared platform number, a customer of two businesses first picks the business. Every bot message shows the business name at the top.

### 1.4 Roles and permissions (RBAC)
Permissions are named actions, such as `customers.write`, `billing.run`, `ledger.adjust`, `payments.record_cash`, `messages.broadcast`, `tickets.reply`, `settings.manage` and `platform.impersonate`. Roles are sets of these permissions. Every API route and server action checks permissions through one `can(user, permission, businessId)` guard, and the UI hides anything the user is not allowed to do. Postgres RLS is a second layer that keeps each business's data separate.

| Level | Built-in roles | Scope |
|---|---|---|
| Platform | **Super Admin** (everything), **Platform Support** (read all, tickets, impersonate with audit), **Platform Finance** (platform billing only) | All businesses |
| Business | **Owner** (everything incl. staff & settings), **Manager** (customers, subscriptions, deliveries, messages, tickets), **Accountant** (billing, ledger, payments, reports), **Delivery Staff** (view route sheet, mark exceptions; read-only otherwise) | Own business |
| Customer | **Customer** (own data only, via WhatsApp) | Own record |

- The owner can create **custom roles** by ticking permissions. Built-in roles cannot be edited.
- Sensitive actions are written to `audit_log` with who, what, before/after values and the time. These include ledger adjustments, write-offs, deleting a customer, changing a price, refunds and impersonation.
- Optional maker-checker rule: adjustments above a set amount need approval from the Owner.

### 1.5 Billing mode: postpaid now, prepaid later
- Billing mode is **one setting per business**, chosen when the super admin creates the instance.
- A business is either postpaid or prepaid, never both. The mode cannot be changed while the business has open bills.
- **The MVP builds postpaid only.** The `billing_mode` field is in the schema from day one, so prepaid can be added later without a data migration.

- **Postpaid (MVP)** (common for milk and newspapers): the business delivers or serves first, then bills at the end of the cycle for actual usage. Payment terms are set per business (for example, due in 7 days). Ageing reports and reminders cover overdue bills.
- **Prepaid (future phase; design kept here for reference):**
  - *Wallet or advance balance* (common for delivery): the customer tops up through a WhatsApp pay link, and each day's delivery is debited automatically from the balance. Low-balance alerts go out on WhatsApp at a threshold. A business setting decides what happens at zero balance: pause deliveries, or allow credit up to a limit.
  - *Advance plan purchase* (common for gyms and coaching): the full cycle is paid upfront. The subscription activates on payment, and the renewal reminder goes out N days before expiry. If unpaid, there is a grace period, then the subscription pauses or expires automatically.
- The ledger works the same way for both modes. A prepaid top-up is a credit and each consumption is a debit. Postpaid adds a bill debit and a payment credit. **The balance is always one number:** positive means the customer has advance with the business, negative means the customer owes money.
- GST rules: prepaid top-ups get an advance receipt voucher, and the tax invoice is raised on consumption or periodically. A CA will confirm this in Phase 0.
