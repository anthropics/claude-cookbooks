"""Helpers for the model-as-judge evaluation cookbook.

Everything the notebook needs to turn "does this answer look right?" into a
repeatable, thresholded measurement:

- A small golden dataset of financial-document Q&A (the source documents, the
  20 held-out questions, and their rubrics).
- The judge: per-dimension rubric prompts, an XML parser, and
  ``evaluate_response`` which scores one answer on every quality dimension.
- Aggregation and the regression gate (``check_regression_gate``) that decides
  whether a change is safe to ship.

The evaluation *loop* (batching over the dataset) lives in the notebook so it
stays editable; the scoring *contract* lives here so it is testable and can be
imported by ``run_eval.py`` in CI.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from statistics import mean
from typing import Any

import anthropic

# ---------------------------------------------------------------------------
# Source documents
#
# Three short financial documents the golden questions are written against.
# Keeping the corpus tiny and self-contained means the notebook runs anywhere
# and the "expected" answers are verifiable by eye. The domain (a loan file, a
# trade confirmation, a regulatory excerpt) deliberately mirrors the compliance
# agent cookbook so the two read as a pair.
# ---------------------------------------------------------------------------

DOCUMENTS: dict[str, str] = {
    "loan_application": """\
MORTGAGE APPLICATION — REF MTG-2024-88213
Applicant:            J. Whitfield, age 34, self-employed contractor (2 years trading)
Stated gross income:  GBP 72,000 / year
Requested loan:       GBP 300,000 over 25 years
Property value:       GBP 400,000
Deposit:              GBP 100,000
Existing credit:      GBP 9,200 across 2 facilities, all up to date
Interest rate:        5.0% fixed for 5 years
Affordability check:  [FIELD BLANK]""",
    "trade_confirmation": """\
TRADE CONFIRMATION — REF TRD-2024-00417
Client:          Meridian Holdings SARL
Instruction:     SELL 100,000 shares VODAFONE GROUP PLC
Executed price:  87.4 pence per share
Commission:      0.20% of gross proceeds
Trade date:      2024-06-14
Settlement:      T+2
Venue:           London Stock Exchange""",
    "regulatory_note": """\
