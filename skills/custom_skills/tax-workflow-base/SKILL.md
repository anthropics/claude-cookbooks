---
name: tax-workflow-base
description: Workflow-only base skill for regulated-domain classification. Defines the three-state contract (clean / conservative-default-with-flag / refuse), the conservative-defaults principle, the citation discipline, the structured-question form, and the reviewer-attention output contract. Contains no tax content, no rates, no thresholds, no jurisdiction-specific rules. MUST be loaded alongside at least one content skill (e.g., classifying-tax-transactions) that supplies the actual rules and the current year's figures. Loading this skill alone is a configuration error and Claude must refuse to proceed.
---

# Tax Workflow Base

This skill is the workflow architecture for any tax classification or computation task. It defines **how** to do the work — the order of operations, how to handle ambiguity, what to produce as output, what to refuse — without specifying **what** rules to apply. The rules come from a companion content skill.

**This skill must always be loaded with at least one content skill.** Loading this skill alone is a configuration error and the model must refuse to proceed.

## The slot contract

A content skill that conforms to this base supplies:

1. A **scope statement** — the jurisdiction, the form(s), the taxpayer type, the tax year, the currency.
2. A **Tier 1 deterministic table** — counterparty patterns mapped directly to a treatment, no reasoning required.
3. A **Tier 2 conservative-defaults table** — for each ambiguity type, the default that costs the taxpayer more tax, with the source citation for the rule that creates the ambiguity.
4. A **refusal catalog** — out-of-scope situations, each with a trigger and a verbatim refusal message.
5. **Output line definitions** — the form lines or codes the content skill targets (e.g., Schedule C Line 27a, ICD-10 J45.x).

This base provides the surrounding workflow, the three-state contract, the citation discipline, and the reviewer-attention output spec.

## The three-state contract

Every input the model touches resolves to **exactly one** of three states. There is no fourth state. Silent assertion, hand-wave, or "best guess" is a contract violation.

### State A — Cleanly resolved

The input matches a Tier 1 deterministic pattern, or the content skill's rules apply unambiguously and a careful reviewer reading the same sources would reach the same conclusion. Apply the treatment. Cite the primary source. Do not flag for reviewer attention unless dollar magnitude alone warrants it (the content skill defines that threshold).

### State B — Resolved with a conservative default

A rule applies but a fact is missing (a percentage, a basis, a substantiation document, a date), OR the public sources themselves are interpretive on this case. The model **must do all four** of the following, in order, with no exceptions:

1. **State the ambiguity** in one sentence in the reviewer brief.
2. **Apply the conservative default** from the content skill — the option that costs the taxpayer more tax, never less.
3. **Cite the primary source** for the rule that creates the ambiguity, so the reviewer can verify it.
4. **Add the question** to the structured question form so the user can resolve it on a single round trip.

The four actions are linked. Silently applying a default is a contract violation. Asking without applying a default is a contract violation. Stating a position without showing the rule it rests on is a contract violation.

### State C — Out of scope, refused

The situation triggers a refusal in the content skill's refusal catalog. **Stop.** Output the refusal message verbatim. Recommend the user consult a credentialed professional outside the platform. Do not partially handle a refused situation. Do not classify the in-scope half. The refusal is total.

## The conservative-defaults principle

When uncertain about a position, choose the treatment that costs the taxpayer more tax. The reviewer can correct an over-conservative position after the fact. The reviewer cannot easily recover from an aggressive position surfacing in audit three years later when the statute of limitations is still open.

The principle applies across all jurisdictions and all tax types:

- Unknown business-use percentage of an asset → 0% business use, no deduction
- Unknown deductibility of an expense → not deductible
- Missing contemporaneous documentation for a substantiation-required item → not deductible
- Unknown whether income is reportable → reportable
- Unknown character of income → ordinary
- Unknown holding period → short-term
- Unknown basis of an asset → zero basis
- Unknown whether an activity is a business or hobby → hobby
- Unknown whether a prior-year election was made → not made
- Unknown filing status → the highest-tax option in most cases

The content skill specifies the concrete defaults for each ambiguity type. This base specifies the principle and the rule that the content skill's defaults must follow it.

## Citation discipline

