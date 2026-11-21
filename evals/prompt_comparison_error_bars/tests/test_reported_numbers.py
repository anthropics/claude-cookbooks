"""Every number quoted in prose must come from the recorded run.

The figures are recomputed from results/main.jsonl and looked up in the READMEs and in the
notebook's markdown. If a rerun changes the results, this fails until the prose is updated.
"""

import json
from pathlib import Path

import pytest
from batch_runner import cost_usd, load_rows, scores_by_prompt
from error_bars import (
    detectable_effect,
    mean_ci,
    paired_diff_ci,
    projected_margin,
    sign_test_p,
    unpaired_diff_ci,
    variance_components,
)
from refund_task import load_cases, ruling

RECIPE = Path(__file__).resolve().parent.parent

CASES = load_cases(RECIPE / "data" / "cases.jsonl")
ROWS = load_rows(RECIPE / "results" / "main.jsonl")
SCORES, LEFT_OUT = scores_by_prompt(ROWS, CASES)
DRAFT, PROSE, PROCEDURE = SCORES["draft"], SCORES["prose"], SCORES["procedure"]
ONCE = {name: scores[:100, 0] for name, scores in SCORES.items()}  # 100 cases, one run

SENTENCE = paired_diff_ci(DRAFT, PROSE)
REWRITE = paired_diff_ci(PROSE, PROCEDURE)
SENTENCE_SMALL = paired_diff_ci(ONCE["draft"], ONCE["prose"])
REWRITE_SMALL = paired_diff_ci(ONCE["prose"], ONCE["procedure"])
COST = f"${cost_usd(ROWS, 0.10, 0.50):.2f}"


def one_line(path: Path) -> str:
    return " ".join(path.read_text().split())


README = one_line(RECIPE / "README.md")
RESULTS_README = one_line(RECIPE / "results" / "README.md")
NOTEBOOK = " ".join(
    " ".join("".join(cell["source"]).split())
    for cell in json.loads((RECIPE / "guide.ipynb").read_text())["cells"]
    if cell["cell_type"] == "markdown"
)


def points(value: float) -> str:
    """A difference in percentage points with its sign, as the prose writes it: +5.1, -0.6."""
    return f"{100 * value:+.1f}"


def span(estimate) -> str:
    return f"{points(estimate.low)} to {points(estimate.high)}"


def test_recorded_run_is_complete() -> None:
    assert DRAFT.shape == PROSE.shape == PROCEDURE.shape == (600, 3) and LEFT_OUT == []
    assert {row["outcome"] for row in ROWS} == {"end_turn"}
    assert f"{len(ROWS):,} requests" in RESULTS_README


def headline_figures() -> list[str]:
    """What any summary of this run has to get right. Also used by the repository's README test."""
    return [
        *(f"{mean_ci(scores)}" for scores in (DRAFT, PROSE, PROCEDURE)),
        f"{points(SENTENCE.value)} points",
        span(SENTENCE),
        f"{points(REWRITE.value)} points",
        span(REWRITE),
        span(SENTENCE_SMALL),
        span(REWRITE_SMALL),
        f"a drop of more than about {-100 * REWRITE.low:.1f} points",
        COST,
    ]


@pytest.mark.parametrize("figure", headline_figures())
def test_readme_quotes_the_recorded_results(figure: str) -> None:
    assert figure in README


def test_results_readme_quotes_tokens_and_cost() -> None:
    assert f"{sum(row['input_tokens'] for row in ROWS):,} input tokens" in RESULTS_README
    assert f"{sum(row['output_tokens'] for row in ROWS):,} output tokens" in RESULTS_README
    assert COST in RESULTS_README


def test_notebook_headline_claims() -> None:
    for claim in [
        COST,
        f"improved the score by {100 * SENTENCE.value:.1f} points ({span(SENTENCE)})",
        f"changed it by {points(REWRITE.value)} points ({span(REWRITE)})",
        f"The difference is {points(SENTENCE.value)} points with an interval of {span(SENTENCE)}",
        f"Its interval, {span(REWRITE)} points, includes zero",
        f"rules out a drop of more than about {-100 * REWRITE.low:.1f} points",
        f"with a drop of more than about {-100 * REWRITE.low:.1f} points ruled out",
        f"a baseline that fails about {round(100 * (1 - mean_ci(DRAFT).value))} requests in 100",
    ]:
        assert claim in NOTEBOOK, claim
    assert SENTENCE.low > 0 and REWRITE.low < 0 < REWRITE.high


