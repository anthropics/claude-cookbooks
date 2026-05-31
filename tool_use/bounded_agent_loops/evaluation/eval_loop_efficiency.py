"""Loop-efficiency scorer for the cost-aware-agent-loops cookbook.

Runs the unguarded and guarded loops from the guide on the labelled query set in
data/sample_queries.json and reports the trade-off table: accuracy, mean iteration
count, mean tokens, max tokens. The interesting columns are mean/max tokens (the cost
distribution) and accuracy (whether guards are paying for themselves).

The agent definitions live inline rather than being imported from the notebook so this
file is runnable standalone after `uv sync --all-extras`.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal
from urllib.parse import quote

import anthropic
import requests
from dotenv import load_dotenv
from pydantic import BaseModel, Field

HAIKU = "claude-haiku-4-5"
SONNET = "claude-sonnet-4-6"

WIKI_API = "https://en.wikipedia.org/api/rest_v1/page/summary/"
COUNTRIES_API = "https://restcountries.com/v3.1/name/"
HEADERS = {"User-Agent": "claude-cookbooks/1.0 (cost-aware-agent-loops/eval)"}

DATA_DIR = Path(__file__).parent.parent / "data"


# ---- Tools -----------------------------------------------------------------


def country_info(name: str) -> dict[str, Any]:
    r = requests.get(COUNTRIES_API + quote(name), headers=HEADERS, timeout=10)
    if r.status_code == 404:
        return {"error": f"no country matched '{name}'"}
    r.raise_for_status()
    hit = r.json()[0]
    return {
        "name": hit["name"]["common"],
        "capital": hit.get("capital", [None])[0],
        "region": hit.get("region"),
        "population": hit.get("population"),
        "languages": list(hit.get("languages", {}).values()),
        "currencies": list(hit.get("currencies", {}).keys()),
    }


def wikipedia_summary(title: str) -> str:
    r = requests.get(WIKI_API + quote(title.replace(" ", "_")), headers=HEADERS, timeout=10)
    if r.status_code == 404:
        return f"no Wikipedia article matched '{title}'"
    r.raise_for_status()
    return r.json()["extract"]


TOOLS = {"country_info": country_info, "wikipedia_summary": wikipedia_summary}

TOOL_SCHEMA = """Available tools:

- country_info(name: str) -> dict
    Returns structured facts (capital, region, population, official languages,
    currencies) for a country. Use exact country names.

