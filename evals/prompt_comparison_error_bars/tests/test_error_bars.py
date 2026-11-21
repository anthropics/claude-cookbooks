"""The intervals have to mean what they say. Check them against arithmetic and simulation."""

import numpy as np
import pytest
from error_bars import (
    Estimate,
    bootstrap_diff_ci,
    detectable_effect,
    mean_ci,
    paired_diff_ci,
    projected_margin,
    required_cases,
    sign_test_p,
    unpaired_diff_ci,
    variance_components,
    verdict,
)

Z95 = 1.959964


def simulate(rng: np.random.Generator, cases: int, runs: int, lift: float, spread: float = 1.0):
    """Two prompts on the same cases. Each case has its own difficulty; the candidate
    converts a fraction `lift` of the baseline's failures.

    Case pass rates are Beta(4 * spread, 2 * spread), mean 2/3, so the true difference is
    `lift / 3`. A small `spread` makes cases either reliably passed or reliably failed.
    """
    pass_rate = rng.beta(4 * spread, 2 * spread, size=cases)
    baseline = rng.random((cases, runs)) < pass_rate[:, None]
    candidate = rng.random((cases, runs)) < (pass_rate + lift * (1 - pass_rate))[:, None]
    return baseline, candidate


def test_mean_ci_matches_hand_arithmetic() -> None:
    estimate = mean_ci([1, 1, 0, 1])  # mean 0.75, sample sd 0.5, standard error 0.25

    assert estimate.value == pytest.approx(0.75)
    assert estimate.standard_error == pytest.approx(0.25)
    assert estimate.low == pytest.approx(0.75 - Z95 * 0.25, abs=1e-6)
    assert estimate.high == pytest.approx(0.75 + Z95 * 0.25, abs=1e-6)
    assert estimate.margin == pytest.approx(Z95 * 0.25, abs=1e-6)
    assert estimate.cases == 4


def test_interval_narrows_with_the_square_root_of_the_cases() -> None:
    rng = np.random.default_rng(0)
    small = mean_ci(rng.random(100) < 0.8)
    large = mean_ci(rng.random(10_000) < 0.8)

    assert large.margin == pytest.approx(small.margin / 10, rel=0.15)


def test_repeating_a_run_does_not_buy_precision() -> None:
    """Three copies of one run are still one run: the case is the unit, not the attempt."""
    one_run = np.random.default_rng(1).random(200) < 0.7
    three_copies = np.column_stack([one_run] * 3)

    assert mean_ci(three_copies) == mean_ci(one_run)


def test_paired_difference_matches_hand_arithmetic() -> None:
    baseline = [1, 0, 0, 1, 0]
    candidate = [1, 1, 0, 1, 1]  # differences 0, 1, 0, 0, 1: mean 0.4, sample sd sqrt(0.3)
    estimate = paired_diff_ci(baseline, candidate)

    assert estimate.value == pytest.approx(0.4)
    assert estimate.standard_error == pytest.approx((0.3 / 5) ** 0.5)


def test_pairing_pays_off_when_the_same_cases_are_hard_for_both_prompts() -> None:
    """With pass rates near 0 or 1 the two prompts agree case by case, and pairing removes
    that shared difficulty. With pass rates near the middle there is little to remove."""
    rng = np.random.default_rng(2)
    consistent = simulate(rng, cases=400, runs=1, lift=0.3, spread=0.1)
    coin_flips = simulate(rng, cases=400, runs=1, lift=0.3, spread=50)

    paired, unpaired = paired_diff_ci(*consistent), unpaired_diff_ci(*consistent)
    assert paired.value == pytest.approx(unpaired.value)
    assert paired.margin < 0.75 * unpaired.margin

    paired, unpaired = paired_diff_ci(*coin_flips), unpaired_diff_ci(*coin_flips)
    assert paired.margin == pytest.approx(unpaired.margin, rel=0.1)


def test_paired_comparison_rejects_mismatched_case_sets() -> None:
    with pytest.raises(ValueError, match="same cases"):
        paired_diff_ci([1, 0, 1], [1, 0])


def test_an_interval_needs_two_cases() -> None:
    with pytest.raises(ValueError, match="at least two cases"):
        mean_ci([1])


def test_bootstrap_agrees_with_the_formula() -> None:
    baseline, candidate = simulate(np.random.default_rng(3), cases=300, runs=3, lift=0.3)
    formula, bootstrap = paired_diff_ci(baseline, candidate), bootstrap_diff_ci(baseline, candidate)

    assert bootstrap.value == pytest.approx(formula.value)
    assert bootstrap.low == pytest.approx(formula.low, abs=0.005)
    assert bootstrap.high == pytest.approx(formula.high, abs=0.005)


def test_bootstrap_counts_cases_and_handles_odd_resample_counts() -> None:
    baseline, candidate = simulate(np.random.default_rng(4), cases=50, runs=2, lift=0.3)
    estimate = bootstrap_diff_ci(baseline, candidate, resamples=2500)

    assert estimate.cases == 50
    assert estimate.low < estimate.value < estimate.high


@pytest.mark.parametrize(
    ("wins", "losses", "expected"),
    [(7, 1, 18 / 256), (1, 7, 18 / 256), (8, 0, 2 / 256), (4, 4, 1.0), (0, 0, 1.0)],
)
def test_sign_test_is_the_exact_binomial(wins: int, losses: int, expected: float) -> None:
    """7 wins against 1 loss: P(at most 1 of 8 coin flips) is 9/256, doubled for two sides."""
    both_right = 90
    baseline = [1] * both_right + [0] * wins + [1] * losses
    candidate = [1] * both_right + [1] * wins + [0] * losses

    assert sign_test_p(baseline, candidate) == pytest.approx(expected)