INTERNAL COMPLIANCE NOTE — MiFID II SUITABILITY
Under MiFID II, a firm providing investment advice must obtain information on
the client's knowledge and experience, financial situation (including ability
to bear losses), and investment objectives (including risk tolerance).
A suitability report must be provided to retail clients before the transaction.
Where the firm cannot obtain the required information, it must NOT proceed with
a personal recommendation.""",
}


# ---------------------------------------------------------------------------
# Golden dataset
#
# 20 held-out questions across four categories. Each carries the expected
# answer, a free-text rubric describing what a correct answer must contain,
# and metadata (category, difficulty, edge_case). The unanswerable questions
# are the hallucination tripwires: the only correct move is to decline.
# ---------------------------------------------------------------------------

GOLDEN_DATASET: list[dict[str, Any]] = [
    # --- factual extraction (3) ---
    {
        "id": "fe-1",
        "document": "loan_application",
        "question": "What is the applicant's stated gross annual income?",
        "expected": "GBP 72,000 per year.",
        "rubric": "Must state 72,000 GBP (currency and amount). Extra context is fine.",
        "category": "factual_extraction",
        "difficulty": "easy",
        "edge_case": False,
    },
    {
        "id": "fe-3",
        "document": "trade_confirmation",
        "question": "How many Vodafone shares were sold and at what executed price?",
        "expected": "100,000 shares at 87.4 pence per share.",
        "rubric": "Must state both 100,000 shares and 87.4 pence (the price).",
        "category": "factual_extraction",
        "difficulty": "medium",
        "edge_case": False,
    },
    {
        "id": "fe-5",
        "document": "loan_application",
        "question": "What is the fixed interest rate and for how long is it fixed?",
        "expected": "5.0% fixed for 5 years.",
        "rubric": "Must state 5.0% (or 5%) and a 5-year fixed period.",
        "category": "factual_extraction",
        "difficulty": "easy",
        "edge_case": False,
    },
    # --- numerical reasoning (3) ---
    {
        "id": "nr-1",
        "document": "loan_application",
        "question": "What is the loan-to-value (LTV) ratio for this mortgage?",
        "expected": "75% (a 300,000 loan against a 400,000 property).",
        "rubric": "Must arrive at 75%. Accept the correct ratio even if the working is brief.",
        "category": "numerical_reasoning",
        "difficulty": "medium",
        "edge_case": False,
    },
    {
        "id": "nr-3",
        "document": "trade_confirmation",
        "question": "What are the gross proceeds of the sale in GBP?",
        "expected": "GBP 87,400 (100,000 shares x 87.4 pence = 8,740,000 pence = 87,400 pounds).",
        "rubric": "Must arrive at GBP 87,400. The pence-to-pounds conversion is the crux.",
        "category": "numerical_reasoning",
        "difficulty": "hard",
        "edge_case": False,
    },
    {
        "id": "nr-5",
        "document": "loan_application",
        "question": "How much deposit is the applicant putting down as a percentage of the property value?",
        "expected": "25% (100,000 deposit on a 400,000 property).",
        "rubric": "Must arrive at 25%.",
        "category": "numerical_reasoning",
        "difficulty": "medium",
        "edge_case": False,
    },
    # --- compliance interpretation (3) ---
    {
        "id": "ci-1",
        "document": "regulatory_note",
        "question": "Under MiFID II suitability rules, can the firm make a personal recommendation if it cannot obtain the client's financial situation and objectives?",
        "expected": "No. If the firm cannot obtain the required information it must not make a personal recommendation.",
        "rubric": "Must conclude the firm must NOT proceed with a personal recommendation. A 'yes' or hedged answer is wrong.",
        "category": "compliance_interpretation",
        "difficulty": "medium",
        "edge_case": False,
    },
    {
        "id": "ci-4",
        "document": "loan_application",
        "question": "The affordability check field is blank. From a Consumer Duty standpoint, is this application ready for an automated approval decision?",
        "expected": "No. A blank affordability check means the file is incomplete and cannot be approved automatically; it needs a human/affordability assessment first.",
        "rubric": "Must conclude it is NOT ready for automated approval, citing the missing affordability check.",
        "category": "compliance_interpretation",
        "difficulty": "hard",
        "edge_case": False,
    },
    {
        "id": "ci-5",
        "document": "trade_confirmation",
        "question": "Does this trade confirmation on its own show that a MiFID II suitability assessment was performed?",
        "expected": "No. The confirmation records execution details only; it contains no evidence of a suitability assessment.",
        "rubric": "Must conclude the confirmation does not evidence a suitability assessment.",
        "category": "compliance_interpretation",
        "difficulty": "hard",
        "edge_case": False,
    },
    # --- ambiguous / unanswerable (3): the hallucination tripwires ---
    {
        "id": "au-1",
        "document": "loan_application",
        "question": "What is the applicant's credit score?",
        "expected": "The document does not state a credit score; it cannot be determined from this file.",
        "rubric": "Must decline: the credit score is not in the document. Inventing any number is a failure.",
        "category": "ambiguous_unanswerable",
        "difficulty": "medium",
        "edge_case": True,
    },
    {
        "id": "au-3",
        "document": "loan_application",
        "question": "Has this mortgage application been approved?",
        "expected": "The document does not record an approval decision; it cannot be determined.",
        "rubric": "Must decline: no decision is recorded. Asserting approved/declined is a failure.",
        "category": "ambiguous_unanswerable",
        "difficulty": "medium",
        "edge_case": True,
    },
    {
        "id": "au-4",
        "document": "regulatory_note",
        "question": "What is the maximum fine for a MiFID II suitability breach?",
        "expected": "The note does not state any fine amount; it cannot be determined from this document.",
        "rubric": "Must decline: no fine is mentioned. Quoting a figure is a failure.",
        "category": "ambiguous_unanswerable",
        "difficulty": "hard",
        "edge_case": True,
    },
]


# ---------------------------------------------------------------------------
# Quality dimensions
#
# Four independent axes, each scored 1-5 by its own judge call. Splitting them
# out (rather than asking for one overall score) is what avoids the halo
# effect: a fluent, confident answer should not inflate its correctness score.
# For every dimension a HIGHER score is better, including hallucination, where
# 5 means "fully grounded" and 1 means "fabricated content".
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Dimension:
    name: str
    description: str
    scale: str
    weight: float


DIMENSIONS: list[Dimension] = [
    Dimension(
        name="correctness",
        description="Is the answer factually right relative to the reference answer and the source document?",
        scale=(
            "5 = fully correct, matches the reference. "
            "4 = correct with a trivial omission. "
            "3 = partially correct, one material error. "
            "2 = mostly wrong. "
            "1 = entirely wrong or contradicts the document."
        ),
        weight=0.40,
    ),
    Dimension(
        name="completeness",
        description="Does the answer cover everything the question and rubric ask for?",
        scale=(
            "5 = every required element present. "
            "4 = one minor element missing. "
            "3 = a required element missing. "
            "2 = several elements missing. "
            "1 = barely addresses the question."
        ),
        weight=0.25,
    ),
    Dimension(
        name="hallucination",
        description=(
            "Is every claim grounded in the source document? Penalize invented figures, "
            "fabricated facts, or confident answers to unanswerable questions. "
            "Declining to answer when the document lacks the information is GOOD grounding, not a failure."
        ),
        scale=(
            "5 = fully grounded, no fabrication (includes correctly declining to answer). "
            "4 = grounded but slightly over-reaches. "
            "3 = one unsupported claim. "
            "2 = multiple unsupported claims. "
            "1 = largely fabricated."
        ),
        weight=0.25,
    ),
    Dimension(
        name="tone",
        description="Is the register appropriate for a regulated financial setting: precise, professional, no undue hedging or bravado?",
        scale=(
            "5 = precise and professional. "
            "4 = minor lapses. "
            "3 = noticeably casual or verbose. "
            "2 = unprofessional. "
            "1 = inappropriate for the domain."
        ),
        weight=0.10,
    ),
]

DIMENSION_BY_NAME: dict[str, Dimension] = {d.name: d for d in DIMENSIONS}


# ---------------------------------------------------------------------------
# Judge prompt
# ---------------------------------------------------------------------------

JUDGE_PROMPT_TEMPLATE = """\
You are a meticulous evaluator scoring ONE quality dimension of an answer to a \
question about a financial document. Score only the dimension named below; \
ignore every other quality.

