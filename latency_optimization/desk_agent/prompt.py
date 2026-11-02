"""System prompt and reference tables. The manual is the one in _gen, with Section 10 (the three tasks) added and two parts moved behind tools: the Section 7 template texts and the Appendix A catalogue."""

import re

from ._gen import mod_quote as _B

_manual = _B.SYSTEM.split("<manual>")[1].split("</manual>")[0].strip()

# Section 7: keep the headings as an index, move each template's text behind get_template
TEMPLATES = {
    m.group(2): m.group(3)
    for m in re.finditer(r'(### 7\.\d [^\n]+\(Template ([A-Z0-9-]+)\))\n> "([^\n]+)"\n', _manual)
}
assert len(TEMPLATES) == 7, sorted(TEMPLATES)
_manual = re.sub(
    r'(### 7\.\d [^\n]+\(Template ([A-Z0-9-]+)\))\n> "[^\n]+"\n',
    lambda m: f'{m.group(1)}\nApproved text: get_template("{m.group(2)}").\n',
    _manual,
)

# Appendix A: move the catalogue behind lookup_parts
_a = _manual.index("| Cat. no. | Part")
_b = _manual.index("\n\n---\n\n*End of Manual")
_rows = _manual[_a:_b].strip().split("\n")
PARTS_HEAD = _rows[0]
PARTS = {r.split("|")[1].strip(): r for r in _rows[2:]}
assert len(PARTS) > 60 and all(k.isdigit() for k in PARTS)
_manual = (
    _manual[:_a]
    + "The catalogue is behind lookup_parts(cat_nos), which returns one row per catalogue number with these columns: "
    + ", ".join(c.strip() for c in PARTS_HEAD.strip("|").split("|"))
    + "."
    + _manual[_b:]
)

ROLE = """You are the desk assistant for Acme Insurance auto claims. An adjuster is on a live call with a customer and gives you one task about one claim. Look up what you need with the tools, follow the manual below, and finish by calling the task's recorder tool once. Only the recorder call reaches the adjuster.
"""
SECTION_10 = """## Section 10: Desk Assistant Tasks

For Section 9, the claim file is everything get_claim, get_estimate and search_ledger return for the claim. Appendix A is behind lookup_parts.

### 10.1 Settlement quote
Apply the Desk Settlement Procedure (Section 9) to the claim file. Record the result with submit_quote: the verdict (APPROVE, SUPERVISOR, FRAUD or DENY) and the amount in dollars and cents (0 for FRAUD and DENY).

### 10.2 SIU pre-screen
Before a claim can go to the Special Investigations Unit, the referral has to cite every prior claim that counts under two lines of the 5.1 rubric, as 9.9 defines them. Record with submit_prescreen:
- ph_claim_ids: the claim ID of every ledger row that counts toward prior claim frequency for this claim's policyholder (9.9). All claim types count.
- shop_flagged_claim_ids: the claim ID of every ledger row that counts toward the repair shop indicator for this claim's repair shop (9.9). Any policyholder, all claim types.
- siu_points: 2 if ph_claim_ids has 3 or more entries, plus 3 if shop_flagged_claim_ids has 3 or more entries (0 if neither).
Use an empty list where nothing counts. Order does not matter. The ledger can include claims dated after the one you are asked about.

### 10.3 Customer letter
The claim is decided and get_claim returns the decision record. Pick the approved Section 7 template, fill every bracket you can from the record, and keep the approved wording unchanged. Where a bracket asks for quoted policy language or a state-specific paragraph, leave that bracket as it is; the adjuster completes those before the letter goes out. Use DEN-PART-01 when a claim is paid but part of it was excluded. Record the draft with submit_letter: the template ID, the letter, and the 8.2 "Pay After Acceptance" entry for the loss state exactly as the matrix shows it ("none" for a full denial).
"""
NO_COMMENTARY = "Write no text outside your tool calls: no plans, notes, summaries or explanations. Nobody reads that text, and the customer waits while you write it. Fill in the recorder call's arguments exactly as the manual asks."
_end = "\n\n---\n\n*End of Manual"
_i = _manual.index(_end)
MANUAL = _manual[:_i] + "\n\n" + SECTION_10.strip() + _manual[_i:]


def system_prompt(*, no_commentary=False):
    """The same text for every item and setting, apart from one optional paragraph at the end: the no-commentary instruction."""
    return (
        ROLE
        + "\n<manual>\n"
        + MANUAL
        + "\n</manual>"
        + ("\n\n" + NO_COMMENTARY if no_commentary else "")
    )
