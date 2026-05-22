# Loop-efficiency evaluation

Standalone script that compares the unguarded and guarded agent loops from the guide
on the labelled query set in `../data/sample_queries.json`.

## Run

```bash
cd capabilities/cost_aware_agent_loops/evaluation
uv run python eval_loop_efficiency.py
```

Requires `ANTHROPIC_API_KEY` in the environment (or in a `.env` at the cookbook root).

## Expected output

A two-row table comparing the configurations, followed by a per-query breakdown
for the guarded run. From one run of the eight-query set:

```
config                                                  acc  iter  mean_tok  max_tok      n
unguarded                                              1.00   5.2     33200   114166    8/8
guarded                                                0.88   1.2      4018    14698    8/8

Unguarded per-query:
  [OK] iter= 2 tok=  2486  Which Nordic country has Icelandic as its official language?
  [OK] iter= 2 tok=  2384  What is the official currency of the country whose capital
  [OK] iter= 3 tok=  8538  Among the G7 countries (United States, United Kingdom, ...
  [OK] iter= 3 tok=  7700  Compare the populations of the capital cities of Germany ...
  [OK] iter= 8 tok= 46904  Among the five most populous countries in Europe (Russia ...
  [OK] iter= 2 tok=  4894  List the official currencies of all G7 countries (United ...
  [OK] iter=11 tok=114166  Compare the total areas of all G7 countries (United States ...
  [OK] iter=11 tok= 78528  Among the G7 countries (United States, United Kingdom ...

Guarded per-query:
  [OK] iter=1 tok= 1449  Which Nordic country has Icelandic as its official language?
  [OK] iter=1 tok= 1458  What is the official currency of the country whose capital
  [OK] iter=1 tok= 3079  Among the G7 countries (United States, United Kingdom, ...
  [OK] iter=1 tok= 2181  Compare the populations of the capital cities of Germany ...
  [--] iter=1 tok= 2801  Among the five most populous countries in Europe (Russia ...
  [OK] iter=1 tok= 3251  List the official currencies of all G7 countries (United ...
  [OK] iter=3 tok=14698  Compare the total areas of all G7 countries (United States ...
  [OK] iter=1 tok= 3227  Among the G7 countries (United States, United Kingdom ...
```

Run-to-run variance is meaningful; the planner and reflector are both
non-deterministic. The same query set executed inside the notebook produced
unguarded mean 20,769 / max 68,829 and guarded mean 5,570 / max 10,069 with 1.00
accuracy on both. Both outcomes are real, and treating any single run as the
canonical number would be misleading. The pattern across runs is stable: guards
reduce mean and max tokens, and on the hardest queries can clip the
trace before the answer is fully reachable (driving the 0.88 accuracy seen above
on the "five most populous European countries / smallest area" query).

The unguarded per-query iteration counts above are the diagnostic for whether
the query set is hard enough to bind the cap. Iterations of 8 and 11 (the
last three queries) confirm the cap is being meaningfully tested; if all
unguarded queries terminated in 1-2 iterations, the cap-bound max-token
reduction would be uninteresting.

If you want a tighter estimate for your own workload, average over 5+ runs. If
accuracy drops too far for your taste, the iteration cap is probably binding too
early; try `max_iterations=4` and re-run. If mean tokens are unexpectedly high
on guarded, the structured reflector is over-committing to `should_continue=True`;
tighten its prompt.

The `n=scored/total` column flags any queries that were skipped due to API or
upstream errors. If you see a WARNING line after the table, accuracy and means
are computed over the scored subset only and are not comparable to a clean run.

## Notes

- The script makes ~100-200 Claude API calls per full run (around £0.80-£1.50 at
  current Haiku + Sonnet pricing). Budget cap settings prevent runaway in
  pathological cases. The unguarded loop is the expensive side; if you only want
  to verify the numbers cheaply, comment out the unguarded evaluation in `main()`.
- Both runs hit the free REST Countries and Wikipedia APIs. If those are flaky,
  the scorer skips affected queries rather than failing the whole run; the
  WARNING line surfaces this.
- The scoring metric (substring match against gold phrases) is intentionally
  simple. Swap in an LLM-judge if you want to score nuance.
