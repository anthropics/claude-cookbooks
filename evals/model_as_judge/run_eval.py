#!/usr/bin/env python3
"""CI entry point for the model-as-judge evaluation gate.

Loads the golden dataset, runs the current production prompt through the judge,
compares against the committed baseline, and exits 0 (ship it) or 1 (blocked).
Wire this into CI so a prompt or model change cannot merge if it regresses
quality past the thresholds in ``utils/evaluator.DEFAULT_THRESHOLDS``.

Usage:
    python run_eval.py                 # full golden set, production prompt
    python run_eval.py --sample 8      # quick stratified subset (2 per category)

The system prompt under test comes from ``prompts.PROD_SYSTEM_PROMPT``. For
testing a candidate change without editing that file, set the environment
variable ``EVAL_SYSTEM_PROMPT`` to override it.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from pathlib import Path

import anthropic

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

from prompts import PROD_SYSTEM_PROMPT  # noqa: E402
from utils.evaluator import (  # noqa: E402
    DEFAULT_THRESHOLDS,
    DOCUMENTS,
    EvalResult,
    aggregate,
    check_regression_gate,
    run_suite,
)


def build_answer_fn(client: anthropic.Anthropic, model: str, system_prompt: str):
    """The system under test: answer one golden record from its source document."""

    def answer_fn(record: dict) -> str:
        response = client.messages.create(
            model=model,
            max_tokens=400,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"<document>\n{DOCUMENTS[record['document']]}\n</document>\n\n"
                        f"{record['question']}"
                    ),
                }
            ],
        )
        return "".join(block.text for block in response.content if block.type == "text")

    return answer_fn


def stratified_head(dataset: list[dict], n: int) -> list[dict]:
    """Take roughly n items, evenly across categories, so a subset still spans them."""
    if n <= 0 or n >= len(dataset):
        return dataset
    categories = sorted({r["category"] for r in dataset})
    per_cat = max(1, math.ceil(n / len(categories)))
    picked: list[dict] = []
    for cat in categories:
        picked.extend([r for r in dataset if r["category"] == cat][:per_cat])
    return picked[:n] if n < len(picked) else picked


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="claude-haiku-4-5", help="system-under-test model")
    parser.add_argument("--judge-model", default="claude-haiku-4-5", help="judge model")
    parser.add_argument(
        "--sample", type=int, default=0, help="limit to N stratified questions (0 = all)"
    )
    args = parser.parse_args()

    golden = json.loads((HERE / "golden_dataset.json").read_text())
    golden = stratified_head(golden, args.sample)
    sampled_ids = {q["id"] for q in golden}

    baseline_raw = json.loads((HERE / "baseline_results.json").read_text())
    baseline = [EvalResult.from_dict(d) for d in baseline_raw if d["question_id"] in sampled_ids]

    system_prompt = os.environ.get("EVAL_SYSTEM_PROMPT", PROD_SYSTEM_PROMPT)

    client = anthropic.Anthropic(max_retries=8)
    answer_fn = build_answer_fn(client, args.model, system_prompt)

    print(f"Running eval on {len(golden)} golden question(s) with model={args.model}...")
    current = run_suite(client, args.judge_model, answer_fn, golden)

    gate = check_regression_gate(baseline, current, DEFAULT_THRESHOLDS)
    agg = aggregate(current)
    print(f"\noverall score: {agg['overall']:.2f}/5.00  (n={agg['n']})")
    print(gate.summary())

    sys.exit(0 if gate.passed else 1)


if __name__ == "__main__":
    main()