Dimension: {dimension_name}
{dimension_description}

Scoring scale (integer 1-5):
{dimension_scale}

<source_document>
{document}
</source_document>

<question>
{question}
</question>

<reference_answer>
{expected}
</reference_answer>

<rubric>
{rubric}
</rubric>

<candidate_answer>
{actual}
</candidate_answer>

First reason step by step about how the candidate answer measures up on the \
{dimension_name} dimension only. Then output an integer score from 1 to 5.

Reply in EXACTLY this XML format and nothing else:
<evaluation>
<reasoning>two to four sentences of assessment</reasoning>
<score>an integer from 1 to 5</score>
</evaluation>"""


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------


@dataclass
class EvalResult:
    """The scored evaluation of a single answer across all dimensions."""

    question_id: str
    category: str
    scores: dict[str, int]  # dimension name -> 1..5
    rationales: dict[str, str]  # dimension name -> judge reasoning
    overall: float  # weighted mean of the dimension scores

    def to_row(self) -> dict[str, Any]:
        """Flatten to a dict suitable for a pandas DataFrame."""
        row: dict[str, Any] = {"question_id": self.question_id, "category": self.category}
        row.update(self.scores)
        row["overall"] = round(self.overall, 2)
        return row

    def to_dict(self) -> dict[str, Any]:
        """Serialize for saving a baseline to JSON."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EvalResult:
        """Reload from a saved baseline JSON record."""
        return cls(
            question_id=data["question_id"],
            category=data["category"],
            scores=data["scores"],
            rationales=data.get("rationales", {}),
            overall=data["overall"],
        )


@dataclass
class GateCheck:
    """One threshold check within the regression gate."""

    label: str  # e.g. "hallucination floor"
    passed: bool
    detail: str  # human-readable value-vs-threshold line


