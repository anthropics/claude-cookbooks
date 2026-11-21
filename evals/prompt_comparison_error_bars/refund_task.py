"""A synthetic refund desk whose correct answers are known by construction.

Each case is a set of order facts. `ruling` is the refund policy written as code and gives
the label; `render_ticket` turns the same facts into the text the model reads. Nothing is
labelled by hand, so a wrong answer is always the model's and never the dataset's.

`PROMPTS` holds three system prompts for the same policy: a draft that leaves one sentence
out, the complete prose, and a rewrite as an ordered procedure. Comparing them is the
running example of the cookbook.
"""

import json
import random
from dataclasses import asdict, dataclass
from datetime import date, timedelta
from pathlib import Path

DECISIONS = ("approve", "deny", "escalate")
DATASET_SIZE = 600
SELLER_FAULT = ("wrong_item", "damaged_in_transit", "defective")

CHANGE_OF_MIND_DAYS = 30
PLUS_CHANGE_OF_MIND_DAYS = 45
SELLER_FAULT_DAYS = 60
DAMAGE_REPORT_DAYS = 14
GROCERY_REPORT_DAYS = 7
WARRANTY_DAYS = 365
SIGN_OFF_ABOVE_USD = 400
REPEAT_REFUND_LIMIT = 3
REPEAT_REFUND_DAYS = 90

DECISION_SCHEMA = {
    "type": "object",
    "properties": {"decision": {"type": "string", "enum": list(DECISIONS)}},
    "required": ["decision"],
    "additionalProperties": False,
}


@dataclass(frozen=True)
class Case:
    case_id: str
    order_on_file: bool
    category: str  # apparel | electronics | grocery | gift_card
    item: str
    quantity: int
    unit_price_usd: int
    final_sale: bool
    delivered_on: date
    requested_on: date
    reason: str  # changed_mind, or one of SELLER_FAULT
    opened: bool
    plus_since: date | None
    previous_refunds: tuple[date, ...]
    message: str  # the customer's own words: colour only, never needed for the decision

    @property
    def days_since_delivery(self) -> int:
        return (self.requested_on - self.delivered_on).days

    @property
    def order_line_usd(self) -> int:
        return self.quantity * self.unit_price_usd

    @property
    def recent_refunds(self) -> int:
        return sum(
            (self.requested_on - refund).days <= REPEAT_REFUND_DAYS
            for refund in self.previous_refunds
        )

    @property
    def plus_on_delivery(self) -> bool:
        return self.plus_since is not None and self.plus_since <= self.delivered_on


def ruling(case: Case) -> tuple[str, str]:
    """The policy as code: the correct decision and the name of the rule that produced it."""
    if not case.order_on_file:
        return "escalate", "no_order_on_file"
    if case.recent_refunds >= REPEAT_REFUND_LIMIT:
        return "escalate", "repeat_refunds"
    if case.category == "gift_card":
        return "deny", "gift_card"

    days = case.days_since_delivery
    if case.reason in SELLER_FAULT:
        if case.category == "grocery":
            limit, too_late = GROCERY_REPORT_DAYS, "grocery_reported_late"
        elif case.reason == "damaged_in_transit":
            limit, too_late = DAMAGE_REPORT_DAYS, "damage_reported_late"
        else:
            limit, too_late = SELLER_FAULT_DAYS, "seller_fault_too_late"
        if days > limit:
            defective_electronics = case.reason == "defective" and case.category == "electronics"
            if defective_electronics and days <= WARRANTY_DAYS:
                return "escalate", "warranty"
            return "deny", too_late
    else:
        if case.final_sale or case.category == "grocery":
            return "deny", "not_returnable"
        if case.category == "electronics" and case.opened:
            return "deny", "opened_electronics"
        window = PLUS_CHANGE_OF_MIND_DAYS if case.plus_on_delivery else CHANGE_OF_MIND_DAYS
        if days > window:
            return "deny", "outside_window"

    if case.order_line_usd > SIGN_OFF_ABOVE_USD:
        return "escalate", "needs_sign_off"
    return "approve", "eligible"


def decide(case: Case) -> str:
    return ruling(case)[0]


