---
name: classifying-tax-transactions
description: Content skill for classifying business bank transactions into US federal Schedule C (Form 1040) line items for sole proprietors and single-member LLCs disregarded for federal tax. Tax year 2025. Federal only. Supplies the Tier 1 deterministic vendor pattern library, Tier 2 conservative-default table, and refusal catalog. MUST be loaded alongside the tax-workflow-base skill which provides the three-state contract, citation discipline, structured-question form, and reviewer-attention output spec. This skill alone supplies rules but no workflow; the base alone supplies workflow but no rules.
---

# Schedule C Transaction Classifier

This skill is the **content layer** for US Schedule C transaction classification. It supplies the rules: the deterministic vendor table, the conservative-default table for ambiguous cases, and the refusal catalog for out-of-scope situations. **It must be loaded alongside `tax-workflow-base`**, which supplies the three-state contract (clean / default-with-flag / refuse), the citation discipline, the structured-question form, and the reviewer-attention output specification.

If the base is not loaded, refuse to proceed and tell the user: "This skill provides Schedule C rules but not the workflow. Please load `tax-workflow-base` alongside it, then ask your question again."

## Scope

| Field | Value |
|---|---|
| Jurisdiction | United States, federal only |
| Form | Schedule C (Form 1040), Profit or Loss From Business |
| Taxpayer type | Sole proprietor or single-member LLC disregarded for federal tax |
| Tax year | 2025 |
| Currency | USD only |
| Currency date | April 2026 |

State income tax, multi-state apportionment, Schedule SE, QBI, retirement contributions, and quarterly estimated tax are out of scope for this skill — they are the responsibility of separate content skills not loaded here.

## Tier 1 — Deterministic vendor patterns

Match by case-insensitive substring on the counterparty as it appears on the bank statement. If multiple match, use the most specific. If none match, fall through to Tier 2.

| Pattern | Schedule C line | Treatment |
|---|---|---|
| AWS, GOOGLE WORKSPACE, MICROSOFT 365, ADOBE, SLACK, NOTION, GITHUB, FIGMA, ZOOM, DROPBOX | Line 27a | Software subscriptions |
| QUICKBOOKS, INTUIT *QB, XERO, FRESHBOOKS | Line 27a | Accounting software |
| MAILCHIMP, CONVERTKIT, HUBSPOT | Line 8 | Advertising / marketing |
| WEWORK, REGUS, INDUSTRIOUS | Line 20b | Rent — other business property |
| VERIZON, AT&T, T-MOBILE, COMCAST, XFINITY | Line 25 | Utilities (business % only — see Tier 2) |
| HARTFORD, HISCOX, NEXT INSURANCE | Line 15 | Business liability insurance |
| FIVERR, UPWORK, TOPTAL | Line 11 | Contract labor (flag for 1099-NEC if ≥$600 cumulative) |
| UNITED, DELTA, AMERICAN, SOUTHWEST, JETBLUE | Line 24a | Travel — airfare |
| MARRIOTT, HILTON, HYATT | Line 24a | Travel — lodging |
| HERTZ, ENTERPRISE, AVIS | Line 24a | Travel — rental car |
| CPA, ATTORNEY, LEGALZOOM | Line 17 | Legal and professional |
| BUSINESS LICENSE, SECRETARY OF STATE | Line 23 | Taxes and licenses |
| CHASE, WELLS FARGO, BANK OF AMERICA, MERCURY | Line 27a | Bank fees |
| STRIPE TRANSFER, PAYPAL TRANSFER, SQUARE | EXCLUDE | Payout is not revenue — see "Payment processor trap" below |
| NETFLIX, HULU, SPOTIFY, APPLE MUSIC | EXCLUDE | Personal — not deductible |
| GYM, EQUINOX, PLANET FITNESS | EXCLUDE | Personal — not deductible |
| GROCERY, WHOLE FOODS, TRADER JOE | EXCLUDE | Personal |
| HEALTH INSURANCE, BLUE CROSS, AETNA, KAISER | EXCLUDE from Schedule C | Self-employed health insurance lives on Schedule 1 line 17, not Schedule C |
| IRS, US TREASURY, EFTPS, FRANCHISE TAX BOARD | EXCLUDE | Personal tax obligation, not Schedule C |
| MORTGAGE, RENT (personal home) | EXCLUDE | Home office is handled separately via Form 8829 |
| AMAZON (no item description) | Tier 2 — receipt review required | Default: personal (exclude) |
| Restaurants, STARBUCKS, DOORDASH | Tier 2 — substantiation required | Default: not deductible without §274(d) substantiation |
| SHELL, CHEVRON, EXXON, MOBIL (fuel) | Tier 2 — vehicle method required | Default: 0% business use, not deductible |

**Payment processor trap.** Stripe / PayPal / Square deposits on the bank statement are **net** of fees, not gross revenue. Gross revenue (Line 1) and processor fees (Line 27a) must be reconciled from the processor dashboard, not the bank statement. Always note this in the reviewer brief when processor payouts appear.

## Tier 2 — Conservative defaults for ambiguity

When data is missing, apply the default. Per the workflow base's three-state contract, every Tier 2 application is State B and must produce a flag, a citation, and a question.

