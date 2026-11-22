"""The gate's exit code is the contract a CI job relies on."""

import importlib.util
from pathlib import Path

import numpy as np
import pytest
from batch_runner import save_rows
from refund_task import decide, load_cases

RECIPE = Path(__file__).resolve().parent.parent
CASES = load_cases(RECIPE / "data" / "cases.jsonl")
COMPARE = ["--baseline", "prose", "--candidate", "procedure"]

spec = importlib.util.spec_from_file_location("run_eval", RECIPE / "evaluation" / "run_eval.py")
run_eval = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run_eval)


def recorded(tmp_path: Path, accuracy: dict[str, float], seed: int = 0) -> Path:
    """Results where each prompt answers correctly with the given probability.

    Both prompts draw on the same per-case luck, so a higher accuracy passes a superset of
    the cases, the way a real improvement mostly does.
    """
    luck = np.random.default_rng(seed).random(len(CASES))
    rows = []
    for prompt, rate in accuracy.items():
        for case, draw in zip(CASES, luck, strict=True):
            correct = decide(case)
            wrong = next(d for d in ("approve", "deny") if d != correct)
            rows.append(
                {
                    "prompt": prompt,
                    "case_id": case.case_id,
                    "run": 0,
                    "decision": correct if draw < rate else wrong,
                    "outcome": "end_turn",
                    "input_tokens": 400,
                    "output_tokens": 50,
                }
            )
    path = tmp_path / "results.jsonl"
    save_rows(rows, path)
    return path


@pytest.mark.parametrize(
    ("accuracy", "require", "exit_code", "verdict"),
    [
        ({"prose": 0.80, "procedure": 0.90}, "better", 0, "better"),
        ({"prose": 0.90, "procedure": 0.80}, "better", 1, "worse"),
        ({"prose": 0.90, "procedure": 0.80}, "not-worse", 1, "worse"),
        ({"prose": 0.85, "procedure": 0.85}, "better", 1, "inconclusive"),
        ({"prose": 0.85, "procedure": 0.85}, "not-worse", 0, "inconclusive"),
        # A real but small drop: measurably worse, and still inside the 2-point margin.
        ({"prose": 0.90, "procedure": 0.895}, "not-worse", 0, "worse"),
        ({"prose": 0.90, "procedure": 0.86}, "not-worse", 1, "worse"),
    ],
)
def test_exit_code_follows_the_verdict(
    tmp_path: Path, capsys, accuracy: dict, require: str, exit_code: int, verdict: str
) -> None:
    results = recorded(tmp_path, accuracy)

    assert run_eval.main([*COMPARE, "--results", str(results), "--require", require]) == exit_code
    assert f"procedure is {verdict}" in capsys.readouterr().out


def test_an_inconclusive_result_says_how_many_cases_would_settle_it(tmp_path: Path, capsys) -> None:
    results = recorded(tmp_path, {"prose": 0.85, "procedure": 0.86})

    assert run_eval.main([*COMPARE, "--results", str(results)]) == 1
    assert "would take about" in capsys.readouterr().out

    assert run_eval.main([*COMPARE, "--results", str(results), "--require", "not-worse"]) == 0
    assert "would take about" not in capsys.readouterr().out  # a different question there


def test_not_worse_fails_when_the_eval_is_too_small_to_rule_out_a_drop(tmp_path: Path) -> None:
    """Unrelated noise on 600 cases leaves an interval wider than a 1-point margin."""
    rows = [
        {
            "prompt": prompt,
            "case_id": case.case_id,
            "run": 0,
            "decision": decide(case) if draw < 0.85 else "wrong",
            "outcome": "end_turn",
            "input_tokens": 400,
            "output_tokens": 50,
        }
        for prompt, seed in (("prose", 1), ("procedure", 2))
        for case, draw in zip(CASES, np.random.default_rng(seed).random(len(CASES)), strict=True)
    ]
    path = tmp_path / "results.jsonl"
    save_rows(rows, path)

    arguments = [*COMPARE, "--results", str(path), "--require", "not-worse"]
    assert run_eval.main([*arguments, "--margin", "0.01"]) == 1
    assert run_eval.main([*arguments, "--margin", "0.2"]) == 0


def test_a_rerun_never_writes_over_the_recorded_results() -> None:
    assert run_eval.RERUN != run_eval.RECORDED and run_eval.RERUN.name == "rerun.jsonl"
