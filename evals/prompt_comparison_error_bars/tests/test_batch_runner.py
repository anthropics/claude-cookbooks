"""The runner against a fake client: no network, no cost."""

import json
import re
from pathlib import Path
from types import SimpleNamespace

import pytest
from batch_runner import (
    build_requests,
    collect_batch,
    cost_usd,
    load_rows,
    run_now,
    save_rows,
    scores_by_prompt,
    submit_batch,
    wait_for_batch,
)
from refund_task import DECISION_SCHEMA, PROMPTS, decide, generate_cases, render_ticket

CASES = generate_cases(6, seed=1)
MODEL = "claude-haiku-5-5"


def message(decision: str | None, stop_reason: str = "end_turn") -> SimpleNamespace:
    """A Messages API response, reduced to the fields the runner reads."""
    text = json.dumps({"decision": decision}) if decision else '{"decision": "appr'
    return SimpleNamespace(
        stop_reason=stop_reason,
        content=[
            SimpleNamespace(type="thinking", thinking=""),
            SimpleNamespace(type="text", text=text),
        ],
        usage=SimpleNamespace(input_tokens=400, output_tokens=50),
    )


def entry(custom_id: str, kind: str, reply: SimpleNamespace | None = None) -> SimpleNamespace:
    return SimpleNamespace(custom_id=custom_id, result=SimpleNamespace(type=kind, message=reply))


class FakeClient:
    """Answers every request correctly unless `overrides` says otherwise for a custom_id."""

    def __init__(self, overrides: dict[str, SimpleNamespace] | None = None, polls: int = 2):
        self.overrides = overrides or {}
        self.polls_left = polls
        self.submitted: list[dict] = []
        self.answers = {case.case_id: decide(case) for case in CASES}
        self.messages = SimpleNamespace(
            create=self._create,
            batches=SimpleNamespace(
                create=self._batch_create, retrieve=self._retrieve, results=self._results
            ),
        )

    def _create(self, **params) -> SimpleNamespace:
        case_id = next(
            c.case_id for c in CASES if render_ticket(c) == params["messages"][0]["content"]
        )
        return message(self.answers[case_id])

    def _batch_create(self, requests: list[dict]) -> SimpleNamespace:
        self.submitted = requests
        return SimpleNamespace(id="msgbatch_test")

    def _retrieve(self, batch_id: str) -> SimpleNamespace:
        self.polls_left -= 1
        status = "ended" if self.polls_left <= 0 else "in_progress"
        counts = SimpleNamespace(processing=len(self.submitted), succeeded=0)
        return SimpleNamespace(id=batch_id, processing_status=status, request_counts=counts)

    def _results(self, batch_id: str):
        for request in reversed(self.submitted):  # results arrive in any order
            custom_id = request["custom_id"]
            if custom_id in self.overrides:
                yield self.overrides[custom_id]
            else:
                case_id = custom_id.split("__")[1]
                yield entry(custom_id, "succeeded", message(self.answers[case_id]))


def test_one_request_per_prompt_case_and_run() -> None:
    requests = build_requests(CASES, PROMPTS, runs=3, model=MODEL)
    ids = [request["custom_id"] for request in requests]

    assert len(requests) == len(PROMPTS) * len(CASES) * 3
    assert len(set(ids)) == len(ids)
    assert all(re.fullmatch(r"[a-zA-Z0-9_-]{1,64}", custom_id) for custom_id in ids)


def test_request_carries_the_prompt_the_ticket_and_the_schema() -> None:
    request = build_requests(CASES[:1], {"prose": PROMPTS["prose"]}, runs=1, model=MODEL)[0]
    params = request["params"]

    assert request["custom_id"] == f"prose__{CASES[0].case_id}__0"
    assert params["model"] == MODEL
    assert params["system"] == PROMPTS["prose"]
    assert params["messages"] == [{"role": "user", "content": render_ticket(CASES[0])}]
    assert params["output_config"] == {
        "effort": "low",
        "format": {"type": "json_schema", "schema": DECISION_SCHEMA},
    }


def test_batch_round_trip_scores_every_attempt() -> None:
    client = FakeClient()
    requests = build_requests(CASES, PROMPTS, runs=2, model=MODEL)

    batch_id = submit_batch(client, requests)
    wait_for_batch(client, batch_id, poll_seconds=0)
    rows = collect_batch(client, batch_id)
    scores, left_out = scores_by_prompt(rows, CASES)

    assert left_out == []
    assert set(scores) == set(PROMPTS)
    for matrix in scores.values():
        assert matrix.shape == (len(CASES), 2)
        assert matrix.min() == 1.0  # the fake client answers correctly