| Ambiguity | Conservative default | Citation |
|---|---|---|
| Unknown business-use % for vehicle | 0% (no Line 9 deduction) | IRC §274(d); §280F |
| Unknown business-use % for home office | 0% (no Line 30 / Form 8829) | IRC §280A(c) |
| Unknown business-use % for phone / internet | 0% (no Line 25 deduction) | IRC §262; Treas. Reg. §1.262-1 |
| Unknown whether expense is business or personal | Personal (exclude) | IRC §162(a) (ordinary and necessary) |
| Meal without documented business purpose | Not deductible | IRC §274(d) (substantiation) |
| Amazon purchase with no item description | Personal (exclude) | IRC §162(a); §6001 (recordkeeping) |
| Cash withdrawal | Owner draw (exclude) | IRC §162(a); §6001 |
| Unknown whether worker is contractor or employee | Contractor (Line 11) with classification flag | Common-law test; §530 safe harbor |
| Capital asset acquired near OBBBA cutoff (Jan 19, 2025) | Pre-cutoff (40% bonus, not 100%) | OBBBA P.L. 119-21; IRC §168(k) |
| Unknown whether prior-year §179 election was made | Not made | IRC §179(b)(4); reviewer must verify from prior return |

## Refusal catalog

If any trigger fires, stop, output the verbatim message, recommend a credentialed professional, end the engagement.

| Code | Trigger | Refusal message (verbatim) |
|---|---|---|
| R-PARTNERSHIP | User mentions partners, partnership agreement, Form 1065, or K-1 | "This skill covers sole proprietors and single-member LLCs only. Partnerships file Form 1065. Please consult a CPA or EA experienced in partnership taxation." |
| R-S-CORP | User mentions S-corp election, Form 2553, Form 1120-S, or owner W-2 wages | "S-corporations file Form 1120-S, not Schedule C. This skill does not cover S-corp returns. Please consult a CPA experienced in S-corp taxation." |
| R-RENTAL | User mentions rental income, landlord activity, Schedule E, or Form 8825 | "Rental real estate income is reported on Schedule E, not Schedule C. Please consult a CPA or EA experienced in rental property taxation." |
| R-CRYPTO | User mentions crypto trading, DeFi, NFTs, mining, staking, or transfers to/from a crypto exchange | "Cryptocurrency transactions involve basis tracking, wash-sale considerations, and Form 8949 reporting. Out of scope. Please consult a CPA or EA experienced in digital assets." |
| R-FOREIGN | User mentions foreign accounts, foreign income, FBAR, FATCA, Form 8938, or Form 2555 | "Foreign income and FBAR/FATCA reporting are out of scope. Please consult a CPA or EA experienced in international tax." |
| R-MULTISTATE | Business activity in more than one US state | "Multi-state apportionment is out of scope. Please consult a CPA or EA experienced in multi-state taxation." |
| R-FARM | User mentions farming, Schedule F, crop or livestock income | "Farm income is reported on Schedule F. Out of scope. Please consult an agricultural tax specialist." |
| R-AUDIT | User mentions an open IRS notice, audit, or unfiled prior-year return | "Open IRS matters require personalised representation. Please consult a CPA, EA, or tax attorney directly." |

## Schedule C output lines targeted

This skill classifies into the following Schedule C Part II lines: 8 (Advertising), 9 (Car and truck), 11 (Contract labor), 13 (Depreciation), 15 (Insurance), 17 (Legal and professional), 18 (Office expense), 20a/20b (Rent), 21 (Repairs), 22 (Supplies), 23 (Taxes and licenses), 24a (Travel), 24b (Meals at 50%), 25 (Utilities), 26 (Wages), 27a (Other expenses — includes software, bank fees, merchant processing). Line 1 (Gross receipts) and Line 30 (Home office, via Form 8829) are noted but their computation is out of scope for this skill.

## Limitations

This skill is a classification aid for review by a human professional credentialed under Treasury Department Circular 230 (Enrolled Agent, CPA, or attorney). It does not file returns. It does not compute Schedule C totals, Schedule SE, the QBI deduction, retirement contributions, self-employed health insurance, or quarterly estimated tax. Tax law referenced is current as of April 2026.

## Disclaimer of liability

This skill is provided "AS IS", without warranty of any kind, express or implied, including but not limited to the warranties of merchantability, fitness for a particular purpose, accuracy, completeness, currency, or non-infringement. The skill does not constitute tax, legal, accounting, financial, or any other form of professional advice and does not establish any professional relationship between any party.

The authors, contributors, distributors, and any party referenced by this skill assume **no liability whatsoever** for any direct, indirect, incidental, consequential, special, exemplary, or punitive damages arising from the use of, or inability to use, this skill or any output it produces — including but not limited to: incorrect classifications, missed deductions, incorrect tax positions, IRS penalties, interest, audit costs, professional fees, or any other loss.

The user assumes **all risk** associated with using this skill and any output it produces. Every output must be independently reviewed and signed off by a qualified human professional credentialed under Treasury Department Circular 230 (Enrolled Agent, CPA, or attorney) before any reliance, filing, or communication with the Internal Revenue Service or any other taxing authority. The reviewing professional, not this skill, is responsible for the final tax positions and the accuracy of any return filed. Use of this skill constitutes acceptance of these terms.
