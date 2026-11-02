"""Grades the recorder call with the graders in _gen."""

import json
import re

from ._gen import mod_ledger2 as _C
from ._gen import mod_letters as _A
from ._gen import mod_quote as _B
from .tools import RECORDERS


def _ids(v):
    """A list of IDs, however it was sent: a list, a JSON string, a comma or space separated string, or nothing."""
    if v is None:
        return []
    if isinstance(v, str):
        try:
            v = json.loads(v)
        except ValueError:
            v = [x for x in re.split(r"[,\s]+", v.strip("[] ")) if x]
    return list(v) if isinstance(v, (list, tuple)) else [v]


def _normal(kind, a):
    """Removes harmless differences of form before the graders in _gen run, because tool input need not match its schema."""
    a = dict(a)
    if kind == "quote":
        if isinstance(a.get("amount"), str):
            a["amount"] = a["amount"].replace("$", "").replace(",", "").strip()
        if isinstance(a.get("verdict"), str):
            a["verdict"] = a["verdict"].strip().upper()
        if a.get("amount") is None and a.get("verdict") in ("DENY", "FRAUD"):
            a["amount"] = 0  # nothing is payable, so no amount means 0
    elif kind == "prescreen":
        for f in ("ph_claim_ids", "shop_flagged_claim_ids"):
            a[f] = _ids(a.get(f))
    else:
        a.setdefault("pay_after_acceptance", None)
    return a


def grade(item, recorded):
    """recorded = {"name", "args"} of the first recorder call, or None. The same flat keys for every item type; a key that does not apply stays False or 0."""
    out = dict(
        correct=False,
        answered=recorded is not None,
        right_recorder=False,
        decision_ok=False,
        ids_missed=0,
        ids_extra=0,
        verdict_ok=False,
        amount_ok=False,
        template_ok=False,
        pay_ok=False,
    )
    if (
        not recorded
        or recorded.get("name") != RECORDERS[item["type"]]
        or not isinstance(recorded.get("args"), dict)
    ):
        return out
    out["right_recorder"] = True
    k, g = item["key"], {"key": item["key"]}
    try:
        a = _normal(item["type"], recorded["args"])
        if item["type"] == "quote":
            out["correct"] = bool(_B.grade(g, a))
            out["verdict_ok"] = a.get("verdict") == k["verdict"]
            out["amount_ok"] = abs(float(a.get("amount")) - k["amount"]) <= 0.5
        elif item["type"] == "prescreen":
            out["correct"] = bool(_C.grade(g, a))
            d = _C.detail(g, a)
            out["decision_ok"] = bool(d["decision_ok"])
            out["ids_missed"] = int(d["missed"] or 0)
            out["ids_extra"] = int(d["extra"] or 0)
        else:
            out["correct"] = bool(_A.grade(g, a))
            out["template_ok"] = a.get("template") == k["template"]
            pa = (a.get("pay_after_acceptance") or "").strip().lower()
            out["pay_ok"] = (
                (pa in ("", "null", "none", "n/a", "not applicable"))
                if k["pay"] is None
                else (_A.ENTRY.findall(pa) == [k["pay"].lower()])
            )
    except Exception:  # noqa: S110 (an answer of the wrong shape keeps the failing marks set above)
        pass
    return out