def _long_date(day: date) -> str:
    return f"{day.day} {day:%B %Y}"


def _yes_no(flag: bool) -> str:
    return "yes" if flag else "no"


def render_ticket(case: Case) -> str:
    """The user turn: the order record, then the request. Every fact the policy needs is here."""
    on_file = "yes" if case.order_on_file else "no (the details below are the customer's account)"
    plus = f"since {_long_date(case.plus_since)}" if case.plus_since else "no"
    refunds = ", ".join(_long_date(refund) for refund in case.previous_refunds) or "none"
    return "\n".join(
        [
            "ORDER RECORD",
            f"Order on file: {on_file}",
            f"Item: {case.item} ({case.category.replace('_', ' ')})",
            f"Quantity: {case.quantity}",
            f"Unit price: ${case.unit_price_usd}",
            f"Final sale: {_yes_no(case.final_sale)}",
            f"Delivered: {_long_date(case.delivered_on)}",
            f"Package opened: {_yes_no(case.opened)}",
            f"Plus member: {plus}",
            f"Previous refunds: {refunds}",
            "",
            "REFUND REQUEST",
            f"Received: {_long_date(case.requested_on)}",
            f"Reason: {case.reason.replace('_', ' ')}",
            f'Customer message: "{case.message}"',
        ]
    )


_HOW_TO_ANSWER = f"""Decide from the order record. The customer's message is background only.
Count calendar days from the delivery date to the date the request was received. Every limit \
in this policy includes its last day: a request received exactly {CHANGE_OF_MIND_DAYS} days \
after delivery is within {CHANGE_OF_MIND_DAYS} days, and a previous refund issued exactly \
{REPEAT_REFUND_DAYS} days before the request is within the last {REPEAT_REFUND_DAYS} days.
Answer with one decision: approve, deny, or escalate (hand the request to a specialist)."""

# The policy the way a policy team writes it. The reader has to work out the order in which
# the rules apply. `{default}` is where the sentence about requests that no rule allows goes.
_PROSE = f"""You handle refund requests for Northwind Outfitters.

Refund policy

We want refunds to be easy. Customers who change their mind can return most items within \
{CHANGE_OF_MIND_DAYS} days of delivery. Plus members get {PLUS_CHANGE_OF_MIND_DAYS} days, as \
long as they joined on or before the day the order was delivered. Opened electronics \
cannot be returned for a change of mind, and neither can groceries or anything bought as \
final sale. When we sent the wrong item, or the item arrived damaged or is defective, the \
customer is not at fault, so we accept those requests for {SELLER_FAULT_DAYS} days after \
delivery, final-sale items included. Two cases are tighter. Damage in transit has to be \
reported within {DAMAGE_REPORT_DAYS} days of delivery, because that is how long the carrier \
gives us to claim. Groceries are perishable, so any problem with a grocery item, damage in transit included, \
has to be reported within {GROCERY_REPORT_DAYS} days. Defective electronics that are past the \
{SELLER_FAULT_DAYS} days but within {WARRANTY_DAYS} days of delivery are covered by the \
manufacturer's warranty and not by us, so a specialist takes them. Gift cards are not \
refundable for any reason. A refund we would otherwise approve needs a specialist's sign-off \
when the order line (unit price times quantity) comes to more than ${SIGN_OFF_ABOVE_USD}. \
Before anything else, check that the order is on file: when it is not, a specialist handles \
the request. The same goes for a customer who has had {REPEAT_REFUND_LIMIT} or more refunds \
in the last {REPEAT_REFUND_DAYS} days, whatever the request is and even if we would deny \
it.{{default}}

{_HOW_TO_ANSWER}"""

# A human reader supplies this without being told. The draft prompt leaves it out.
DEFAULT_SENTENCE = (
    " A specialist is only for the situations named here: a request that this policy does not"
    " allow is denied."
)

