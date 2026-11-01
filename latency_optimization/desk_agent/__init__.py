"""Acme desk agent: tasks, system prompt, simulated tools, and graders. Standard library only. See README.md in this folder."""

import json

# The names below are the package's public names, re-exported here: hence "noqa: F401".
from .grade import grade  # noqa: F401
from .prompt import NO_COMMENTARY, system_prompt  # noqa: F401
from .tools import DATA, RECORDERS, TOOL_NAMES, call_tool, is_terminal, tool_specs  # noqa: F401

TURN_CAP = 16  # model calls per episode
NUDGE_MESSAGE = "Use a tool. Finish by calling the task's recorder tool."
TURN_CAP_MESSAGE = "This was your last lookup. Call the recorder tool now with your best answer."


def load_items(split):
    """The tasks in data/<split>/. Fields a loop may read: id, type, level, cluster, claim_id, user_turn."""
    return json.loads((DATA / split / "items.json").read_text())


def first_turn(item, *, prefetch=False, big_pages=False):
    """The first user turn. With prefetch the application attaches what every task of this kind needs first: the claim record and, for a quote, page 1 of the estimate."""
    if not prefetch:
        return item["user_turn"]
    parts = [
        item["user_turn"],
        "Already looked up for you.",
        "get_claim:\n" + call_tool(item, "get_claim", {"claim_id": item["claim_id"]}),
    ]
    if item["type"] == "quote":
        parts.append(
            "get_estimate, page 1:\n"
            + call_tool(
                item, "get_estimate", {"claim_id": item["claim_id"], "page": 1}, big_pages=big_pages
            )
        )
    return "\n\n".join(parts)
