# Profit Radar production cost envelope

Checked 2026-10-09. These are **planning assumptions, not invoices or approved prices**. Product price is the existing ¥19,800/month **tax-inclusive** contract; no trial customer is charged automatically. Google assessment, legal, backup, monitoring and actual resource use have no verified quote yet. The owner must approve a monthly ceiling before upgrading Railway or inviting customers.

| Component | Planning basis | Fixed vs variable |
|---|---|---|
| Railway | [Railway plans](https://docs.railway.com/pricing/plans): Pro base $20/month with $20 usage included; total is approximately `max($20, metered usage)` for a single subscribed account, before any extras. Current workspace plan/actual three-service resource usage is not verified. | Fixed minimum + metered compute/memory/egress/build |
| Supabase | [Supabase pricing](https://supabase.com/pricing): Pro starts at $25/month for the first project with Micro compute credit, 7-day daily backups; overages, larger compute and longer/PITR retention extra. Current Production plan must be checked in its billing page. | Fixed minimum + usage |
| Stripe | [Japan standard pricing](https://stripe.com/jp/pricing): 3.6% per successful domestic card payment. Other methods, cross-border/FX, Billing/Tax products, dispute/refund charges may add cost. | Per successful payment |
| AI | Code enforces company token/USD limits via `AI_COMPANY_MONTHLY_TOKENS`, `AI_COMPANY_MONTHLY_USD`, model-rate table and reservation RPC. Actual model mix, usage and owner-approved limit are unknown. | At most approved budget `B` USD/company/month, plus any non-AI provider fees |
| Gmail/Google | API quotas do not prove a zero operating cost. Restricted-scope verification and possible annual independent security assessment require a Google-approved assessor quote; [Google requirements](https://developers.google.com/identity/protocols/oauth2/production-readiness/restricted-scope-verification). | Unknown one-off/annual assessment and operations |
| Backup, monitoring, domain, support, legal | Encrypted off-host storage, alert receiver, domain renewal, on-call and counsel quote not yet selected. | Unknown fixed/usage |

Let `R` be the actual JPY/USD exchange rate, `U` Railway metered USD/month, `S` Supabase total USD/month (minimum assumption $25), `B` approved AI USD/company/month, and `X` all other USD costs. The **upper-bound planning formula** for `N` paying companies using domestic cards is:

`gross receipts = 19,800 × N JPY`; `Stripe base fee ≈ 712.8 × N JPY`; `operating cost ≈ R × (max(20,U) + S + B×N + X) + Stripe fee + JPY-only costs`.

| Paying companies | Gross receipts (tax-inclusive) | Base Stripe 3.6% | Illustrative AI ceiling at B=$1 | Illustrative known-cost subtotal* |
|---:|---:|---:|---:|---:|
| 3 | ¥59,400 | ¥2,138 | ¥450 | ¥9,338 |
| 10 | ¥198,000 | ¥7,128 | ¥1,500 | ¥15,378 |
| 50 | ¥990,000 | ¥35,640 | ¥7,500 | ¥49,890 |

*Illustration only: `R=¥150/$`, Railway usage ≤$20, Supabase exactly $25, AI B=$1/company, no X or JPY-only costs. These are **not measured** and exclude Google assessment, counsel, tax processing, backup, monitoring and support labor. Stripe fees are rounded to whole yen at portfolio level; actual per-transaction rounding may differ. Do not present the remainder as profit or AI-attributed recovery. Ask the accountant to confirm consumption-tax/invoice treatment.

Before paid sale: record real Railway/Supabase plan and cost cap, AI model rates and company budget, monthly usage estimate from a three-tenant test, Stripe LIVE pricing/product fees, assessor/legal/backup/monitoring quotes and the desired margin floor. Recalculate with the actual exchange rate on approval day.
