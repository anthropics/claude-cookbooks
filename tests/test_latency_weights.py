import json
from dataclasses import dataclass
from types import SimpleNamespace

import numpy as np
import pytest

from latency_optimization.latency_stats import Sweep, rank_row


@dataclass(frozen=True)
class Config:
    name = "baseline"
    order = 0

    def dollars(self, row):
        return 0.0


@pytest.mark.parametrize("shared_names", [False, True])
def test_jobs_keep_their_weights_when_difficulty_names_overlap(tmp_path, shared_names):
    # Letters have one level, quotes have two. Each job should contribute half the weight.
    samples = [
        ("letter", "easy", True, 1),
        ("letter", "easy", True, 1),
        ("quote", "easy", False, 5),
        ("quote", "hard", False, 9),
    ]
    rows = [
        {
            "task": str(i),
            "cluster": str(i),
            "round": 1,
            "type": kind,
            "level": level if shared_names else f"{kind}-{level}",
            "correct": correct,
            "secs": secs,
            "call_secs": [secs],
        }
        for i, (kind, level, correct, secs) in enumerate(samples)
    ]
    log = tmp_path / "sweep.jsonl"
    log.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    sweep = Sweep(log, Config, draws=4)
    cfg = Config()
    np.testing.assert_allclose(sweep.stat(cfg, "correct"), 0.5)
    np.testing.assert_allclose(sweep.stat(cfg, "p50"), 1.0)
    row = rank_row(sweep, cfg, SimpleNamespace(metric="p50"))
    assert row["correct (hardest level)"] == "50.0% (50.0%)"
