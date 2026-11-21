# Is the new prompt actually better? Evals with error bars

Decide whether a prompt change helped, with a confidence interval instead of two bare scores.

## The problem

You change a prompt, rerun your eval, and the score moves a few points. That number alone
cannot tell you whether the new prompt is better. An eval is a sample of cases, so a
different sample would score differently. And the model's answers vary between runs:
Claude Haiku 5.5 rejects a `temperature` setting, so a run cannot be pinned down and
repeated. Comparing two bare scores ships changes that did nothing and discards changes
that worked.

## What this cookbook does

It builds four small tools and uses them on a worked example, a refund desk and two
changes to its system prompt:

- **An interval on a score**, so you know how far to trust it at your eval's size.
- **An interval on the difference** between two prompts run on the same cases, read as
  better, worse, or not yet known.
- **A split of the noise** into the part between runs and the part between cases, which
  tells you whether more runs or more cases is the better buy.
- **A sample-size calculation and a release gate**, with the full eval run at half price
  through the Message Batches API.

Start with **[guide.ipynb](guide.ipynb)**. It is fully executed, so you can read the outputs
without running anything.

The statistics follow Evan Miller, [Adding Error Bars to Evals: A Statistical Approach to
Language Model Evaluations](https://arxiv.org/abs/2411.00640) (2024).

## What's in here

| Path | What it is |
|---|---|
| `guide.ipynb` | The cookbook: the task, each tool at the point it is needed, the full run, and the gate |
| `error_bars.py` | The statistics: intervals, the paired difference, an exact sign test, a bootstrap cross-check, variance components, sample size and detectable effect. Standard library and NumPy |
| `refund_task.py` | The example task: the refund policy as code, a seeded case generator, and three versions of the prompt |
| `batch_runner.py` | Builds one request per prompt, case, and run, sends them through the Message Batches API, and grades the answers |
| `evaluation/run_eval.py` | The release gate, with a `better` mode and a `not-worse` mode |
| `data/cases.jsonl` | The 600 generated cases with their expected decisions |
| `results/` | The recorded run the notebook analyses, with a README describing the fields |
| `tests/` | Offline tests for all of the above, including one that recomputes every figure quoted in this README and in the notebook from the recorded run |

The shop, its policy, and every case are made up. Cases are generated from order facts and
labelled by the policy code, so the expected decisions are correct by construction.

## What the recorded run shows

Three versions of the prompt on 600 cases, three runs each:

| Prompt | Score (95% interval) |
|---|---|
| `draft`: the policy in prose, missing one sentence | 92.9% (91.2% to 94.7%) |
| `prose`: the draft plus that sentence | 98.0% (97.2% to 98.8%) |
| `procedure`: the policy rewritten as a checklist | 98.4% (97.6% to 99.2%) |

- **Adding one sentence** (what happens to a request that no rule allows) is a real
  improvement: +5.1 points, with an interval of +3.3 to +6.8.
- **Rewriting the policy as a procedure** is not a measurable one: +0.4 points, with an
  interval of -0.6 to +1.4. The interval is still useful: it rules out a drop of more than
  about 0.6 points, so the rewrite can be adopted for other reasons. A breakdown by policy
  rule shows it trading fewer mistakes on approvals for more on gift cards.
- **100 cases read once settle neither.** The first change comes out as +0.6 to +11.4
  points, where the interval and an exact test disagree about significance. The second
  comes out as -2.8 to +2.8, which cannot rule out a real drop.

The run of 5,400 requests cost $0.57.

## Run it

From this folder:

```bash
pip install -U "anthropic>=2.0.0" numpy pandas matplotlib python-dotenv jupyter
jupyter notebook guide.ipynb

python evaluation/run_eval.py                                      # draft -> prose
python evaluation/run_eval.py --baseline prose --candidate procedure
python evaluation/run_eval.py --baseline prose --candidate procedure --require not-worse
python evaluation/run_eval.py --run 3    # rerun the eval through the Batches API, then gate
python -m pytest tests                   # offline tests
```

The notebook needs an API key: it calls the API on five cases, for less than a cent. Set
`RUN_FULL_EVAL=1` before starting it to rerun all 5,400 requests. A rerun is written to
`results/rerun.jsonl` and never replaces the recorded run.

## Assumptions

- **Environment.** Python 3.11 or later and `ANTHROPIC_API_KEY` in the environment or in a
  `.env` file. The model ID is the `MODEL` constant in the notebook and `--model` on the
  gate; both default to `claude-haiku-5-5`.
- **Your eval.** One score per case and per run, in an array shaped `(cases, runs)`. Scores
  can be 0/1 or anything between. Cases are independent of each other; if yours come in
  groups (several questions about one document), you need clustered standard errors,
  which this code does not implement. Runs of a case are interchangeable.
- **Batches.** A batch usually ends within an hour and can take up to 24. Results are kept
  for 29 days, so keep the batch id that `submit_batch` returns.

## Failures the code handles

- **No usable answer.** A response that was cut off at `max_tokens`, refused, or is not
  the JSON that was asked for scores 0, as it would fail in production. One malformed
  answer does not stop the collection of the rest.
- **No response.** A batch entry that errored, expired, or was canceled removes its case
  from every prompt, so the comparison stays paired. `scores_by_prompt` returns the ids
  it left out.
- **Results in any order.** Batch results are matched to cases by `custom_id`, never by
  position. Duplicate rows for one attempt are refused.
- **Mismatched case sets.** `paired_diff_ci` refuses two score arrays of different shape.
- **An eval too small to judge.** The gate fails both of its modes when the interval is
  too wide, instead of passing because no regression was detected.

Intervals come from the normal approximation, which is unreliable for a score near 0% or
100% on few cases. The notebook shows two such intervals running past 100%.
