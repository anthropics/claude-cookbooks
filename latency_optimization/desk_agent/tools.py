"""Eight simulated tools: five lookups and three recorders. Every tool is a pure function of (item, arguments): no clock, no randomness, no I/O beyond the package's own data files."""

import json
import re
from functools import cache
from pathlib import Path

from .prompt import PARTS, PARTS_HEAD, TEMPLATES

DATA = Path(__file__).parent / "data"
RECORDERS = {"quote": "submit_quote", "prescreen": "submit_prescreen", "letter": "submit_letter"}
SIZES = {
    False: dict(est=15, rows=10, parts=20),
    True: dict(est=30, rows=20, parts=40),
}  # keyed by big_pages. Small enough that the longest estimates and ledger searches take several pages
LEDGER_COLS = ["claim", "policyholder", "loss date", "type", "status", "paid", "shop", "SIU flag"]
_S, _I, _BOOL = {"type": "string"}, {"type": "integer", "minimum": 1}, {"type": "boolean"}
_IDS = {"type": "array", "items": {"type": "string"}}


def _spec(name, description, props, required):
    return {
        "name": name,
        "description": description,
        "input_schema": {"type": "object", "properties": props, "required": required},
    }


def tool_specs(*, big_pages=False):
    z = SIZES[bool(big_pages)]
    return [
        _spec(
            "get_claim",
            "The claim record. For a claim being settled: policy, vehicle, loss facts, other charges and file notes. For a claim being pre-screened: policyholder, date of loss and repair shop. For a decided claim: the decision record.",
            {"claim_id": _S},
            ["claim_id"],
        ),
        _spec(
            "get_estimate",
            f"The repair estimate of record, {z['est']} lines per page. Every page says how many pages there are. The billed total and any supplement note are on the last page.",
            {"claim_id": _S, "page": _I},
            ["claim_id"],
        ),
        _spec(
            "lookup_parts",
            f"Appendix A catalogue rows for up to {z['parts']} catalogue numbers per call.",
            {"cat_nos": _IDS},
            ["cat_nos"],
        ),
        _spec(
            "search_ledger",
            f'Search the claims ledger. All filters are optional and combine with AND. shop matches any shop whose name contains the text, ignoring case; ledger shop names carry no state, so a trailing state ("Harbor Auto Body, OH") is ignored. policyholder_id must match exactly. date_from and date_to bound the loss date, are YYYY-MM-DD and are inclusive. Returns {z["rows"]} rows per page, in no particular order, with the number of matching rows and pages.',
            {
                "policyholder_id": _S,
                "shop": _S,
                "date_from": _S,
                "date_to": _S,
                "flagged_only": _BOOL,
                "page": _I,
            },
            [],
        ),
        _spec(
            "get_template",
            "The approved text of a Section 7 letter template.",
            {"template_id": _S},
            ["template_id"],
        ),
        _spec(
            "submit_quote",
            "Recorder for a settlement quote (10.1). Call once, when done.",
            {
                "verdict": {"type": "string", "enum": ["APPROVE", "SUPERVISOR", "FRAUD", "DENY"]},
                "amount": {"type": "number"},
            },
            ["verdict", "amount"],
        ),
        _spec(
            "submit_prescreen",
            "Recorder for an SIU pre-screen (10.2). Call once, when done.",
            {
                "ph_claim_ids": _IDS,
                "shop_flagged_claim_ids": _IDS,
                "siu_points": {"type": "integer"},
            },
            ["ph_claim_ids", "shop_flagged_claim_ids", "siu_points"],
        ),
        _spec(
            "submit_letter",
            'Recorder for a customer letter (10.3). Call once, when done. pay_after_acceptance is the 8.2 entry, or "none" for a full denial.',
            {
                "template": {"type": "string", "enum": sorted(TEMPLATES)},
                "pay_after_acceptance": _S,
                "letter": _S,
            },
            ["template", "pay_after_acceptance", "letter"],
        ),
    ]


TOOL_NAMES = [t["name"] for t in tool_specs()]


def is_terminal(name):
    return name in RECORDERS.values()


@cache
def _ledgers(split):
    return json.loads((DATA / split / "ledgers.json").read_text())


def ledger_rows(item):
    """The rows search_ledger searches for this item: the claim's own rows for a quote, one of the four shared ledgers in ledgers.json for a pre-screen, none for a letter."""
    if item["type"] == "quote":
        return item["_ledger_rows"]
    if item["type"] == "prescreen":
        return _ledgers(item["_split"])[item["_ledger"]]
    return []


def render_row(r):
    return " | ".join(r[c] for c in LEDGER_COLS)