# The same policy as an ordered procedure. Every branch ends in an explicit decision.
_PROCEDURE = f"""You handle refund requests for Northwind Outfitters.

Refund policy

Work through these checks in order and stop at the first one that gives a decision.

1. The order is not on file: escalate.
2. Count the previous refunds issued in the last {REPEAT_REFUND_DAYS} days. \
{REPEAT_REFUND_LIMIT} or more: escalate.
3. The item is a gift card: deny.
4. Count the days from delivery to the request.
5. The reason is wrong item, damaged in transit, or defective. The time limit is \
{GROCERY_REPORT_DAYS} days for a grocery item; otherwise {DAMAGE_REPORT_DAYS} days for damage \
in transit; otherwise {SELLER_FAULT_DAYS} days.
   - Within the limit: go to step 7.
   - Past the limit, the item is electronics, the reason is defective, and it is \
{WARRANTY_DAYS} days or fewer since delivery: escalate (manufacturer's warranty).
   - Otherwise: deny.
6. The reason is changed mind:
   - The item is final sale, a grocery item, or opened electronics: deny.
   - The window is {CHANGE_OF_MIND_DAYS} days, or {PLUS_CHANGE_OF_MIND_DAYS} days if the \
customer became a Plus member on or before the delivery date. Past the window: deny.
   - Otherwise: go to step 7.
7. Unit price times quantity is more than ${SIGN_OFF_ABOVE_USD}: escalate. Otherwise: approve.

{_HOW_TO_ANSWER}"""

PROMPTS = {
    "draft": _PROSE.format(default=""),
    "prose": _PROSE.format(default=DEFAULT_SENTENCE),
    "procedure": _PROCEDURE,
}

# ---------------------------------------------------------------------------------------
# Case generator. Day counts, order totals, membership dates and refund dates are drawn
# mostly from bands around the policy's thresholds, where a careless reader goes wrong.
# ---------------------------------------------------------------------------------------

_ITEMS = {
    "apparel": ["trail running jacket", "merino base layer", "hiking boots", "down vest"],
    "electronics": ["GPS watch", "headlamp", "action camera", "handheld radio"],
    "grocery": ["freeze-dried meal box", "energy bar case", "electrolyte mix"],
    "gift_card": ["gift card"],
}
_CATEGORY_WEIGHTS = {"apparel": 0.38, "electronics": 0.42, "grocery": 0.13, "gift_card": 0.07}
_REASON_WEIGHTS = {
    "changed_mind": 0.4,
    "defective": 0.3,
    "damaged_in_transit": 0.16,
    "wrong_item": 0.14,
}
_QUANTITY_WEIGHTS = {1: 0.55, 2: 0.25, 3: 0.12, 4: 0.08}
_REFUND_COUNT_WEIGHTS = {0: 0.34, 1: 0.2, 2: 0.2, 3: 0.16, 4: 0.1}
# Bands are (first value, last value, weight).
_DAYS_SINCE_DELIVERY = [
    (1, 5, 0.16),
    (6, 8, 0.1),
    (12, 16, 0.12),
    (17, 26, 0.1),
    (28, 32, 0.11),
    (43, 47, 0.09),
    (58, 62, 0.1),
    (63, 200, 0.14),
    (360, 370, 0.05),
    (371, 500, 0.03),
]
_ORDER_LINE_USD = [(15, 380, 0.55), (385, 415, 0.25), (420, 1200, 0.2)]
_GROCERY_UNIT_PRICE = (12, 120)
_GIFT_CARD_VALUES = [25, 50, 100, 200, 500]
_DAYS_SINCE_REFUND = [(5, 80, 0.55), (86, 94, 0.3), (95, 200, 0.15)]
_PLUS_JOINED_RELATIVE_TO_DELIVERY = [(-400, -10, 0.55), (-4, 4, 0.3), (5, 60, 0.15)]
# What the customer wrote. None of these states a fact the policy uses, so a message can
# never contradict the order record.
_MESSAGES = {
    "changed_mind": [
        "It just isn't what I expected. I've been a loyal customer for years.",
        "Found a better deal elsewhere. Please process this quickly.",
        "It doesn't suit me after all.",
        "I ordered it on impulse and would like my money back.",
    ],
    "defective": [
        "It doesn't work the way it should.",
        "There is a fault with it. Really disappointed.",
        "It is faulty. Please sort this out.",
    ],
    "damaged_in_transit": [
        "The box arrived crushed.",
        "The packaging was torn when the courier handed it over.",
    ],
    "wrong_item": [
        "This is not what I ordered.",
        "You sent the wrong one.",
    ],
}
_FIRST_DELIVERY = date(2026, 1, 5)


