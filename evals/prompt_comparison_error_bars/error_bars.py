"""Error bars for evals: how sure can you be about a score, and about a difference?

Scores are arrays of 0/1 (or any per-attempt score) shaped `(cases,)` or `(cases, runs)`.
The case is the unit of analysis. Repeated runs of one case are averaged first, because
they tell you more about that case and nothing about cases you did not sample.

The methods follow Evan Miller, "Adding Error Bars to Evals: A Statistical Approach to
Language Model Evaluations" (2024), https://arxiv.org/abs/2411.00640.
"""

from dataclasses import dataclass
from math import ceil, comb, hypot, sqrt
from statistics import NormalDist

import numpy as np
from numpy.typing import ArrayLike, NDArray

_NORMAL = NormalDist()


@dataclass(frozen=True)
class Estimate:
    """A number with its uncertainty."""

    value: float
    low: float
    high: float
    standard_error: float
    cases: int

    @property
    def margin(self) -> float:
        """Half the width of the interval: the "plus or minus"."""
        return (self.high - self.low) / 2

    @property
    def p_value(self) -> float:
        """Two-sided p-value for "the true value is zero". Meaningful for differences."""
        if self.standard_error == 0:
            return 1.0 if self.value == 0 else 0.0
        return 2 * (1 - _NORMAL.cdf(abs(self.value) / self.standard_error))

    @property
    def p_text(self) -> str:
        return p_text(self.p_value)

    def __format__(self, spec: str) -> str:
        """`f"{estimate:.1%}"` formats the value and both ends of the interval the same way."""
        spec = spec or ".1%"
        return f"{self.value:{spec}} ({self.low:{spec}} to {self.high:{spec}})"


def p_text(p_value: float) -> str:
    """A p-value for printing: three decimals, and "p < 0.001" below that."""
    return "p < 0.001" if p_value < 0.001 else f"p = {p_value:.3f}"


def per_case(scores: ArrayLike) -> NDArray[np.float64]:
    """One number per case: the score itself, or the mean over that case's runs."""
    array = np.asarray(scores, dtype=float)
    return array if array.ndim == 1 else array.mean(axis=1)


def estimate_mean(values: NDArray[np.float64], confidence: float = 0.95) -> Estimate:
    """The mean of one number per case, with an interval from the central limit theorem:
    the standard error is the spread between cases divided by the square root of their count."""
    if len(values) < 2:
        raise ValueError("an interval needs at least two cases")
    mean = float(values.mean())
    standard_error = float(values.std(ddof=1)) / sqrt(len(values))
    half_width = _NORMAL.inv_cdf(0.5 + confidence / 2) * standard_error
    return Estimate(mean, mean - half_width, mean + half_width, standard_error, len(values))


def mean_ci(scores: ArrayLike, confidence: float = 0.95) -> Estimate:
    """The eval score with its confidence interval. Runs are averaged per case first."""
    return estimate_mean(per_case(scores), confidence)


def paired_diff_ci(baseline: ArrayLike, candidate: ArrayLike, confidence: float = 0.95) -> Estimate:
    """Candidate minus baseline, measured on the same cases.

    Each case contributes one difference, so difficulty that both prompts share cancels.
    How much tighter this is than comparing two separate scores depends on how often the
    prompts pass and fail the same cases, which is something to measure, not assume.
    """
    before, after = per_case(baseline), per_case(candidate)
    if before.shape != after.shape:
        raise ValueError("a paired comparison needs the same cases in the same order")
    return estimate_mean(after - before, confidence)


def unpaired_diff_ci(
    baseline: ArrayLike, candidate: ArrayLike, confidence: float = 0.95
) -> Estimate:
    """Candidate minus baseline as if the two scores came from different cases.

    This is what comparing two reported scores amounts to. It is here for contrast.
    """
    before, after = mean_ci(baseline), mean_ci(candidate)
    difference = after.value - before.value
    standard_error = hypot(before.standard_error, after.standard_error)
    half_width = _NORMAL.inv_cdf(0.5 + confidence / 2) * standard_error
    return Estimate(
        difference,
        difference - half_width,
        difference + half_width,
        standard_error,
        min(before.cases, after.cases),
    )