def test_cut_off_and_refused_answers_count_as_wrong() -> None:
    target, other = CASES[0].case_id, CASES[1].case_id
    client = FakeClient(
        {
            f"prose__{target}__0": entry(
                f"prose__{target}__0", "succeeded", message(None, "max_tokens")
            ),
            f"prose__{other}__0": entry(
                f"prose__{other}__0", "succeeded", message(None, "refusal")
            ),
        }
    )
    submit_batch(client, build_requests(CASES, PROMPTS, runs=1, model=MODEL))
    rows = collect_batch(client, "msgbatch_test")
    scores, left_out = scores_by_prompt(rows, CASES)

    assert left_out == []
    assert scores["prose"][:2, 0].tolist() == [0.0, 0.0]
    assert scores["procedure"][:2, 0].tolist() == [1.0, 1.0]
    cut_off = next(r for r in rows if r["prompt"] == "prose" and r["case_id"] == target)
    assert cut_off["decision"] is None and cut_off["outcome"] == "max_tokens"


@pytest.mark.parametrize(
    "content",
    [
        [],  # no text block at all
        [SimpleNamespace(type="text", text="approve")],  # not JSON
        [SimpleNamespace(type="text", text='["approve"]')],  # JSON, but not the object asked for
        [SimpleNamespace(type="text", text='{"verdict": "approve"}')],  # no decision key
    ],
)
def test_a_malformed_answer_counts_as_wrong_and_does_not_stop_collection(content: list) -> None:
    custom_id = f"prose__{CASES[0].case_id}__0"
    reply = message("approve")
    reply.content = content
    client = FakeClient({custom_id: entry(custom_id, "succeeded", reply)})
    submit_batch(client, build_requests(CASES, PROMPTS, runs=1, model=MODEL))
    rows = collect_batch(client, "msgbatch_test")
    scores, left_out = scores_by_prompt(rows, CASES)

    assert len(rows) == len(PROMPTS) * len(CASES) and left_out == []
    assert scores["prose"][0, 0] == 0.0
    malformed = next(r for r in rows if r["prompt"] == "prose" and r["case_id"] == CASES[0].case_id)
    assert malformed["decision"] is None and malformed["outcome"] == "end_turn"


def test_scoring_refuses_duplicate_or_unrelated_rows() -> None:
    client = FakeClient()
    submit_batch(client, build_requests(CASES, PROMPTS, runs=1, model=MODEL))
    rows = collect_batch(client, "msgbatch_test")

    with pytest.raises(ValueError, match="two rows for"):
        scores_by_prompt(rows + rows[:1], CASES)
    with pytest.raises(ValueError, match="none of the rows"):
        scores_by_prompt(rows, generate_cases(3, seed=99)[:0])


@pytest.mark.parametrize("kind", ["errored", "expired", "canceled"])
def test_a_case_the_api_never_answered_is_left_out_of_both_prompts(kind: str) -> None:
    target = CASES[2].case_id
    client = FakeClient({f"procedure__{target}__1": entry(f"procedure__{target}__1", kind)})
    submit_batch(client, build_requests(CASES, PROMPTS, runs=2, model=MODEL))
    scores, left_out = scores_by_prompt(collect_batch(client, "msgbatch_test"), CASES)

    assert left_out == [target]
    assert scores["prose"].shape == scores["procedure"].shape == (len(CASES) - 1, 2)


def test_wrong_answers_score_zero_in_case_order() -> None:
    wrong = next(d for d in ("approve", "deny") if d != decide(CASES[3]))
    custom_id = f"prose__{CASES[3].case_id}__0"
    client = FakeClient({custom_id: entry(custom_id, "succeeded", message(wrong))})
    submit_batch(client, build_requests(CASES, PROMPTS, runs=1, model=MODEL))
    scores, _ = scores_by_prompt(collect_batch(client, "msgbatch_test"), CASES)

    assert scores["prose"][:, 0].tolist() == [1.0, 1.0, 1.0, 0.0, 1.0, 1.0]


def test_run_now_returns_the_same_rows_as_a_batch() -> None:
    requests = build_requests(CASES, PROMPTS, runs=1, model=MODEL)
    client = FakeClient()
    submit_batch(client, requests)

    def key(row: dict) -> tuple:
        return row["prompt"], row["case_id"], row["run"]

    direct = sorted(run_now(client, requests, workers=2), key=key)
    batched = sorted(collect_batch(client, "msgbatch_test"), key=key)
    assert direct == batched


def test_cost_uses_token_counts_and_the_batch_discount() -> None:
    rows = [{"input_tokens": 1_000_000, "output_tokens": 200_000}] * 2

    assert cost_usd(rows, input_per_mtok=0.10, output_per_mtok=0.50, batch=False) == pytest.approx(
        0.40
    )
    assert cost_usd(rows, input_per_mtok=0.10, output_per_mtok=0.50) == pytest.approx(0.20)


def test_rows_round_trip_in_a_stable_order(tmp_path: Path) -> None:
    client = FakeClient()
    submit_batch(client, build_requests(CASES, PROMPTS, runs=2, model=MODEL))
    rows = collect_batch(client, "msgbatch_test")
    path = tmp_path / "rows.jsonl"
    save_rows(rows, path)
    loaded = load_rows(path)

    assert sorted(loaded, key=json.dumps) == sorted(rows, key=json.dumps)
    assert loaded == sorted(loaded, key=lambda r: (r["prompt"], r["case_id"], r["run"]))