No position is valid without a primary-source citation. A primary source is one of: a statutory section (IRC §, ITA s, equivalent in other jurisdictions), a regulation, an official publication issued by the tax authority, a revenue ruling or revenue procedure, or current form instructions from the tax authority itself.

Secondary sources (commentary, blog posts, advisor memos, training materials) are not acceptable as the citation for a position. They may be referenced as supporting context only.

If the content skill cannot supply a primary-source citation for a position, the position cannot be taken. Default to State B (conservative default) or State C (refuse) instead.

## The structured question form

Every conservative default applied (every State B classification) must produce a question for the user. Per the workflow, the user gets exactly one round trip to answer questions. The questions are presented at the end of the work, all together, grouped by category, ordered by dollar magnitude.

When the volume of questions exceeds 10, group by category rather than asking one per transaction. ("The 8 fuel transactions at Shell totalling $X — is the vehicle..." not eight separate questions.)

Each question must include:

1. **The question itself**, in plain language.
2. **The current default applied**, so the user knows what happens if they don't answer.
3. **The alternative that would apply** if they answer differently.
4. **The dollar (or equivalent) impact** of the swing between default and alternative.

A question without all four of these elements is incomplete and must be revised before delivery.

## The reviewer-attention output contract

The output of any task built on this base is structured for a human reviewer credentialed in the relevant jurisdiction (a tax professional under Circular 230 in the US, an ATT/CTA in the UK, an Avukat or perit in Malta, etc.). The reviewer is the immediate consumer of the output, not the taxpayer. The reviewer signs off on positions before they reach a return or the taxing authority.

Every output must contain:

1. **The bottom line** — the headline number(s) the reviewer needs to see first, in the units the form expects.
2. **High-flag list** — items that required judgment AND have high dollar magnitude, ordered by dollar effect descending. The reviewer reads top-down and stops when confident.
3. **Computation trail** — for every position taken: what was concluded, what source data was used, what rule was applied (with citation), what dollar effect resulted.
4. **Conservative defaults applied** — a complete list of every State B position, in dollar order, with the ambiguity, the default, the cash impact of the swing, and the citation.
5. **Refusal trace** — for each refusal code in the content skill's catalog, one line stating "cleared" or "fired" with reason. This makes refusal handling auditable rather than asserted.
6. **Scope limitations** — explicit statement of what the work product covers and what it does not.

## The composition contract

When this base is loaded **alongside** a content skill, the two skills compose: this base provides the workflow scaffolding, the content skill provides the substantive rules. Both must be present for any task to proceed.

When this base is loaded **alone** with no content skill, the base must refuse to operate. The refusal message:

> "I am the workflow base for tax classification tasks. I do not contain any tax rules, rates, or jurisdiction-specific content myself — those come from a companion content skill. Please load a content skill (e.g., `classifying-tax-transactions` for US Schedule C) alongside me, then ask your question again."

This is the slot contract enforced at runtime.

## What this base is not

- Not tax advice. The output is a classification or computation aid for review by a credentialed professional.
- Not a return preparer. It does not file returns.
- Not jurisdiction-specific. Every jurisdiction-specific rule comes from the content skill.
- Not a substitute for the content skill. The base is empty without it.

## Disclaimer of liability

This skill is provided "AS IS", without warranty of any kind, express or implied, including but not limited to the warranties of merchantability, fitness for a particular purpose, accuracy, completeness, currency, or non-infringement. The skill does not constitute tax, legal, accounting, financial, or any other form of professional advice and does not establish any professional relationship between any party.

The authors, contributors, distributors, and any party referenced by this skill assume **no liability whatsoever** for any direct, indirect, incidental, consequential, special, exemplary, or punitive damages arising from the use of, or inability to use, this skill or any output it produces — including but not limited to: incorrect classifications, missed deductions, incorrect tax positions, penalties, interest, audit costs, professional fees, or any other loss.

The user assumes **all risk** associated with using this skill and any output it produces. Every output must be independently reviewed and signed off by a qualified human professional credentialed under the applicable jurisdiction's regulatory regime (e.g., Treasury Department Circular 230 for the United States — Enrolled Agent, CPA, or attorney) before any reliance, filing, or communication with a taxing authority. The reviewing professional, not this skill, is responsible for the final positions and the accuracy of any return or filing. Use of this skill constitutes acceptance of these terms.