def test_notebook_claims_about_the_first_100_cases() -> None:
    flipped = int((DRAFT[:100, 0] != DRAFT[:100, 1]).sum())
    wins = int((ONCE["prose"] > ONCE["draft"]).sum())
    losses = int((ONCE["prose"] < ONCE["draft"]).sum())
    exact = sign_test_p(ONCE["draft"], ONCE["prose"])

    for claim in [
        f"scored {DRAFT[:100, 0].mean():.0%} and then {DRAFT[:100, 1].mean():.0%}",
        f"{flipped} of the 100 cases changed outcome",
        f"split on {wins + losses} cases, {wins} one way and {losses} the other",
        f"gives p = {exact:.3f}",
        f"up to {100 * REWRITE_SMALL.high:.1f} points better or {-100 * REWRITE_SMALL.low:.1f} points worse",
        f"anywhere from {100 * SENTENCE_SMALL.low:.1f} to {100 * SENTENCE_SMALL.high:.1f} points",
        f"that interval reached {points(REWRITE_SMALL.low)}",
    ]:
        assert claim in NOTEBOOK, claim

    # "the sentence is worth six points, and the rewrite ... changes nothing"
    assert round(100 * (ONCE["prose"].mean() - ONCE["draft"].mean())) == 6
    assert ONCE["prose"].mean() == ONCE["procedure"].mean()
    # borderline: the interval clears zero and the exact test does not clear 0.05
    assert SENTENCE_SMALL.low > 0 and exact > 0.05
    # pairing: "about a tenth off the first interval and more than a quarter off the second"
    saved = [
        1 - paired_diff_ci(ONCE[a], ONCE[b]).margin / unpaired_diff_ci(ONCE[a], ONCE[b]).margin
        for a, b in (("draft", "prose"), ("prose", "procedure"))
    ]
    assert 0.07 < saved[0] < 0.13 and saved[1] > 0.25
    # "Pairing took about a tenth off both intervals at full size"
    for before, after in ((DRAFT, PROSE), (PROSE, PROCEDURE)):
        full_saving = (
            1 - paired_diff_ci(before, after).margin / unpaired_diff_ci(before, after).margin
        )
        assert 0.07 < full_saving < 0.13


def test_notebook_claims_about_noise_and_sample_size() -> None:
    between_cases, between_runs = variance_components(PROSE - DRAFT)
    right = DRAFT.sum(axis=1)
    ever_wrong, sometimes_right = int((right < 3).sum()), int(((right > 0) & (right < 3)).sum())

    assert (
        f"Of the {ever_wrong} cases the `draft` prompt ever got wrong, {sometimes_right} were right"
        in NOTEBOOK
    )
    assert 0.5 < between_runs / (between_cases + between_runs) < 0.6  # "a little over half"

    def margin(cases: int, runs: int) -> str:
        return f"{projected_margin(between_cases, between_runs, cases, runs):.1%}"

    assert f"plus or minus {margin(100, 3)} as 100 cases run three times" in NOTEBOOK
    assert f"plus or minus {margin(300, 1)} as 300 cases run once" in NOTEBOOK
    assert f"from {margin(100, 1)} to {margin(100, 3)} with no new labelling" in NOTEBOOK

    detects = [
        100 * detectable_effect(600, float((after - before).mean(axis=1).std(ddof=1)))
        for before, after in ((DRAFT, PROSE), (PROSE, PROCEDURE))
    ]
    assert (
        f"about {detects[0]:.1f} points from the first change and about {detects[1]:.1f} points"
        in NOTEBOOK
    )


def test_notebook_claims_about_individual_rules() -> None:
    truth = {case.case_id: ruling(case) for case in CASES}
    wrong = [row for row in ROWS if row["decision"] != truth[row["case_id"]][0]]

    def count(prompt: str, **where: str) -> int:
        return sum(
            row["prompt"] == prompt
            and where.get("expected", truth[row["case_id"]][0]) == truth[row["case_id"]][0]
            and where.get("said", row["decision"]) == row["decision"]
            and where.get("rule", truth[row["case_id"]][1]) == truth[row["case_id"]][1]
            for row in wrong
        )

    gift_card_cases = {c.case_id for c in CASES if truth[c.case_id][1] == "gift_card"}
    hit_by_procedure = {
        row["case_id"]
        for row in wrong
        if row["prompt"] == "procedure" and row["case_id"] in gift_card_cases
    }
    for claim in [
        f"{count('draft', expected='deny', said='escalate')} of the {count('draft')} wrong attempts",
        f"another {count('draft', expected='approve', said='escalate')} are requests it should",
        f"fall from {count('draft', expected='deny', said='escalate')} to "
        f"{count('prose', expected='deny', said='escalate')} and from "
        f"{count('draft', expected='approve', said='escalate')} to "
        f"{count('prose', expected='approve', said='escalate')}",
        f"({count('prose', expected='approve')} wrong attempts down to "
        f"{count('procedure', expected='approve')})",
        f"({count('procedure', rule='gift_card')} against {count('prose', rule='gift_card')}, "
        f"spread over {len(hit_by_procedure)} of the {len(gift_card_cases)} gift-card cases)",
        f"leaves the totals at {count('prose')} and {count('procedure')}",
        f"one row picked out of {len({rule for _, rule in truth.values()})}",
    ]:
        assert claim in NOTEBOOK, claim