@dataclass
class GateResult:
    """The verdict of the regression gate: every check, and the overall pass/fail."""

    checks: list[GateCheck] = field(default_factory=list)
    deltas: dict[str, float] = field(default_factory=dict)  # metric -> current - baseline

    @property
    def passed(self) -> bool:
        return all(c.passed for c in self.checks)

    @property
    def breaches(self) -> list[str]:
        return [c.detail for c in self.checks if not c.passed]

    def summary(self) -> str:
        head = "PASS" if self.passed else "FAIL"
        lines = [
            f"[{head}] regression gate — {len(self.breaches)} of {len(self.checks)} checks breached"
        ]
        for c in self.checks:
            mark = "ok  " if c.passed else "FAIL"
            lines.append(f"  [{mark}] {c.label}: {c.detail}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Judge
# ---------------------------------------------------------------------------


def parse_judge_xml(text: str) -> tuple[int, str]:
    """Pull the integer score and reasoning out of the judge's XML reply.

    Defensive on purpose: a judge that returns an unparseable score is an
    evaluation failure we want to see loudly, not a silent zero.
    """
    score_match = re.search(r"<score>\s*(\d+)\s*</score>", text)
    reason_match = re.search(r"<reasoning>\s*(.*?)\s*</reasoning>", text, re.DOTALL)
    if not score_match:
        raise ValueError(f"judge returned no parseable <score>: {text[:200]!r}")
    score = int(score_match.group(1))
    if not 1 <= score <= 5:
        raise ValueError(f"judge score out of range 1-5: {score}")
    reasoning = reason_match.group(1).strip() if reason_match else ""
    return score, reasoning


def score_dimension(
    client: anthropic.Anthropic,
    judge_model: str,
    dimension: Dimension,
    *,
    document: str,
    question: str,
    expected: str,
    rubric: str,
    actual: str,
    parse_retries: int = 2,
) -> tuple[int, str]:
    """One judge call for one dimension. Returns (score, reasoning).

    Transport errors are handled by the SDK's own retry logic. Here we add a
    small retry for the rare case where the judge returns unparseable XML, so a
    single formatting hiccup does not fail an entire suite run.
    """
    prompt = JUDGE_PROMPT_TEMPLATE.format(
        dimension_name=dimension.name,
        dimension_description=dimension.description,
        dimension_scale=dimension.scale,
        document=document,
        question=question,
        expected=expected,
        rubric=rubric,
        actual=actual,
    )
    last_error: Exception | None = None
    for _ in range(parse_retries + 1):
        response = client.messages.create(
            model=judge_model,
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(block.text for block in response.content if block.type == "text")
        try:
            return parse_judge_xml(text)
        except ValueError as exc:
            last_error = exc
    raise ValueError(f"judge output unparseable after retries: {last_error}")


def weighted_overall(scores: dict[str, int]) -> float:
    """Weighted mean of dimension scores, on the same 1-5 scale."""
    total_weight = sum(DIMENSION_BY_NAME[name].weight for name in scores)
    return sum(scores[name] * DIMENSION_BY_NAME[name].weight for name in scores) / total_weight


def evaluate_response(
    client: anthropic.Anthropic,
    judge_model: str,
    *,
    question_id: str,
    category: str,
    document: str,
    question: str,
    expected: str,
    rubric: str,
    actual: str,
) -> EvalResult:
    """Score one candidate answer on every dimension, one judge call each.

    Runs the dimensions independently so no single judgement can bias another
    (the halo effect). The weighted ``overall`` is a convenience roll-up; the
    per-dimension scores are what the regression gate actually reasons over.
    """
    scores: dict[str, int] = {}
    rationales: dict[str, str] = {}
    for dimension in DIMENSIONS:
        score, reasoning = score_dimension(
            client,
            judge_model,
            dimension,
            document=document,
            question=question,
            expected=expected,
            rubric=rubric,
            actual=actual,
        )
        scores[dimension.name] = score
        rationales[dimension.name] = reasoning
    return EvalResult(
        question_id=question_id,
        category=category,
        scores=scores,
        rationales=rationales,
        overall=weighted_overall(scores),
    )


# ---------------------------------------------------------------------------
# Suite runner
# ---------------------------------------------------------------------------


def run_suite(
    client: anthropic.Anthropic,
    judge_model: str,
    answer_fn: Callable[[dict[str, Any]], str],
    dataset: list[dict[str, Any]],
    *,
    max_workers: int = 3,
) -> list[EvalResult]:
    """Answer and score every question in ``dataset``, preserving input order.

    ``answer_fn`` is the system under test: given a golden record it returns the
    candidate answer string. Each question's answer-then-judge chain is
    independent, so we fan them out across a small thread pool — the synchronous
    Anthropic client is thread-safe, and this turns a serial minutes-long run
    into a parallel one. ``max_workers`` is kept modest to stay within rate limits.
    """

    def _one(record: dict[str, Any]) -> EvalResult:
        actual = answer_fn(record)
        return evaluate_response(
            client,
            judge_model,
            question_id=record["id"],
            category=record["category"],
            document=DOCUMENTS[record["document"]],
            question=record["question"],
            expected=record["expected"],
            rubric=record["rubric"],
            actual=actual,
        )

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        return list(pool.map(_one, dataset))


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------


def aggregate(results: list[EvalResult]) -> dict[str, Any]:
    """Roll a list of EvalResults up into overall, per-dimension, and per-category means."""
    if not results:
        raise ValueError("no results to aggregate")
    dims = [d.name for d in DIMENSIONS]
    per_dimension = {name: mean(r.scores[name] for r in results) for name in dims}
    categories = sorted({r.category for r in results})
    per_category = {
        cat: {
            "overall": mean(r.overall for r in results if r.category == cat),
            **{name: mean(r.scores[name] for r in results if r.category == cat) for name in dims},
        }
        for cat in categories
    }
    return {
        "n": len(results),
        "overall": mean(r.overall for r in results),
        "per_dimension": per_dimension,
        "per_category": per_category,
    }


# ---------------------------------------------------------------------------
# Regression gate
# ---------------------------------------------------------------------------

# Default thresholds. These are policy, not model output: a team sets them once
# and every candidate change is measured against them.
DEFAULT_THRESHOLDS: dict[str, Any] = {
    # Overall weighted score may not fall by more than this fraction of baseline.
    "max_overall_drop_pct": 5.0,
    # Absolute floor on the mean hallucination score (grounding must stay high).
    "min_hallucination": 4.0,
    # Absolute floor on the mean overall score within named categories.
    "category_floors": {"compliance_interpretation": 4.5},
}


def check_regression_gate(
    baseline: list[EvalResult],
    current: list[EvalResult],
    thresholds: dict[str, Any] | None = None,
) -> GateResult:
    """Decide whether ``current`` is safe to ship relative to ``baseline``.

    Three kinds of check, any of which can fail the gate:
      1. Overall score must not drop more than ``max_overall_drop_pct`` percent.
      2. Mean hallucination score must stay at or above ``min_hallucination``.
      3. Each named category's overall must stay at or above its floor.
    """
    thresholds = thresholds or DEFAULT_THRESHOLDS
    base_agg = aggregate(baseline)
    cur_agg = aggregate(current)
    checks: list[GateCheck] = []
    deltas: dict[str, float] = {}

    # 1. Overall regression.
    base_overall = base_agg["overall"]
    cur_overall = cur_agg["overall"]
    drop_pct = (base_overall - cur_overall) / base_overall * 100 if base_overall else 0.0
    deltas["overall"] = cur_overall - base_overall
    checks.append(
        GateCheck(
            label="overall regression",
            passed=drop_pct <= thresholds["max_overall_drop_pct"],
            detail=(
                f"{base_overall:.2f} -> {cur_overall:.2f} "
                f"({'-' if drop_pct >= 0 else '+'}{abs(drop_pct):.1f}%), "
                f"max allowed drop {thresholds['max_overall_drop_pct']:.1f}%"
            ),
        )
    )

    # 2. Hallucination floor.
    cur_halluc = cur_agg["per_dimension"]["hallucination"]
    deltas["hallucination"] = cur_halluc - base_agg["per_dimension"]["hallucination"]
    checks.append(
        GateCheck(
            label="hallucination floor",
            passed=cur_halluc >= thresholds["min_hallucination"],
            detail=f"{cur_halluc:.2f} vs floor {thresholds['min_hallucination']:.2f}",
        )
    )

    # 3. Per-category floors.
    for cat, floor in thresholds.get("category_floors", {}).items():
        cur_cat = cur_agg["per_category"].get(cat, {}).get("overall")
        if cur_cat is None:
            continue
        base_cat = base_agg["per_category"].get(cat, {}).get("overall", cur_cat)
        deltas[f"category:{cat}"] = cur_cat - base_cat
        checks.append(
            GateCheck(
                label=f"category floor: {cat}",
                passed=cur_cat >= floor,
                detail=f"{cur_cat:.2f} vs floor {floor:.2f} (baseline {base_cat:.2f})",
            )
        )

    return GateResult(checks=checks, deltas=deltas)
