# Claude Managed Agents cookbooks

Claude Managed Agents is Anthropic's hosted runtime for stateful, tool-using
agents. You define an agent and a sandboxed environment once, then run
them in sessions that persist files, tool state, and conversation
across turns. These tutorials show it end to end.

## Applied cookbooks

- **[data_analyst_agent.ipynb](data_analyst_agent.ipynb)** builds an
  analyst that turns a CSV into a narrative HTML report using pandas
  and plotly. You'll configure an environment and agent, mount a
  dataset, stream the run, and retrieve the generated artifacts.
- **[slack_data_bot.ipynb](slack_data_bot.ipynb)** wraps that agent in
  a Slack bot. Mention it with a CSV to get the report in-thread;
  replies continue the same session.
- **[sre_incident_responder.ipynb](sre_incident_responder.ipynb)** puts
  Managed Agents on the on-call path: a pager alert starts a session,
  the agent investigates and opens a PR, then pauses for human
  approval before merging. You'll wire the alert webhook, attach a
  Skill and custom tools, and review the full run in the Console.

## Guided tutorials

End-to-end tutorials that teach the Managed Agents API surface
through realistic workflows. There's no strict reading order,
but `CMA_iterate_fix_failing_tests.ipynb` is a good entry point,
it introduces every API shape the others build on.

| Notebook | What it teaches |
|----------|-----------------|
| [`CMA_iterate_fix_failing_tests.ipynb`](CMA_iterate_fix_failing_tests.ipynb) | Do → observe → fix loop on a failing test suite. The entry-point notebook: introduces agent / environment / session, file mounts, and the streaming event loop through the lens of getting a buggy package to green. |
| [`CMA_orchestrate_issue_to_pr.ipynb`](CMA_orchestrate_issue_to_pr.ipynb) | Issue → fix → PR → CI → review → merge through a mock `gh` CLI. Multi-turn steering, mid-chain recovery from a CI failure and a review comment. Sidebar shows how to swap the file mount for a `github_repository` resource against a real repo. |
| [`CMA_explore_unfamiliar_codebase.ipynb`](CMA_explore_unfamiliar_codebase.ipynb) | Grounding in an unfamiliar codebase, with a planted stale-doc trap. Sidebar shows how to add resources to a running session via `sessions.resources.add`. |
| [`CMA_gate_human_in_the_loop.ipynb`](CMA_gate_human_in_the_loop.ipynb) | Human-in-the-loop expense approval via custom-tool `decide()` / `escalate()`. Covers the custom-tool round-trip pattern, the `requires_action` idle bounce, and parallel-tool-call dedupe. |
| [`CMA_prompt_versioning_and_rollback.ipynb`](CMA_prompt_versioning_and_rollback.ipynb) | Server-side prompt versioning: create v1, evaluate against a labelled test set, ship v2, detect a regression, roll back by pinning sessions to version 1. Covers `agents.update`, version pinning on `sessions.create`, and where the review gate moves when prompts are not code. |
| [`CMA_operate_in_production.ipynb`](CMA_operate_in_production.ipynb) | Production setup: MCP toolsets, vaults for per-end-user credentials, the `session.status_idled` webhook pattern for HITL without long-lived connections, and the resource lifecycle CRUD verbs. |

The streaming event loop is walked through line by line in the
iterate notebook and then factored into
`utilities.stream_until_end_turn` so the other notebooks can
import it instead of repeating the `match ev.type:` block. The
gate notebook is the exception: it keeps the loop inline because
custom-tool agents need to handle `requires_action` idle bounces
in addition to `end_turn`, which the helper doesn't cover.

## Getting started

Set `ANTHROPIC_API_KEY` in your environment, then open
`data_analyst_agent.ipynb` in Jupyter and run the cells top to
bottom. Each notebook installs its own dependencies and prompts
for any credentials it needs. The orchestrate-to-PR sidebar in
`CMA_orchestrate_issue_to_pr.ipynb` and the vault-backed MCP
example in `CMA_operate_in_production.ipynb` additionally need
`GITHUB_TOKEN` set (a fine-grained PAT with public-repo read is
enough).

All cookbook fixture data — input CSVs and supporting assets for
the applied cookbooks, plus the planted-trap fixtures the guided
tutorials read from — lives under `example_data/`. See
[`example_data/OVERVIEW.md`](example_data/OVERVIEW.md) for the
directory map.
