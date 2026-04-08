# Orchestrate, drive an issue to a merged PR

Self-contained mock of a maintainer workflow, used by `CMA_orchestrate_issue_to_pr.py`. The cookbook zips this directory and hands it to the agent.

- `gh-mock`, bash script that fakes the relevant `gh` subcommands. State persists in `.gh-state/`.
- `issue_42.json`, Unicode bug report (`Café Culture` → `caf-culture`). Vague enough that the agent has to read code.
- `src/url_utils.py` + `src/blog.py` + `tests/test_urls.py`, buggy `slugify()` and the failing tests that catch it.

Two recovery points are planted: an incomplete first fix fails CI with a pytest traceback, and the mock reviewer-bot blocks the merge if `slugify()` is missing a docstring. A healthy run ends with `.gh-state/pr_101.json` showing `state: merged`, `ci/test: pass`, and an `APPROVED` review.