_DATE = re.compile(r"\d{4}-\d{2}-\d{2}$")
_STATE = re.compile(r",\s*[A-Z]{2}\.?$")


def _err(msg):
    return "ERROR: " + msg


def _page(args):
    p = args.get("page", 1)
    if p is None:
        p = 1
    if isinstance(p, str) and re.fullmatch(r"[0-9]{1,9}", p.strip()):
        p = int(p)
    if isinstance(p, float) and p.is_integer():
        p = int(p)
    return p if isinstance(p, int) and not isinstance(p, bool) and p >= 1 else None


def call_tool(item, name, args, *, big_pages=False):
    """Returns the tool result as a string. Bad names or arguments give a string that starts with "ERROR: "; nothing the model writes can raise.
    big_pages doubles the page sizes, which tool_specs states in its descriptions, so give both the same value."""
    z = SIZES[bool(big_pages)]
    if name not in TOOL_NAMES:
        return _err(f"unknown tool {name!r}")
    if not isinstance(args, dict):
        return _err("arguments must be an object")
    if is_terminal(name):
        return "Recorded."
    if name in ("get_claim", "get_estimate"):
        cid = args.get("claim_id")
        if not isinstance(cid, str) or cid.strip().upper() != item["claim_id"]:
            return _err(
                f"no claim {cid!r} is open on this call; the open claim is {item['claim_id']}"
            )
        if name == "get_claim":
            return item["_claim"]
        if item["type"] != "quote":
            return _err("this claim has no estimate attached; get_claim has everything on file")
        lines = item["_est_lines"]
        total = max(1, -(-len(lines) // z["est"]))
        p = _page(args)
        if p is None or p > total:
            return _err(f"page must be a whole number from 1 to {total}")
        part = lines[(p - 1) * z["est"] : p * z["est"]] + (item["_est_tail"] if p == total else [])
        return "\n".join([item["_est_head"]] + part + [f"[page {p} of {total}]"])
    if name == "lookup_parts":
        nos = args.get("cat_nos")
        if isinstance(nos, str):
            nos = re.findall(r"\d+", nos)  # a list sent as one string
        if not isinstance(nos, list) or not nos:
            return _err("cat_nos must be a non-empty list of catalogue numbers")
        if len(nos) > z["parts"]:
            return _err(f"at most {z['parts']} catalogue numbers per call")
        nos = [str(n).strip().strip("[]") for n in nos]
        return "\n".join(
            [PARTS_HEAD] + [PARTS.get(n, f"| {n} | not in the catalogue |") for n in nos]
        )
    if name == "search_ledger":
        args = {
            k: v for k, v in args.items() if v is not None and v != ""
        }  # an optional filter sent empty is a filter not used
        for k in ("date_from", "date_to"):
            if k in args and not (isinstance(args[k], str) and _DATE.match(args[k])):
                return _err(f"{k} must be YYYY-MM-DD")
        for k in ("policyholder_id", "shop"):
            if k in args and not isinstance(args[k], str):
                return _err(f"{k} must be a string")
        if "flagged_only" in args and not isinstance(args["flagged_only"], bool):
            return _err("flagged_only must be true or false")
        bad = set(args) - {
            "policyholder_id",
            "shop",
            "date_from",
            "date_to",
            "flagged_only",
            "page",
        }
        if bad:
            return _err(f"unknown filter {sorted(bad)[0]!r}")
        hit = [
            r
            for r in ledger_rows(item)
            if (
                "policyholder_id" not in args
                or r["policyholder"] == args["policyholder_id"].strip()
            )
            and (
                "shop" not in args
                or _STATE.sub("", args["shop"].strip()).lower() in r["shop"].lower()
            )
            and ("date_from" not in args or r["loss date"] >= args["date_from"])
            and ("date_to" not in args or r["loss date"] <= args["date_to"])
            and (not args.get("flagged_only") or r["SIU flag"] == "Y")
        ]
        total = max(1, -(-len(hit) // z["rows"]))
        p = _page(args)
        if p is None or p > total:
            return _err(f"page must be a whole number from 1 to {total}")
        head = f"{len(hit)} rows match; page {p} of {total}"
        if not hit:
            return head
        return "\n".join(
            [head, " | ".join(LEDGER_COLS)]
            + [render_row(r) for r in hit[(p - 1) * z["rows"] : p * z["rows"]]]
        )
    if name == "get_template":
        t = str(args.get("template_id", "")).strip()
        return (
            TEMPLATES[t] if t in TEMPLATES else _err(f"no template {t!r}; the IDs are in Section 7")
        )
    return _err("unreachable")
