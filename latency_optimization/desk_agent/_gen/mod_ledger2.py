"""SIU pre-screens: the grader, and how far off each list of claim IDs is. Standard library only."""


def _set(x):
    return {str(i).strip().upper() for i in x}


def grade(item, p):
    """Exact set match on both lists (order, case, spaces and repeated IDs are ignored) and the points."""
    k = item["key"]
    try:
        return (
            _set(p["ph_claim_ids"]) == set(k["ph_claim_ids"])
            and _set(p["shop_flagged_claim_ids"]) == set(k["shop_flagged_claim_ids"])
            and int(p["siu_points"]) == k["siu_points"]
        )
    except Exception:
        return False


def detail(item, p):
    """Decision-level result and how far off each list is, for the log."""
    k = item["key"]
    try:
        A, B_ = _set(p["ph_claim_ids"]), _set(p["shop_flagged_claim_ids"])
        return dict(
            decision_ok=int(p["siu_points"]) == k["siu_points"],
            missed=len(set(k["ph_claim_ids"]) - A) + len(set(k["shop_flagged_claim_ids"]) - B_),
            extra=len(A - set(k["ph_claim_ids"])) + len(B_ - set(k["shop_flagged_claim_ids"])),
        )
    except Exception:
        return dict(decision_ok=False, missed=None, extra=None)