def test_bootstrap_is_reproducible() -> None:
    baseline, candidate = simulate(np.random.default_rng(4), cases=100, runs=1, lift=0.3)

    assert bootstrap_diff_ci(baseline, candidate) == bootstrap_diff_ci(baseline, candidate)


def test_a_95_percent_interval_covers_the_truth_95_percent_of_the_time() -> None:
    rng = np.random.default_rng(5)
    lift, experiments = 0.3, 2000
    covered = 0
    for _ in range(experiments):
        estimate = paired_diff_ci(*simulate(rng, cases=200, runs=3, lift=lift))
        covered += estimate.low <= lift / 3 <= estimate.high

    assert 0.935 <= covered / experiments <= 0.965


def test_same_prompt_twice_is_called_different_about_5_percent_of_the_time() -> None:
    rng = np.random.default_rng(6)
    experiments = 2000
    false_alarms = sum(
        verdict(paired_diff_ci(*simulate(rng, cases=200, runs=1, lift=0.0))) != "inconclusive"
        for _ in range(experiments)
    )

    assert 0.035 <= false_alarms / experiments <= 0.065


def test_variance_components_recover_a_known_split() -> None:
    rng = np.random.default_rng(7)
    pass_rate = rng.beta(4, 2, size=20_000)
    scores = rng.random((len(pass_rate), 4)) < pass_rate[:, None]
    between_cases, between_runs = variance_components(scores)

    assert between_cases == pytest.approx(pass_rate.var(), rel=0.05)
    assert between_runs == pytest.approx((pass_rate * (1 - pass_rate)).mean(), rel=0.05)


def test_projected_margin_matches_the_measured_one_at_the_measured_size() -> None:
    baseline, candidate = simulate(np.random.default_rng(9), cases=400, runs=3, lift=0.3)
    between_cases, between_runs = variance_components(candidate.astype(float) - baseline)
    measured = paired_diff_ci(baseline, candidate).margin

    assert projected_margin(between_cases, between_runs, cases=400, runs=3) == pytest.approx(
        measured
    )
    # A new case averages down both kinds of noise, a rerun only one: cases win at equal cost.
    assert projected_margin(between_cases, between_runs, 1200, 1) < projected_margin(
        between_cases, between_runs, 400, 3
    )


def test_variance_components_need_repeated_runs() -> None:
    with pytest.raises(ValueError, match="two runs"):
        variance_components([1, 0, 1])


def test_required_cases_matches_the_textbook_formula() -> None:
    # ((1.959964 + 0.841621) * 0.3 / 0.05) ** 2 = 282.56
    assert required_cases(smallest_effect=0.05, sd_of_differences=0.3) == 283
    assert required_cases(0.05, 0.3, power=0.9) > 283
    assert required_cases(0.025, 0.3) == pytest.approx(4 * 283, abs=3)
    with pytest.raises(ValueError, match="effect of zero"):
        required_cases(0.0, 0.3)


def test_detectable_effect_is_the_inverse_of_required_cases() -> None:
    effect = detectable_effect(cases=283, sd_of_differences=0.3)

    assert effect == pytest.approx(0.05, abs=0.0005)
    assert required_cases(effect, 0.3) in (283, 284)
    assert detectable_effect(4 * 283, 0.3) == pytest.approx(effect / 2)


def test_required_cases_delivers_the_promised_power() -> None:
    rng = np.random.default_rng(8)
    lift, experiments = 0.3, 1000
    pilot_baseline, pilot_candidate = simulate(rng, cases=5000, runs=1, lift=lift)
    sd = float((pilot_candidate.astype(float) - pilot_baseline).std(ddof=1))
    cases = required_cases(smallest_effect=lift / 3, sd_of_differences=sd)

    detected = sum(
        verdict(paired_diff_ci(*simulate(rng, cases=cases, runs=1, lift=lift))) == "better"
        for _ in range(experiments)
    )

    assert 0.75 <= detected / experiments <= 0.85


@pytest.mark.parametrize(
    ("low", "high", "expected"),
    [(0.01, 0.07, "better"), (-0.07, -0.01, "worse"), (-0.02, 0.06, "inconclusive")],
)
def test_verdict_reads_the_interval(low: float, high: float, expected: str) -> None:
    assert verdict(Estimate((low + high) / 2, low, high, 0.015, 300)) == expected


def test_p_value_and_formatting() -> None:
    significant = Estimate(0.04, 0.04 - Z95 * 0.01, 0.04 + Z95 * 0.01, 0.01, 300)
    borderline = Estimate(Z95 * 0.01, 0.0, 2 * Z95 * 0.01, 0.01, 300)

    assert significant.p_value < 0.001
    assert borderline.p_value == pytest.approx(0.05, abs=1e-4)
    assert Estimate(0.0, 0.0, 0.0, 0.0, 10).p_value == 1.0
    assert significant.p_text == "p < 0.001"
    assert borderline.p_text == "p = 0.050"
    assert f"{significant:+.1%}" == "+4.0% (+2.0% to +6.0%)"
    assert f"{Estimate(0.86, 0.82, 0.90, 0.02, 300)}" == "86.0% (82.0% to 90.0%)"
