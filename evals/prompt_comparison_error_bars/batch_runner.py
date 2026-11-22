"""Run the eval: one request per (prompt, case, run), sent to Claude, read back as rows.

The full eval goes through the Message Batches API, which is asynchronous and half the
price: `submit_batch`, `wait_for_batch`, `collect_batch`. `run_now` sends the same requests
directly for a quick look at a handful of cases. Both produce the same rows, one per
attempt, and `scores_by_prompt` turns rows into the arrays that `error_bars` works on.
"""

import json
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import anthropic
import numpy as np
from anthropic.types import Message
from refund_task import DECISION_SCHEMA, Case, decide, render_ticket

SEPARATOR = "__"  # custom_id allows only letters, digits, "-" and "_"
NO_RESPONSE = ("errored", "expired", "canceled")  # batch outcomes that carry no message


def build_requests(
    cases: list[Case],
    prompts: dict[str, str],
    runs: int,
    model: str,
    effort: str = "low",
    max_tokens: int = 4096,
) -> list[dict]:
    """Every prompt on every case, `runs` times. The `custom_id` says which attempt it is."""
    return [
        {
            "custom_id": SEPARATOR.join([name, case.case_id, str(run)]),
            "params": {
                "model": model,
                "max_tokens": max_tokens,
                "system": system_prompt,
                "messages": [{"role": "user", "content": render_ticket(case)}],
                "output_config": {
                    "effort": effort,
                    "format": {"type": "json_schema", "schema": DECISION_SCHEMA},
                },
            },
        }
        for name, system_prompt in prompts.items()
        for case in cases
        for run in range(runs)
    ]


def _decision(message: Message) -> str | None:
    """The answer in a response, or None when it holds no usable one."""
    if message.stop_reason != "end_turn":
        return None  # cut off or refused: structured outputs promise valid JSON only on a normal finish
    text = next((block.text for block in message.content if block.type == "text"), "")
    try:
        return json.loads(text).get("decision")
    except (json.JSONDecodeError, AttributeError):
        return None  # one malformed answer must not sink a 3,600-request collection


def _row(custom_id: str, outcome: str, message: Message | None = None) -> dict:
    """One attempt. `decision` is None when the model gave no usable answer."""
    prompt, case_id, run = custom_id.split(SEPARATOR)
    return {
        "prompt": prompt,
        "case_id": case_id,
        "run": int(run),
        "decision": _decision(message) if message else None,
        "outcome": outcome if message is None else message.stop_reason,
        "input_tokens": message.usage.input_tokens if message else 0,
        "output_tokens": message.usage.output_tokens if message else 0,
    }


def submit_batch(client: anthropic.Anthropic, requests: list[dict]) -> str:
    """Send the requests as one batch and return its id. Keep the id: results last 29 days."""
    return client.messages.batches.create(requests=requests).id


def wait_for_batch(client: anthropic.Anthropic, batch_id: str, poll_seconds: float = 30) -> None:
    """Block until the batch has ended. Most batches finish within an hour."""
    while True:
        batch = client.messages.batches.retrieve(batch_id)
        if batch.processing_status == "ended":
            return
        counts = batch.request_counts
        print(f"{batch_id}: {counts.processing} processing, {counts.succeeded} done")
        time.sleep(poll_seconds)


def collect_batch(client: anthropic.Anthropic, batch_id: str) -> list[dict]:
    """Rows for an ended batch. Results come back in any order, so the id carries the key."""
    rows = []
    for entry in client.messages.batches.results(batch_id):
        result = entry.result
        message = result.message if result.type == "succeeded" else None
        rows.append(_row(entry.custom_id, result.type, message))
    return rows


def run_now(client: anthropic.Anthropic, requests: list[dict], workers: int = 8) -> list[dict]:
    """The same requests through the regular Messages API: full price, answers in seconds."""

    def attempt(request: dict) -> dict:
        message = client.messages.create(**request["params"])
        return _row(request["custom_id"], "succeeded", message)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(attempt, requests))


def scores_by_prompt(
    rows: list[dict], cases: list[Case]
) -> tuple[dict[str, np.ndarray], list[str]]:
    """Grade the rows: a `(cases, runs)` array of 0/1 per prompt, cases in the order given.

    An attempt with no usable answer (cut off, refused) scores 0, as it would in production.
    An attempt the API never answered says nothing about the prompt, so its case is left out
    of every prompt's array to keep the comparison paired. Returns the arrays and the ids of
    the cases left out.
    """
    expected = {case.case_id: decide(case) for case in cases}
    attempts: dict[str, dict[str, dict[int, float]]] = {}
    unanswered = set()
    for row in rows:
        if row["case_id"] not in expected:
            continue
        if row["outcome"] in NO_RESPONSE:
            unanswered.add(row["case_id"])
        by_run = attempts.setdefault(row["prompt"], {}).setdefault(row["case_id"], {})
        if row["run"] in by_run:
            raise ValueError(f"two rows for {row['prompt']}, {row['case_id']}, run {row['run']}")
        by_run[row["run"]] = float(row["decision"] == expected[row["case_id"]])
    if not attempts:
        raise ValueError("none of the rows belong to these cases")

    runs = max(len(by_run) for by_case in attempts.values() for by_run in by_case.values())
    complete = [
        case.case_id
        for case in cases
        if case.case_id not in unanswered
        and all(len(by_case.get(case.case_id, {})) == runs for by_case in attempts.values())
    ]
    scores = {
        prompt: np.array(
            [[by_case[case_id][run] for run in sorted(by_case[case_id])] for case_id in complete]
        )
        for prompt, by_case in attempts.items()
    }
    return scores, [case.case_id for case in cases if case.case_id not in complete]


def cost_usd(
    rows: list[dict], input_per_mtok: float, output_per_mtok: float, batch: bool = True
) -> float:
    """What the rows cost at the given prices per million tokens. Batches are half price."""
    tokens_in = sum(row["input_tokens"] for row in rows)
    tokens_out = sum(row["output_tokens"] for row in rows)
    full_price = (tokens_in * input_per_mtok + tokens_out * output_per_mtok) / 1_000_000
    return full_price / 2 if batch else full_price


def save_rows(rows: list[dict], path: Path) -> None:
    """One JSON object per line, in a stable order so reruns diff cleanly."""
    ordered = sorted(rows, key=lambda row: (row["prompt"], row["case_id"], row["run"]))
    path.write_text("".join(json.dumps(row) + "\n" for row in ordered))


def load_rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines()]
