"""The labels are only "correct by construction" if the policy code is right. Pin it down."""

import json
from collections import Counter
from dataclasses import replace
from datetime import date, timedelta
from pathlib import Path

import pytest
from refund_task import (
    DATASET_SIZE,
    DECISIONS,
    PROMPTS,
    Case,
    decide,
    generate_cases,
    load_cases,
    render_ticket,
    ruling,
    save_cases,
)

DATA = Path(__file__).resolve().parent.parent / "data" / "cases.jsonl"
DELIVERED = date(2026, 3, 1)

# A plain request that the policy approves. Each test changes only what it is about.
ELIGIBLE = Case(
    case_id="case-test",
    order_on_file=True,
    category="apparel",
    item="down vest",
    quantity=1,
    unit_price_usd=100,
    final_sale=False,
    delivered_on=DELIVERED,
    requested_on=DELIVERED + timedelta(days=10),
    reason="changed_mind",
    opened=False,
    plus_since=None,
    previous_refunds=(),
    message="Not for me.",
)


def case(
    days: int | None = None,
    refund_ages: tuple[int, ...] | None = None,
    plus_joined: int | None = None,
    **changes,
) -> Case:
    """`days` after delivery; refunds `refund_ages` days before the request; Plus joined
    `plus_joined` days after delivery (negative: before)."""
    if days is not None:
        changes["requested_on"] = DELIVERED + timedelta(days=days)
    if plus_joined is not None:
        changes["plus_since"] = DELIVERED + timedelta(days=plus_joined)
    if refund_ages is not None:
        requested_on = changes.get("requested_on", ELIGIBLE.requested_on)
        changes["previous_refunds"] = tuple(requested_on - timedelta(days=a) for a in refund_ages)
    return replace(ELIGIBLE, **changes)


@pytest.mark.parametrize(
    ("changed", "expected"),
    [
        (case(), ("approve", "eligible")),
        # Change of mind: 30 days inclusive.
        (case(days=30), ("approve", "eligible")),
        (case(days=31), ("deny", "outside_window")),
        # Plus members get 45 days, but only if they had joined by the delivery date.
        (case(days=45, plus_joined=-100), ("approve", "eligible")),
        (case(days=46, plus_joined=-100), ("deny", "outside_window")),
        (case(days=40, plus_joined=0), ("approve", "eligible")),
        (case(days=40, plus_joined=1), ("deny", "outside_window")),
        (case(days=20, plus_joined=5), ("approve", "eligible")),
        # Items that cannot come back for a change of mind.
        (case(final_sale=True), ("deny", "not_returnable")),
        (case(category="grocery"), ("deny", "not_returnable")),
        (case(category="electronics", opened=True), ("deny", "opened_electronics")),
        (case(category="electronics", opened=False), ("approve", "eligible")),
        (case(opened=True), ("approve", "eligible")),  # opened apparel is fine
        # Seller fault: 60 days, and the change-of-mind exclusions do not apply.
        (case(days=60, reason="wrong_item"), ("approve", "eligible")),
        (case(days=61, reason="wrong_item"), ("deny", "seller_fault_too_late")),
        (case(days=40, reason="defective", final_sale=True), ("approve", "eligible")),
        (
            case(days=5, reason="defective", category="electronics", opened=True),
            ("approve", "eligible"),
        ),
        # Damage in transit: 14 days.
        (case(days=14, reason="damaged_in_transit"), ("approve", "eligible")),
        (case(days=15, reason="damaged_in_transit"), ("deny", "damage_reported_late")),
        (
            case(days=15, reason="damaged_in_transit", category="electronics"),
            ("deny", "damage_reported_late"),
        ),
        # Groceries: 7 days for any seller fault, tighter than the damage limit.
        (case(days=7, reason="defective", category="grocery"), ("approve", "eligible")),
        (case(days=8, reason="defective", category="grocery"), ("deny", "grocery_reported_late")),
        (
            case(days=10, reason="damaged_in_transit", category="grocery"),
            ("deny", "grocery_reported_late"),
        ),
        (case(days=8, reason="wrong_item", category="grocery"), ("deny", "grocery_reported_late")),
        # Warranty: defective electronics only, day 61 to day 365.
        (case(days=61, reason="defective", category="electronics"), ("escalate", "warranty")),
        (case(days=365, reason="defective", category="electronics"), ("escalate", "warranty")),
        (
            case(days=366, reason="defective", category="electronics"),
            ("deny", "seller_fault_too_late"),
        ),
        (
            case(days=100, reason="wrong_item", category="electronics"),
            ("deny", "seller_fault_too_late"),
        ),
        (case(days=100, reason="defective"), ("deny", "seller_fault_too_late")),
        # Sign-off: the order line, and only for refunds that would otherwise be approved.
        (case(unit_price_usd=400), ("approve", "eligible")),
        (case(unit_price_usd=401), ("escalate", "needs_sign_off")),
        (case(unit_price_usd=200, quantity=2), ("approve", "eligible")),
        (case(unit_price_usd=134, quantity=3), ("escalate", "needs_sign_off")),
        (case(unit_price_usd=900, days=31), ("deny", "outside_window")),
        (case(unit_price_usd=900, days=20, reason="defective"), ("escalate", "needs_sign_off")),
        # Gift cards.
        (case(category="gift_card"), ("deny", "gift_card")),
        # Repeat refunds: three or more in the last 90 days, day 90 included.
        (case(refund_ages=(10, 20)), ("approve", "eligible")),
        (case(refund_ages=(10, 20, 90)), ("escalate", "repeat_refunds")),
        (case(refund_ages=(10, 20, 91)), ("approve", "eligible")),
        (case(refund_ages=(91, 120, 150, 200)), ("approve", "eligible")),
        (case(refund_ages=(5, 6, 7), category="gift_card"), ("escalate", "repeat_refunds")),
        (case(refund_ages=(5, 6, 7, 8), days=200), ("escalate", "repeat_refunds")),
        # No order on file comes before everything.
        (case(order_on_file=False, category="gift_card"), ("escalate", "no_order_on_file")),
    ],
)
def test_policy(changed: Case, expected: tuple[str, str]) -> None:
    assert ruling(changed) == expected
    assert decide(changed) == expected[0]


