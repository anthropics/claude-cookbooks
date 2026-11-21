# Recorded results

`main.jsonl` is one full run of the eval: 600 cases, three prompts, three runs each, 5,400
requests to `claude-haiku-5-5` at `effort: "low"`, sent as a single batch through the
Message Batches API on 21 November 2026. The notebook and `evaluation/run_eval.py` read
it, so the analysis reproduces without rerunning the eval.

Each line is one attempt:

| Field | Meaning |
|---|---|
| `prompt` | `draft`, `prose`, or `procedure`, a key of `refund_task.PROMPTS` |
| `case_id` | The case in `data/cases.jsonl` |
| `run` | 0, 1, or 2 |
| `decision` | The model's answer, or `null` when it gave no usable answer |
| `outcome` | The response's `stop_reason`, or the batch result type (`errored`, `expired`, `canceled`) when there was no response |
| `input_tokens`, `output_tokens` | Usage for the attempt |

The file holds answers only. `batch_runner.scores_by_prompt` grades them against the
policy code at read time, so a change to the policy shows up as a change in the scores.

## Exclusion rules

- An attempt with a response but no usable answer (cut off at `max_tokens`, refused, or
  not the JSON asked for) scores 0. A production system would have failed on it too.
- An attempt the API never answered says nothing about any prompt. Its case is left out
  of every prompt's scores, so the comparisons stay paired.

In this run all 5,400 attempts finished with `end_turn`, and no case was left out.

## Cost

5,095,530 input tokens and 1,267,231 output tokens. The regular price for
`claude-haiku-5-5` is $0.10 per million input tokens and $0.50 per million output tokens,
and the Batches API charges half of that: $0.57 for this run.