def bootstrap_diff_ci(
    baseline: ArrayLike,
    candidate: ArrayLike,
    confidence: float = 0.95,
    resamples: int = 10_000,
    seed: int = 0,
) -> Estimate:
    """The paired difference again, by resampling cases instead of trusting a formula.

    The interval is the percentile interval of the resampled means. `standard_error` is their
    spread, so `p_value` on the result is still a normal approximation.
    """
    differences = per_case(candidate) - per_case(baseline)
    rng = np.random.default_rng(seed)
    means = np.concatenate(
        [  # in chunks, so memory stays flat however many cases there are
            differences[rng.integers(0, len(differences), size=(chunk, len(differences)))].mean(
                axis=1
            )
            for chunk in [1000] * (resamples // 1000) + [resamples % 1000]
            if chunk
        ]
    )
    low, high = np.quantile(means, [(1 - confidence) / 2, (1 + confidence) / 2])
    return Estimate(
        float(differences.mean()),
        float(low),
        float(high),
        float(means.std(ddof=1)),
        len(differences),
    )


def sign_test_p(baseline: ArrayLike, candidate: ArrayLike) -> float:
    """Exact two-sided p-value for "neither prompt is better", from the cases they split on.

    Only cases where one prompt beat the other carry evidence. If the prompts were equally
    good on every case, each such case would be a coin flip, so the count of wins is
    binomial and needs no approximation. Read it next to the interval when only a handful
    of cases differ.

    It asks a slightly different question from the interval: how many cases moved each way,
    not by how much the average moved. It is also on the cautious side, as exact tests are.
    So the two can disagree near the 0.05 line.
    """
    before, after = per_case(baseline), per_case(candidate)
    wins, losses = int((after > before).sum()), int((after < before).sum())
    split = wins + losses
    if split == 0:
        return 1.0
    one_tail = sum(comb(split, k) for k in range(min(wins, losses) + 1)) / 2**split
    return min(1.0, 2 * one_tail)


def variance_components(scores: ArrayLike) -> tuple[float, float]:
    """Split the spread of `(cases, runs)` scores into (between cases, between runs).

    The variance of the eval score is `(between_cases + between_runs / runs) / cases`, so
    the two numbers say what another case buys you and what another run buys you. This
    assumes the runs of a case are interchangeable: run 2 is not systematically different
    from run 1.
    """
    array = np.asarray(scores, dtype=float)
    if array.ndim != 2 or array.shape[1] < 2:
        raise ValueError("splitting the variance needs at least two runs per case")
    between_runs = float(array.var(axis=1, ddof=1).mean())
    case_means_variance = float(array.mean(axis=1).var(ddof=1))
    between_cases = max(case_means_variance - between_runs / array.shape[1], 0.0)
    return between_cases, between_runs


def projected_margin(
    between_cases: float, between_runs: float, cases: int, runs: int, confidence: float = 0.95
) -> float:
    """The plus-or-minus an eval of `cases` x `runs` would have, given `variance_components`."""
    half_width = _NORMAL.inv_cdf(0.5 + confidence / 2)
    return half_width * sqrt((between_cases + between_runs / runs) / cases)


def required_cases(
    smallest_effect: float,
    sd_of_differences: float,
    power: float = 0.8,
    confidence: float = 0.95,
) -> int:
    """Cases needed for a paired comparison to detect `smallest_effect` with the given power."""
    if smallest_effect == 0:
        raise ValueError("no number of cases can detect an effect of zero")
    z_total = _NORMAL.inv_cdf(0.5 + confidence / 2) + _NORMAL.inv_cdf(power)
    return ceil((z_total * sd_of_differences / smallest_effect) ** 2)


def detectable_effect(
    cases: int, sd_of_differences: float, power: float = 0.8, confidence: float = 0.95
) -> float:
    """The smallest effect a paired comparison of this many cases detects with the given power."""
    z_total = _NORMAL.inv_cdf(0.5 + confidence / 2) + _NORMAL.inv_cdf(power)
    return z_total * sd_of_differences / sqrt(cases)


def verdict(difference: Estimate) -> str:
    """Read a difference interval: "better", "worse", or "inconclusive" when it spans zero."""
    if difference.low > 0:
        return "better"
    if difference.high < 0:
        return "worse"
    return "inconclusive"
