"""Command-line entry point for the task agent.

    python -m bodhan_agent --task "..." --files ./inputs --out ./out \
        [--max-steps 30] [--max-cost-inr 20]
"""

from __future__ import annotations

import argparse
import json
import sys

from .loop import run_task


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="bodhan_agent",
        description="Complete a plain-language Indian-language media task using Bodhan models.",
    )
    parser.add_argument("--task", required=True, help="The task, in plain language.")
    parser.add_argument("--files", required=True,
                        help="Input file or folder of input files.")
    parser.add_argument("--out", required=True, help="Output folder for this run.")
    parser.add_argument("--max-steps", type=int, default=30,
                        help="Maximum planning steps before stopping (default 30).")
    parser.add_argument("--max-cost-inr", type=float, default=20.0,
                        help="Maximum spend in rupees before stopping (default 20).")
    parser.add_argument("--call-timeout", type=float, default=180.0,
                        help="Per-LLM-call timeout in seconds (default 180).")
    args = parser.parse_args(argv)

    report = run_task(
        task=args.task,
        files_arg=args.files,
        out_dir=args.out,
        max_steps=args.max_steps,
        max_cost_inr=args.max_cost_inr,
        call_timeout=args.call_timeout,
    )

    print(json.dumps({
        "status": report["status"],
        "stop_reason": report["stop_reason"],
        "steps": report["steps"],
        "cost_inr": report["cost"]["total_inr"],
        "elapsed_seconds": report["elapsed_seconds"],
        "out": args.out,
    }, indent=2))

    return 0 if report["status"] == "completed" else 1


if __name__ == "__main__":
    sys.exit(main())
