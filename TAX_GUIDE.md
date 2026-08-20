# Imaginarium Tax Guide

This document explains Imaginarium's HMRC tax compliance strategy tier by tier.
All strategies described here use only legitimate HMRC-approved reliefs.
No aggressive or artificial tax avoidance schemes are used.

---

## Tax Year

The UK tax year runs from **6 April to 5 April** the following year.
Set `IMAGINARIUM_TAX_YEAR_START` in `.env` to match the current tax year start (e.g. `2024-04-06`).

---

## Phase 1 — £0 to £1,000 (Trading Allowance)

**HMRC Rule:** Sole traders can earn up to **£1,000 gross revenue** per tax year completely tax-free under the Trading Allowance.

- No Self Assessment registration required
- No filing required
- No tax due
- K-2SO tracks gross revenue against the threshold in real time

**Monitor:** `GET /tax-status` shows remaining allowance and whether the threshold has been crossed.

---

## Phase 2 — £1,001 to £12,570 (Self Assessment + Personal Allowance)

**Triggered when:** Gross revenue exceeds £1,000 in a tax year.

**HMRC obligations:**
- Register for Self Assessment by **5 October** after the tax year ends
- File Self Assessment return by **31 January** the following year
- Pay any tax due by **31 January**

**Tax calculation:**
1. Gross revenue
2. Less: Trading allowance (£1,000) OR itemised actual expenses (whichever is higher)
3. = Taxable profit
4. Less: Personal allowance (£12,570)
5. = Taxable income

At this phase, taxable income is usually **£0** so no income tax is due.
The Self Assessment return must still be filed to declare income.

**K-2SO action:** `/tax-compliance/forecast` generates the forecast, deadlines, and estimated liability.

---

## Phase 3 — £12,570 to £50,270 (Basic Rate Income Tax)

**Tax charges:**
- **Income tax:** 20% on profit above personal allowance (£12,570)
- **Class 2 NI:** £163.80/year flat rate
- **Class 4 NI:** 8% on profit between £12,570 and £50,270

**Efficiency strategies (all HMRC-compliant):**

| Strategy | Relief | How to use |
|---|---|---|
| **Allowable expenses** | Reduces taxable profit £ for £ | Log via `/tax-compliance/log-expense` |
| **Home office** | 10% of rent/mortgage interest | Log as `home_office` category |
| **Pension contributions** | 100% deductible, reduces taxable profit | `/tax-compliance/efficiency` shows saving |
| **Equipment (AIA)** | 100% deductible in purchase year (up to £1,000,000) | Log as `equipment` category |
| **Software/subscriptions** | Fully deductible if for business | Log as `software` category |
| **Marketing spend** | Fully deductible | Log as `marketing` category |
| **Professional development** | Courses, books, training — fully deductible | Log as `professional_dev` category |

**Monitor:** `GET /tax-compliance/efficiency` gives tailored recommendations.

---

## Phase 4 — £50,270+ (Higher Rate Tax — Incorporation Analysis)

At this level, consider whether a **Limited Company** is more tax-efficient than remaining a sole trader.

**Comparison (approximate, seek professional advice):**

| Structure | Tax on £60,000 profit |
|---|---|
| Sole trader | ~20% income tax + Class 2 + Class 4 NI |
| Limited company | 19% Corporation Tax, then salary + dividends |

**Dividend allowance:** £500/year tax-free (2024/25).

**K-2SO action:** `GET /tax-compliance/efficiency` includes incorporation analysis when profit exceeds £50,270.

> Seek professional advice from a qualified accountant before incorporating.

---

## VAT

**Mandatory threshold:** Register for VAT if turnover exceeds **£90,000** in any rolling 12-month period.

**VAT Flat Rate Scheme (FRS):**
- Available to businesses with turnover below £150,000
- Pay a fixed percentage (16.5% for most digital/service businesses) of gross turnover to HMRC
- Simplifies accounting — no need to track input VAT
- Can be beneficial if your actual VAT input (purchases) is low

**Monitor:** `GET /tax-compliance/vat-forecast` shows progress to threshold and FRS eligibility.

**EU customers (MOSS):** If selling digital services to EU consumers, consider the One Stop Shop (OSS) scheme to handle EU VAT across all member states from a single registration.

---

## Expense Categories

K-2SO approves expenses in these HMRC-allowable categories:

| Category | Examples |
|---|---|
| `home_office` | 10% of rent, mortgage interest, utilities |
| `software` | Canva, Adobe, subscriptions, SaaS tools |
| `hosting` | Web server, cloud storage, CDN |
| `domain` | Domain name registrations and renewals |
| `marketing` | Paid ads, promotional materials |
| `professional_dev` | Courses, books, training, conferences |
| `equipment` | Laptops, cameras, peripherals (AIA applies) |

All expenses require:
1. A receipt reference or document identifier
2. A business justification
3. K-2SO approval

Expenses are logged via `POST /tax-compliance/log-expense`.

---

## Audit Trail

Every tax calculation, expense approval, and filing decision is logged with:
- Timestamp
- Agent responsible (K-2SO)
- Action type
- Full payload

Access via `GET /tax-compliance/audit-trail`. Exportable for accountant review or HMRC audit.

---

## API Reference — Tax Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/tax-status` | GET | Current tax position, phase, alerts |
| `/tax-compliance/forecast` | GET | Self Assessment forecast and deadlines |
| `/tax-compliance/expenses` | GET | Approved expenses by category |
| `/tax-compliance/log-expense` | POST | K-2SO expense logging |
| `/tax-compliance/efficiency` | GET | Tax efficiency recommendations |
| `/tax-compliance/vat-forecast` | GET | VAT threshold progress |
| `/tax-compliance/audit-trail` | GET | Complete tax audit trail |

---

## Compliance Principles

1. **No aggressive avoidance** — only HMRC-approved reliefs are used
2. **GLaDOS compliance check** — all tax strategies must be lawful and non-deceptive
3. **K-2SO authorization** — all expense claims require K-2SO approval with justification
4. **Transparency** — complete audit trail accessible at all times
5. **Core Laws override** — tax efficiency never overrides ethical or legal obligations