def test_day_count_crosses_month_ends() -> None:
    late_january = case(delivered_on=date(2026, 1, 30), requested_on=date(2026, 3, 1))
    assert late_january.days_since_delivery == 30


def test_generation_is_reproducible() -> None:
    assert generate_cases(50, seed=7) == generate_cases(50, seed=7)
    assert generate_cases(50, seed=7) != generate_cases(50, seed=8)


def test_generated_set_exercises_the_whole_policy() -> None:
    cases = generate_cases(DATASET_SIZE)
    decisions = Counter(decide(c) for c in cases)
    rules = Counter(ruling(c)[1] for c in cases)

    assert set(decisions) == set(DECISIONS)
    assert min(decisions.values()) >= 0.2 * len(cases), decisions
    assert len(rules) == 12 and min(rules.values()) >= 15, rules


def test_generated_refunds_always_precede_the_request() -> None:
    for generated in generate_cases(DATASET_SIZE):
        assert all(refund < generated.requested_on for refund in generated.previous_refunds)
        assert len(set(generated.previous_refunds)) == len(generated.previous_refunds)


def test_ticket_states_every_fact_the_policy_uses() -> None:
    ticket = render_ticket(
        case(
            days=31,
            refund_ages=(40, 5),
            plus_joined=-28,
            category="electronics",
            quantity=2,
            unit_price_usd=201,
            final_sale=True,
            opened=True,
            reason="damaged_in_transit",
        )
    )
    for fact in [
        "Order on file: yes",
        "(electronics)",
        "Quantity: 2",
        "Unit price: $201",
        "Final sale: yes",
        "Delivered: 1 March 2026",
        "Package opened: yes",
        "Plus member: since 1 February 2026",
        "Previous refunds: 20 February 2026, 27 March 2026",
        "Received: 1 April 2026",
        "Reason: damaged in transit",
    ]:
        assert fact in ticket

    plain = render_ticket(case())
    assert "Plus member: no" in plain and "Previous refunds: none" in plain


def test_both_prompts_carry_the_same_thresholds() -> None:
    for prompt in PROMPTS.values():
        for number in ("7 days", "14 days", "30 days", "45 days", "60 days", "365 days", "$400"):
            assert number in prompt
        assert "90 days" in prompt and "3 or more" in prompt


def test_the_draft_is_the_prose_prompt_minus_one_sentence() -> None:
    from refund_task import DEFAULT_SENTENCE

    assert DEFAULT_SENTENCE in PROMPTS["prose"]
    assert PROMPTS["prose"].replace(DEFAULT_SENTENCE, "") == PROMPTS["draft"]
    assert "{default}" not in "".join(PROMPTS.values())


def test_round_trip_through_jsonl(tmp_path: Path) -> None:
    cases = generate_cases(20, seed=3)
    path = tmp_path / "cases.jsonl"
    save_cases(cases, path)
    assert load_cases(path) == cases


def test_committed_dataset_matches_the_generator_and_the_policy() -> None:
    assert load_cases(DATA) == generate_cases(DATASET_SIZE)
    for line, generated in zip(
        DATA.read_text().splitlines(), generate_cases(DATASET_SIZE), strict=True
    ):
        assert json.loads(line)["expected"] == decide(generated)
