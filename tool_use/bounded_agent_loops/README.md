# Bounded Agent Loops with Claude

Three guards for making termination of a multi-step agent loop an explicit,
auditable decision rather than implicit in the planner's behaviour: a hard
iteration cap, a per-request token budget, and a structured reflector that
commits to `should_continue` via a Pydantic schema.

## Contents

- `guide.ipynb`: Main tutorial notebook with a runnable four-node agent (planner,
  executor, reflector, recommender) over two free APIs (REST Countries, Wikipedia).
- `data/sample_queries.json`: Eight multi-hop geography queries with gold answers
  for evaluation. Treated as illustrative, not a benchmark.
- `evaluation/eval_loop_efficiency.py`: Standalone scorer that compares the
  unguarded and guarded loops on the labelled set.

For evaluation instructions, see `evaluation/README.md`.