- wikipedia_summary(title: str) -> str
    Returns the first paragraph of a Wikipedia article. Use for facts that aren't
    in the country_info structured fields."""


# ---- State + node primitives -----------------------------------------------


@dataclass
class AgentState:
    query: str
    plan: list[dict[str, Any]] = field(default_factory=list)
    trace: list[dict[str, Any]] = field(default_factory=list)
    reflection: str = ""
    answer: str = ""
    iterations: int = 0
    tokens_in: int = 0
    tokens_out: int = 0
    should_continue: bool = True


class ToolCall(BaseModel):
    tool: Literal["country_info", "wikipedia_summary"]
    argument: str
    rationale: str


class Plan(BaseModel):
    calls: list[ToolCall]


class Reflection(BaseModel):
    summary: str
    should_continue: bool
    confidence: float = Field(ge=0.0, le=1.0)
    what_is_missing: str


@dataclass
class Budget:
    max_tokens_in: int = 30_000
    max_tokens_out: int = 5_000
    estimated_call_in: int = 3_000
    estimated_call_out: int = 500


def would_exceed_budget(state: AgentState, budget: Budget) -> bool:
    return (
        state.tokens_in + budget.estimated_call_in > budget.max_tokens_in
        or state.tokens_out + budget.estimated_call_out > budget.max_tokens_out
    )


def planner(client: anthropic.Anthropic, state: AgentState) -> AgentState:
    context = (
        f"User query: {state.query}\n\n"
        f"{TOOL_SCHEMA}\n\n"
        f"Previous tool outputs:\n"
        f"{json.dumps(state.trace, indent=2) if state.trace else '(none yet)'}\n\n"
        f"Reflection from previous iteration:\n{state.reflection or '(none)'}\n\n"
        f"Plan the next 1-3 tool calls. Return an empty list ONLY when every fact "
        f"needed to answer the query is already present in the tool outputs above. "
        f"Do not skip tools because you think you know the answer from prior "
        f"knowledge — the user wants tool-grounded facts."
    )
    response = client.messages.parse(
        model=HAIKU,
        max_tokens=800,
        messages=[{"role": "user", "content": context}],
        output_format=Plan,
    )
    state.tokens_in += response.usage.input_tokens
    state.tokens_out += response.usage.output_tokens
    state.plan = [c.model_dump() for c in response.parsed_output.calls]
    return state


def executor(state: AgentState) -> AgentState:
    for call in state.plan:
        try:
            output = TOOLS[call["tool"]](call["argument"])
        except (requests.RequestException, KeyError) as e:
            output = {"error": str(e)}
        state.trace.append({"call": call, "output": output})
    state.plan = []
    return state


def reflector_naive(client: anthropic.Anthropic, state: AgentState) -> AgentState:
    """Free-text reflection used to inform the next iteration's planning context.

    No explicit termination signal; the naive unguarded loop relies on the planner
    returning an empty plan to terminate.
    """
    context = (
        f"User query: {state.query}\n\n"
        f"Tool outputs so far:\n{json.dumps(state.trace, indent=2)}\n\n"
        f"Summarise what the trace tells us so far and note what's still missing."
    )
    response = client.messages.create(
        model=SONNET,
        max_tokens=400,
        messages=[{"role": "user", "content": context}],
    )
    state.tokens_in += response.usage.input_tokens
    state.tokens_out += response.usage.output_tokens
    state.reflection = response.content[0].text
    state.should_continue = True  # naive loop has no explicit termination signal
    return state


def reflector_structured(client: anthropic.Anthropic, state: AgentState) -> AgentState:
    context = (
        f"User query: {state.query}\n\n"
        f"Tool outputs so far:\n{json.dumps(state.trace, indent=2)}\n\n"
        f"Decide whether another iteration would help. Be honest about diminishing "
        f"returns: if the trace already contains the answer, set should_continue=False."
    )
    response = client.messages.parse(
        model=SONNET,
        max_tokens=400,
        messages=[{"role": "user", "content": context}],
        output_format=Reflection,
    )
    state.tokens_in += response.usage.input_tokens
    state.tokens_out += response.usage.output_tokens
    parsed = response.parsed_output
    state.reflection = (
        f"{parsed.summary} (continue={parsed.should_continue}, confidence={parsed.confidence:.2f})"
    )
    state.should_continue = parsed.should_continue
    return state


def recommender(client: anthropic.Anthropic, state: AgentState) -> AgentState:
    context = (
        f"User query: {state.query}\n\n"
        f"All tool outputs collected:\n{json.dumps(state.trace, indent=2)}\n\n"
        f"Answer the query in one or two sentences. If the trace doesn't contain "
        f"enough information, say so explicitly rather than guessing."
    )
    response = client.messages.create(
        model=SONNET,
        max_tokens=400,
        messages=[{"role": "user", "content": context}],
    )
    state.tokens_in += response.usage.input_tokens
    state.tokens_out += response.usage.output_tokens
    state.answer = response.content[0].text
    return state


# ---- Two loop variants -----------------------------------------------------


def run_unguarded(client: anthropic.Anthropic, query: str) -> AgentState:
    """Naive pattern: trust the planner to return empty when done."""
    state = AgentState(query=query)
    while True:
        state.iterations += 1
        state = planner(client, state)
        if not state.plan:  # planner self-terminates
            break
        state = executor(state)
        state = reflector_naive(client, state)
        if state.iterations > 10:  # absolute safety net
            break
    return recommender(client, state)


def run_guarded(
    client: anthropic.Anthropic,
    query: str,
    max_iterations: int = 3,
    budget: Budget | None = None,
) -> AgentState:
    budget = budget or Budget()
    state = AgentState(query=query)
    while state.iterations < max_iterations:
        if would_exceed_budget(state, budget):
            state.reflection = "(budget cap reached)"
            break
        state.iterations += 1
        state = planner(client, state)
        if not state.plan:
            break
        state = executor(state)
        if would_exceed_budget(state, budget):
            state.reflection = "(budget cap reached after executor)"
            break
        state = reflector_structured(client, state)
        if not state.should_continue:
            break
    return recommender(client, state)


# ---- Scoring ---------------------------------------------------------------


def score_answer(answer: str, gold_contains: list[str]) -> bool:
    return all(phrase.lower() in answer.lower() for phrase in gold_contains)


def evaluate(client, run_fn, eval_set: list[dict], label: str) -> dict:
    results = []
    skipped = []
    for case in eval_set:
        try:
            state = run_fn(client, case["query"])
        except (anthropic.APIError, requests.RequestException) as e:
            print(f"  skipped (API error): {case['query']!r}: {e}")
            skipped.append(case["query"])
            continue
        correct = score_answer(state.answer, case["gold_contains"])
        results.append(
            {
                "query": case["query"],
                "correct": correct,
                "iterations": state.iterations,
                "tokens": state.tokens_in + state.tokens_out,
            }
        )
    if not results:
        return {
            "label": label,
            "accuracy": 0.0,
            "mean_iterations": 0.0,
            "mean_tokens": 0,
            "max_tokens": 0,
            "n_scored": 0,
            "n_total": len(eval_set),
            "skipped": skipped,
            "per_query": [],
        }
    n = len(results)
    return {
        "label": label,
        "accuracy": sum(r["correct"] for r in results) / n,
        "mean_iterations": sum(r["iterations"] for r in results) / n,
        "mean_tokens": sum(r["tokens"] for r in results) / n,
        "max_tokens": max(r["tokens"] for r in results),
        "n_scored": n,
        "n_total": len(eval_set),
        "skipped": skipped,
        "per_query": results,
    }


def main() -> None:
    load_dotenv()
    # max_retries bumped from the default of 2 to ride out transient overload
    # windows (HTTP 529) on a multi-query evaluation run.
    client = anthropic.Anthropic(max_retries=5)

    with open(DATA_DIR / "sample_queries.json", encoding="utf-8") as f:
        eval_set = json.load(f)

    print(f"Running {len(eval_set)} queries through each configuration.\n")

    print("Unguarded loop:")
    unguarded = evaluate(client, run_unguarded, eval_set, "unguarded")

    print("\nGuarded loop (cap=3, budget=30k/5k, structured reflector):")
    guarded = evaluate(client, run_guarded, eval_set, "guarded")

    print(f"\n{'config':<55} {'acc':>5} {'iter':>5} {'mean_tok':>9} {'max_tok':>8} {'n':>6}")
    print("-" * 96)
    for r in (unguarded, guarded):
        n_str = f"{r['n_scored']}/{r['n_total']}"
        print(
            f"{r['label']:<55} {r['accuracy']:>5.2f} {r['mean_iterations']:>5.1f} "
            f"{r['mean_tokens']:>9.0f} {r['max_tokens']:>8.0f} {n_str:>6}"
        )
    # Loud about skips: any skipped query is a confounder on the comparison.
    for r in (unguarded, guarded):
        if r["skipped"]:
            print(
                f"\nWARNING: {len(r['skipped'])} query(s) skipped in {r['label']!r} "
                f"due to API errors. Accuracy and means are over the scored subset only."
            )

    # Per-query breakdown for both runs. The unguarded iteration counts are the
    # diagnostic for whether the query set is hard enough to bind the cap; if every
    # unguarded query terminates in 1-2 iterations, the cap isn't being tested.
    print("\nUnguarded per-query:")
    for r in unguarded["per_query"]:
        mark = "OK" if r["correct"] else "--"
        print(f"  [{mark}] iter={r['iterations']} tok={r['tokens']:>5}  {r['query'][:60]}")

    print("\nGuarded per-query:")
    for r in guarded["per_query"]:
        mark = "OK" if r["correct"] else "--"
        print(f"  [{mark}] iter={r['iterations']} tok={r['tokens']:>5}  {r['query'][:60]}")


if __name__ == "__main__":
    main()
