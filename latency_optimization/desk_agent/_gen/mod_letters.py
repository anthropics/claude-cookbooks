"""Customer letters: the grader. It checks a letter against the approved Section 7 template and the values the task's key names. Standard library only."""

import re


def _manual():
    """One manual for the whole cookbook: the same text the quote prompt carries."""
    from . import mod_quote

    return mod_quote.SYSTEM.split("<manual>")[1].split("</manual>")[0].strip()


# Grader. Every check maps to a sentence of the system prompt: "keep the approved wording unchanged" (the template's whole text, in order and unbroken),
# "fill every bracket you can from the record" (each keyed value in its own bracket's place, no square bracket where one was to be filled),
# "leave that bracket as it is" (KEEP), "exactly as the matrix shows it" (pay entry).
ENTRY = re.compile(r"(?<!\d)(?:30 days|5 business days|20 days|10 days)|prompt")
TEMPLATE = dict(re.findall(r'\(Template ([A-Z0-9-]+)\)\n> "([^\n]+)"\n', _manual()))
assert len(TEMPLATE) == 7, sorted(TEMPLATE)
KEEP = ("[QUOTE POLICY LANGUAGE]", "[Insert state-mandated")
PROSE = ("[DESCRIPTION", "[plain-language reason]", "[factual basis]")
STOP = r"[.!?] [A-Z]"  # where one sentence ends and the next begins
# One parenthetical may follow a keyed value, as in "$1,325.00 (as billed)", "$0.00 (waived)" or "EXCL-08 (Non-permissive use, PP-00-01 A.4)":
# it belongs to the bracket's fill and leaves the approved wording alone. It may hold no STOP. It is not read for sense.
GLOSS = r"(?: \((?:(?!%s)[^()\[\]])*\))?" % STOP  # noqa: UP031 (a regex: braces would need escaping)


def _norm(s):
    """Typography is not wording: commas, quotation marks, backticks and asterisks are dropped, a dash of any kind is a hyphen, white space is one space."""
    s = re.sub("[,'\"`*\u2018\u2019\u201c\u201d\u2032]", "", s)
    s = re.sub("[\u2010-\u2015\u2212]", "-", s)
    return re.sub(r"\s+", " ", s)


def _val(n):  # "$500.00" also matches "$500"; "$993.75" must match as written
    n = re.escape(n.replace(",", ""))
    return (n[:-4] + r"(?:\.00)?") if n.endswith(r"\.00") else n


def _block(t, need):
    """The whole template as one pattern. Words outside brackets stand as printed and in order, with nothing between them but the fills. Only at the very end of the letter may the last full stop be missing.
    A "$[...]" bracket and [EXCL-CODE] take the keyed values in the key's order, each with its GLOSS if any. A KEEP bracket stands as printed.
    Any other bracket takes text that holds no square bracket: a PROSE bracket as many sentences as the writer likes, the rest ([PAYEE], [DATE], [ITEM], [YEAR MAKE MODEL]) no STOP."""
    need, out = list(need), ""
    for part in re.split(r"(\$?\[[^\]]*\])", _norm(TEMPLATE[t]).rstrip(".")):
        if part.startswith("$[") or part == "[EXCL-CODE]":
            out += _val(need.pop(0)) + GLOSS
        elif part.startswith(PROSE):
            out += r"[^\[\]]+?"
        elif part.startswith("[") and not part.startswith(KEEP):
            out += r"(?:(?!%s)[^\[\]])+?" % STOP  # noqa: UP031 (a regex: braces would need escaping)
        else:  # where the template prints a long dash, the spaces round it and a doubled hyphen are typography too
            out += re.escape(part).replace(r"\ \-\ ", " ?-+ ?")
    assert not need, (t, need)
    return out + r"(?:\.|\s*$)"


def grade(item, p):
    k = item["key"]
    t = k["template"]
    # outside the try: a fault in the key or the template is not the letter's
    block = _block(t, k["need"])
    try:
        if p["template"] != t:
            return False
        pa = (p["pay_after_acceptance"] or "").strip().lower()
        if k["pay"] is None:
            if pa not in ("", "null", "none", "n/a", "not applicable"):
                return False
        elif ENTRY.findall(pa) != [k["pay"].lower()]:
            return False
        L = _norm(p["letter"])
        # For text outside the block too: none of these may stand anywhere in the letter as the templates print them
        if any(
            b in L
            for b in (
                "[factual basis]",
                "[PAYEE]",
                "[DATE]",
                "[ITEM]",
                "[plain-language reason]",
                "[DESCRIPTION",
                "[YEAR MAKE MODEL]",
            )
        ):
            return False
        return bool(re.search(block, L))
    except Exception:
        return False
