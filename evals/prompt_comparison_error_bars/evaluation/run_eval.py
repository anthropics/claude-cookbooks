"""A release gate for a prompt change: exit 0 only when the evidence supports shipping.

    python evaluation/run_eval.py                        # draft -> prose, on the recorded results
    python evaluation/run_eval.py --baseline prose --candidate procedure
    python evaluation/run_eval.py --require not-worse    # rule out a drop beyond the margin
    python evaluation/run_eval.py --run 3                # run the eval now (3 runs), then gate

Two gates. `better` passes when the whole interval of the difference is above zero.
`not-worse` is for changes that are not meant to improve quality: it passes when the
interval rules out a drop larger than `--margin`. That is a non-inferiority check, so a
small but real drop inside the margin passes. Choose the margin before looking at results;
the default of 2 points is only a placeholder. An interval that is merely too wide to tell
fails both, because "we could not measure a regression" is not "there is none".

Run it from the recipe folder. `--run` calls the Message Batches API, needs
ANTHROPIC_API_KEY, and writes to results/rerun.jsonl so the recorded run stays as it is.
"""

import argparse
import sys
from pathlib import Path

RECIPE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RECIPE))

from batch_runner import (  # noqa: E402
    build_requests,
    collect_batch,
    load_rows,
    save_rows,
    scores_by_prompt,
    submit_batch,
    wait_for_batch,
)
from error_bars import mean_ci, paired_diff_ci, required_cases, verdict  # noqa: E402
from refund_task import PROMPTS, load_cases  # noqa: E402

RECORDED = RECIPE / "results" / "main.jsonl"
RERUN = RECIPE / "results" / "rerun.jsonl"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--cases", type=Path, default=RECIPE / "data" / "cases.jsonl")
    parser.add_argument("--results", type=Path, help="results file to read, or to write with --run")
    parser.add_argument("--baseline", default="draft", choices=PROMPTS)
    parser.add_argument("--candidate", default="prose", choices=PROMPTS)
    parser.add_argument("--require", default="better", choices=["better", "not-worse"])
    parser.add_argument(
        "--margin", type=float, default=0.02, help="largest drop `not-worse` tolerates"
    )
    parser.add_argument("--run", type=int, metavar="RUNS", help="run the eval before gating")
    parser.add_argument("--model", default="claude-haiku-5-5")
    args = parser.parse_args(argv)
    results = args.results or (RERUN if args.run else RECORDED)

    cases = load_cases(args.cases)
    if args.run:
        import anthropic
        from dotenv import load_dotenv

        load_dotenv()
        client = anthropic.Anthropic()
        batch_id = submit_batch(client, build_requests(cases, PROMPTS, args.run, args.model))
        print(f"submitted {batch_id}", flush=True)
        wait_for_batch(client, batch_id)
        results.parent.mkdir(parents=True, exist_ok=True)
        save_rows(collect_batch(client, batch_id), results)

    scores, left_out = scores_by_prompt(load_rows(results), cases)
    baseline, candidate = scores[args.baseline], scores[args.candidate]
    difference = paired_diff_ci(baseline, candidate)
    outcome = verdict(difference)

    print(f"cases: {difference.cases} ({len(left_out)} left out), runs: {baseline.shape[1]}")
    print(f"{args.baseline:>10}: {mean_ci(baseline)}")
    print(f"{args.candidate:>10}: {mean_ci(candidate)}")
    print(f"difference: {difference:+.1%}, {difference.p_text}")
    print(f"verdict: {args.candidate} is {outcome}")
    if args.require == "better":
        passed = difference.low > 0
        if outcome == "inconclusive" and difference.value != 0:
            sd = difference.standard_error * difference.cases**0.5
            needed = required_cases(abs(difference.value), sd)
            print(
                f"if the true difference were the {difference.value:+.1%} seen here, confirming "
                f"it would take about {needed:,} cases (a rough guide: that figure is itself noisy)"
            )
    else:
        passed = difference.low > -args.margin
        print(f"largest drop the interval allows: {min(difference.low, 0):+.1%}")
    print("gate:", "pass" if passed else "fail")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