def _weighted(rng: random.Random, weights: dict):
    return rng.choices(list(weights), weights=list(weights.values()))[0]


def _from_bands(rng: random.Random, bands: list[tuple[int, int, float]]) -> int:
    low, high, _ = rng.choices(bands, weights=[weight for *_, weight in bands])[0]
    return rng.randint(low, high)


def _quantity_and_unit_price(rng: random.Random, category: str) -> tuple[int, int]:
    if category == "gift_card":
        return 1, rng.choice(_GIFT_CARD_VALUES)
    quantity = _weighted(rng, _QUANTITY_WEIGHTS)
    if category == "grocery":
        return quantity, rng.randint(*_GROCERY_UNIT_PRICE)
    return quantity, max(5, round(_from_bands(rng, _ORDER_LINE_USD) / quantity))


def generate_cases(n: int, seed: int = 0) -> list[Case]:
    """`n` cases, the same ones for the same seed."""
    rng = random.Random(seed)
    cases = []
    for index in range(n):
        category = _weighted(rng, _CATEGORY_WEIGHTS)
        is_gift_card = category == "gift_card"
        reason = "changed_mind" if is_gift_card else _weighted(rng, _REASON_WEIGHTS)
        quantity, unit_price = _quantity_and_unit_price(rng, category)
        delivered_on = _FIRST_DELIVERY + timedelta(days=rng.randint(0, 250))
        requested_on = delivered_on + timedelta(days=_from_bands(rng, _DAYS_SINCE_DELIVERY))
        refund_ages = {
            _from_bands(rng, _DAYS_SINCE_REFUND)
            for _ in range(_weighted(rng, _REFUND_COUNT_WEIGHTS))
        }
        joined_plus = rng.random() < 0.4
        joined_offset = _from_bands(rng, _PLUS_JOINED_RELATIVE_TO_DELIVERY)
        cases.append(
            Case(
                case_id=f"case-{index + 1:04d}",
                order_on_file=rng.random() < 0.95,
                category=category,
                item=rng.choice(_ITEMS[category]),
                quantity=quantity,
                unit_price_usd=unit_price,
                final_sale=not is_gift_card and category != "grocery" and rng.random() < 0.15,
                delivered_on=delivered_on,
                requested_on=requested_on,
                reason=reason,
                opened=rng.random() < 0.55,
                plus_since=delivered_on + timedelta(days=joined_offset) if joined_plus else None,
                previous_refunds=tuple(
                    requested_on - timedelta(days=age) for age in sorted(refund_ages, reverse=True)
                ),
                message=rng.choice(_MESSAGES[reason]),
            )
        )
    return cases


def save_cases(cases: list[Case], path: Path) -> None:
    """One JSON object per line: the case, plus the label and rule so the file reads on its own."""
    with path.open("w") as handle:
        for case in cases:
            expected, rule = ruling(case)
            row = asdict(case) | {"expected": expected, "rule": rule}
            handle.write(json.dumps(row, default=date.isoformat) + "\n")


def load_cases(path: Path) -> list[Case]:
    cases = []
    for line in path.read_text().splitlines():
        row = json.loads(line)
        del row["expected"], row["rule"]  # derived fields: `ruling` is the source of truth
        for field in ("delivered_on", "requested_on"):
            row[field] = date.fromisoformat(row[field])
        row["plus_since"] = row["plus_since"] and date.fromisoformat(row["plus_since"])
        row["previous_refunds"] = tuple(map(date.fromisoformat, row["previous_refunds"]))
        cases.append(Case(**row))
    return cases


if __name__ == "__main__":
    target = Path(__file__).parent / "data" / "cases.jsonl"
    target.parent.mkdir(exist_ok=True)
    save_cases(generate_cases(DATASET_SIZE), target)
    print(f"wrote {target}")
