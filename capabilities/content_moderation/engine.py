"""
Deterministic rule engine used by guide.ipynb.

Compiled artifact (what the compiler emits)
-------------------------------------------
{
  "derived_fields": {                      # LLM-judged booleans the compiler needed; merged into
    "<name>": {"type": ["boolean","null"], # the extraction schema at runtime (still ONE Claude call)
               "judge": "<instruction>", "source_policy": "1.1"}
  },
  "rules": [
    {
      "id": "nj_gambling_helpline",
      "policy_ref": "5.1",
      "policy_text": "In New Jersey, gambling creatives must display the 1-800-GAMBLER helpline.",
      "action": "block" | "flag",
      "scope": <condition>,                # optional. WHERE the rule applies. Evaluated against
                                           # context ∪ fields (context wins on name collision).
                                           # Absent scope = applies everywhere.
      "when": <condition>                  # the VIOLATION. Evaluated against extracted fields
                                           # (incl. derived). Rule fires => policy breached.
    }
  ],
  "uncompilable": [                        # clauses that map to NEITHER schema fields NOR an
    {"policy_ref": "...", "policy_text": "...", "reason": "..."}   # LLM judgment (e.g. need external data)
  ]
}

<condition> grammar (same for scope and when):
  {"all": [...]} | {"any": [...]} | {"not": <condition>}
  {"field": "<name>", "op": "<operator>", "value": <literal>}

Operators: eq, neq, gt, gte, lt, lte, in, not_in, contains, not_contains, regex, exists

Three-valued logic
------------------
Extraction may return null ("couldn't tell from the image") and context may omit keys.
Assertions on a missing/null value evaluate to UNKNOWN (None) and propagate Kleene-style.
  scope=False        -> out_of_scope (skipped, but logged)
  scope=True/absent  -> when: True->fired, False->clear, None->unknown
  scope=None         -> when: False->clear, else->unknown   (fail-safe, not fail-open)
Any unknown that would matter yields decision "needs_review" rather than a confident verdict.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

OPS = {
    "eq": lambda a, v: a == v,
    "neq": lambda a, v: a != v,
    "gt": lambda a, v: a > v,
    "gte": lambda a, v: a >= v,
    "lt": lambda a, v: a < v,
    "lte": lambda a, v: a <= v,
    "in": lambda a, v: a in v,
    "not_in": lambda a, v: a not in v,
    "contains": lambda a, v: (v.lower() in a.lower()) if isinstance(a, str) else (v in a),
    "not_contains": lambda a, v: (
        (v.lower() not in a.lower()) if isinstance(a, str) else (v not in a)
    ),
    "regex": lambda a, v: re.search(v, str(a), re.IGNORECASE) is not None,
    "exists": lambda a, v: True,  # handled specially below; only reached when a is not None
}


@dataclass
class Step:
    """One line of the audit trail: a leaf assertion, or an all/any/not connective."""

    field: str
    op: str
    expected: Any
    actual: Any
    result: bool | None
    depth: int = 0
    group: bool = False  # True = this line is an all/any/not connective, not a leaf


@dataclass
class RuleResult:
    rule_id: str
    action: str
    outcome: str  # "fired" | "clear" | "unknown" | "out_of_scope"
    scope_trace: list[Step] = field(default_factory=list)
    trace: list[Step] = field(default_factory=list)
    scope_result: bool | None = True  # True = in scope / no scope clause


@dataclass
class Verdict:
    decision: str  # "block" | "flag" | "needs_review" | "approve"
    fired: list[RuleResult]
    unknown: list[RuleResult]
    clear: list[RuleResult]
    out_of_scope: list[RuleResult]

    @staticmethod
    def _fmt(steps: list[Step], indent: str) -> list[str]:
        out = []
        for s in steps:
            mark = {True: "T", False: "F", None: "?"}[s.result]
            pad = indent + "  " * s.depth
            if s.group:
                out.append(f"{pad}{mark}  {s.op}:")
            else:
                rhs = "" if s.op == "exists" else f" {s.expected!r}"
                out.append(f"{pad}{mark}  {s.field} {s.op}{rhs}  (actual: {s.actual!r})")
        return out

    def explain(self) -> str:
        lines = [f"DECISION: {self.decision.upper()}"]
        for r in self.fired:
            lines.append(f"  ✗ [{r.action}] {r.rule_id}")
            if r.scope_trace:
                lines.append("      scope:")
                lines += self._fmt(r.scope_trace, "        ")
            lines += self._fmt(r.trace, "      ")
        for r in self.unknown:
            missing = sorted(
                {s.field for s in r.scope_trace + r.trace if s.result is None and not s.group}
            )
            why = "scope indeterminate" if r.scope_result is None else "could not determine"
            lines.append(f"  ? [{r.action}] {r.rule_id}  — {why}: {', '.join(missing)}")
        if self.out_of_scope:
            lines.append(f"  – out of scope: {', '.join(r.rule_id for r in self.out_of_scope)}")
        if not self.fired and not self.unknown:
            lines.append(f"  ✓ all {len(self.clear)} applicable rules clear")
        return "\n".join(lines)


def _eval(cond: dict, values: dict, trace: list[Step], depth: int = 0) -> bool | None:
    for connective in ("all", "any", "not"):
        if connective in cond:
            header = Step("", connective, None, None, None, depth, group=True)
            trace.append(header)
            children = cond[connective] if connective != "not" else [cond[connective]]
            results = [_eval(c, values, trace, depth + 1) for c in children]
            if connective == "all":
                out = (
                    False
                    if any(r is False for r in results)
                    else (None if any(r is None for r in results) else True)
                )
            elif connective == "any":
                out = (
                    True
                    if any(r is True for r in results)
                    else (None if any(r is None for r in results) else False)
                )
            else:
                out = None if results[0] is None else (not results[0])
            header.result = out
            return out

    name, op, expected = cond["field"], cond["op"], cond.get("value")
    actual = values.get(name)
    if op == "exists":
        result: bool | None = actual is not None
    elif actual is None:
        result = None
    else:
        try:
            result = bool(OPS[op](actual, expected))
        except (TypeError, re.error):
            result = None
    trace.append(Step(name, op, expected, actual, result, depth))
    return result


def evaluate_rule(rule: dict, fields: dict, context: dict | None = None) -> RuleResult:
    context = context or {}
    rr = RuleResult(rule["id"], rule.get("action", "flag"), "clear")

    if "scope" in rule:
        # context wins on collision; scope may also key off extracted fields (e.g. ad_category)
        rr.scope_result = _eval(rule["scope"], {**fields, **context}, rr.scope_trace)
        if rr.scope_result is False:
            rr.outcome = "out_of_scope"
            return rr

    w = _eval(rule["when"], fields, rr.trace)
    if rr.scope_result is None:  # can't confirm applicability: only a definite pass is safe
        rr.outcome = "clear" if w is False else "unknown"
    else:
        rr.outcome = "fired" if w is True else "clear" if w is False else "unknown"
    return rr


def evaluate(rules: list[dict], fields: dict, context: dict | None = None) -> Verdict:
    results = [evaluate_rule(r, fields, context) for r in rules]
    fired = [r for r in results if r.outcome == "fired"]
    unknown = [r for r in results if r.outcome == "unknown"]
    clear = [r for r in results if r.outcome == "clear"]
    oos = [r for r in results if r.outcome == "out_of_scope"]
    if any(r.action == "block" for r in fired):
        decision = "block"
    elif fired:
        decision = "flag"
    elif unknown:
        decision = "needs_review"
    else:
        decision = "approve"
    return Verdict(decision, fired, unknown, clear, oos)


# ---------------------------------------------------------------------------
# Static validation of a compiled document. Catches the compiler referencing
# a field that doesn't exist, scoping on an undeclared context key, comparing
# an enum to a value outside its set, etc., BEFORE anything runs. This is what
# the compiler's retry loop feeds back to Claude.
# ---------------------------------------------------------------------------

NUMERIC_OPS = {"gt", "gte", "lt", "lte"}
LIST_OPS = {"in", "not_in"}


def _check_condition(cond: Any, props: dict, path: str, problems: list[str]) -> None:
    if not isinstance(cond, dict):
        problems.append(f"{path}: condition must be an object")
        return
    keys = [k for k in ("all", "any", "not", "field") if k in cond]
    if len(keys) != 1:
        problems.append(f"{path}: must have exactly one of all/any/not/field, got {list(cond)}")
        return
    k = keys[0]
    if k in ("all", "any"):
        if not isinstance(cond[k], list) or not cond[k]:
            problems.append(f"{path}.{k}: must be a non-empty list")
            return
        for i, c in enumerate(cond[k]):
            _check_condition(c, props, f"{path}.{k}[{i}]", problems)
        return
    if k == "not":
        _check_condition(cond["not"], props, f"{path}.not", problems)
        return

    name, op = cond.get("field"), cond.get("op")
    if name not in props:
        problems.append(f"{path}: unknown field {name!r} (available: {sorted(props)})")
        return
    if op not in OPS:
        problems.append(f"{path}: unknown op {op!r}")
        return
    spec = props[name]
    ftype = spec.get("type")
    types = set(ftype) if isinstance(ftype, list) else {ftype}
    types.discard("null")
    val = cond.get("value")
    if op in NUMERIC_OPS and not types & {"number", "integer"}:
        problems.append(f"{path}: op {op!r} needs a numeric field, {name!r} is {ftype}")
    if op in LIST_OPS and not isinstance(val, list):
        problems.append(f"{path}: op {op!r} needs a list value")
    if "enum" in spec and op in ("eq", "neq") and val not in spec["enum"]:
        problems.append(f"{path}: {val!r} not in enum for {name!r}: {spec['enum']}")
    if "enum" in spec and op in LIST_OPS and isinstance(val, list):
        bad = [v for v in val if v not in spec["enum"]]
        if bad:
            problems.append(f"{path}: {bad!r} not in enum for {name!r}: {spec['enum']}")
    if op == "regex":
        try:
            re.compile(str(val))
        except re.error as e:
            problems.append(f"{path}: invalid regex {val!r}: {e}")


def validate_document(
    doc: dict, schema: dict, context_schema: dict | None = None
) -> dict[str, list[str]]:
    """Validate a full compiled artifact {derived_fields, rules, uncompilable}.

    Returns {rule_id_or_section: [problems]}; empty dict means well-formed.
    - 'when' may reference schema fields + derived fields.
    - 'scope' may reference context keys + schema fields + derived fields.
    """
    out: dict[str, list[str]] = {}
    derived = doc.get("derived_fields", {})

    dprobs: list[str] = []
    for name, spec in derived.items():
        if name in schema.get("properties", {}):
            dprobs.append(f"derived field {name!r} collides with schema field")
        if not spec.get("judge"):
            dprobs.append(f"derived field {name!r} missing 'judge' instruction")
    if dprobs:
        out["derived_fields"] = dprobs

    field_props = {**schema.get("properties", {}), **derived}
    scope_props = {**field_props, **(context_schema or {}).get("properties", {})}

    seen: set[str] = set()
    for r in doc.get("rules", []):
        rid = r.get("id", "<missing id>")
        probs: list[str] = []
        for key in ("id", "when"):
            if key not in r:
                probs.append(f"rule missing '{key}'")
        if r.get("action") not in (None, "block", "flag"):
            probs.append(f"action must be 'block' or 'flag', got {r.get('action')!r}")
        if rid in seen:
            probs.append(f"duplicate rule id {rid!r}")
        seen.add(rid)
        if "scope" in r:
            _check_condition(r["scope"], scope_props, f"{rid}.scope", probs)
        if "when" in r:
            _check_condition(r["when"], field_props, f"{rid}.when", probs)
        if probs:
            out.setdefault(rid, []).extend(probs)
    return out
