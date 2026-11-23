"""Cost metering and budget enforcement.

Every paid call is priced before it is made. When a call would take the run past
its rupee budget, BudgetExceeded is raised *before* spending the money -- the
agent catches it, stops cleanly and reports what it managed to do.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from .config import (
    PRICE_OCR_PER_IMAGE,
    PRICE_SPEAK_PER_10K_INPUT_CHARS,
    PRICE_TRANSCRIBE_PER_AUDIO_MINUTE,
    PRICE_TRANSLATE_PER_10K_OUTPUT_TOKENS,
)


class BudgetExceeded(RuntimeError):
    """Raised when a call would push the run past its rupee budget."""

    def __init__(self, attempted_inr: float, spent_inr: float, budget_inr: float) -> None:
        super().__init__(
            f"Budget exhausted: spent Rs {spent_inr:.4f} of Rs {budget_inr:.2f}; "
            f"next call would cost Rs {attempted_inr:.4f}."
        )
        self.attempted_inr = attempted_inr
        self.spent_inr = spent_inr
        self.budget_inr = budget_inr


def price_transcribe(audio_seconds: float) -> float:
    return (audio_seconds / 60.0) * PRICE_TRANSCRIBE_PER_AUDIO_MINUTE


def price_translate(output_tokens: int) -> float:
    return (output_tokens / 10_000.0) * PRICE_TRANSLATE_PER_10K_OUTPUT_TOKENS


def price_speak(input_chars: int) -> float:
    return (input_chars / 10_000.0) * PRICE_SPEAK_PER_10K_INPUT_CHARS


def price_ocr(images: int) -> float:
    return images * PRICE_OCR_PER_IMAGE


def estimate_tokens(text: str) -> int:
    """Rough token estimate. Indic scripts run denser per character than English,
    so this deliberately over-estimates rather than under-charging the budget."""
    return max(1, math.ceil(len(text) / 3.0))


@dataclass
class LineItem:
    model: str
    units: float
    unit_name: str
    inr: float
    cached: bool = False


@dataclass
class CostMeter:
    budget_inr: float | None = None
    items: list[LineItem] = field(default_factory=list)

    @property
    def total_inr(self) -> float:
        return sum(i.inr for i in self.items)

    def check(self, attempted_inr: float) -> None:
        """Raise before spending if this call would break the budget."""
        if self.budget_inr is None:
            return
        if self.total_inr + attempted_inr > self.budget_inr:
            raise BudgetExceeded(attempted_inr, self.total_inr, self.budget_inr)

    def record(self, model: str, units: float, unit_name: str, inr: float,
               cached: bool = False) -> LineItem:
        item = LineItem(model=model, units=units, unit_name=unit_name,
                        inr=0.0 if cached else inr, cached=cached)
        self.items.append(item)
        return item

    def by_model(self) -> dict[str, dict[str, float]]:
        out: dict[str, dict[str, float]] = {}
        for i in self.items:
            row = out.setdefault(i.model, {"calls": 0, "cached_calls": 0, "units": 0.0, "inr": 0.0})
            row["calls"] += 1
            row["cached_calls"] += 1 if i.cached else 0
            row["units"] += i.units
            row["inr"] += i.inr
        return out

    def summary(self) -> dict:
        return {
            "total_inr": round(self.total_inr, 4),
            "budget_inr": self.budget_inr,
            "by_model": {k: {kk: round(vv, 4) for kk, vv in v.items()}
                         for k, v in self.by_model().items()},
        }


METER = CostMeter()
