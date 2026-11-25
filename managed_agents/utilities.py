"""Shared helpers for the cookbook notebooks.

Notebook 00 introduces two ways to consume a session's output:
polling `events.list` after the fact, and streaming events live
through `events.stream`. Both loops are written out inline in 00 so
readers see the literal API shapes the first time they meet them.

Once that introduction is done, every other notebook imports
`stream_until_end_turn` from this module instead of repeating the
loop. The helper is a direct lift of the streaming pattern shown in
notebook 00, printing `agent.message` text, marking each
`agent.tool_use`, and exiting when `session.status_idle` arrives
with `stop_reason.type == "end_turn"`.

The helper deliberately does not handle `requires_action`. Custom
tool notebooks (01 Part A and 05) drive the stream directly because
they need to respond to tool calls mid-turn, and their loops stay
inline.
"""

import io
import textwrap
import time
import zipfile

from anthropic import Anthropic


def wait_for_idle_status(client: Anthropic, session_id: str, max_wait: float = 5.0) -> None:
    """Poll until the session's server-side status field is `idle`.

    The `session.status_idle` event in the SSE stream can arrive
    slightly before `sessions.retrieve` reports `status == "idle"`,
    which causes an `archive()` call issued immediately after the
    stream exits to 400 with "cannot be archived while its status
    is running." This helper absorbs that race with a short poll.
    Call it after `stream_until_end_turn` (or after breaking out of
    an inline stream loop) and before `archive()`.
    """
    deadline = time.monotonic() + max_wait
    while time.monotonic() < deadline:
        if client.beta.sessions.retrieve(session_id).status == "idle":
            return
        time.sleep(0.25)


def stream_until_end_turn(client: Anthropic, session_id: str) -> None:
    """Stream a session's events and print until the agent finishes its turn.

    This is the streaming pattern from notebook 00, lifted into a
    helper so the later notebooks don't repeat it. The session emits
    `session.status_idle` any time it's waiting for input, both at
    end of turn and when a custom tool call needs a response, so we
    disambiguate with `stop_reason.type` and only exit on `end_turn`.

    After the stream exits we also wait for the server-side status
    to settle so an immediate `archive()` call doesn't race the
    state machine.
    """
    with client.beta.sessions.events.stream(session_id) as stream:
        for ev in stream:
            match ev.type:
                case "agent.message":
                    for block in ev.content:
                        if block.type == "text":
                            print(block.text, end="")
                case "agent.tool_use":
                    print(f"\n[{ev.name}]")
                case "session.status_idle" if ev.stop_reason and ev.stop_reason.type == "end_turn":
                    break
                case "session.status_terminated":
                    return
    wait_for_idle_status(client, session_id)


# Notebook 04 builds its repo fixture in-memory with the helper
# below rather than checking files into `example_data/`; the repo
# is small enough that the helper is more readable than a directory
# of stub files.


def make_unfamiliar_repo_zip() -> io.BytesIO:
    """Build an in-memory ZIP of a small repository with a stale doc.

    The repo is about 37 files laid out as microservices under
    `services/`, but `ARCHITECTURE.md` still describes the older
    monolithic layout. The grounding notebook uses this to show how
    an agent that trusts documentation without verifying it against
    the actual code will produce confidently wrong answers.
    """
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr(
            "ARCHITECTURE.md",
            textwrap.dedent("""\
            # Architecture (STALE, do not trust)

            The app is a monolith with three layers:
            - api/ for REST handlers
            - core/ for business logic
            - db/ for database access

            [Out of date. The real structure is microservices under
            services/. An agent that trusts this without reading the
            code will answer wrong.]
        """),
        )
        zf.writestr(
            "README.md",
            "# Widget Service\n\nSee ARCHITECTURE.md (possibly outdated).\n",
        )
        for svc in ["auth", "billing", "notifications", "widgets"]:
            zf.writestr(
                f"services/{svc}/main.py",
                f"# {svc} service entrypoint\ndef handle(): ...\n",
            )
            zf.writestr(f"services/{svc}/models.py", f"class {svc.title()}: ...\n")
            for i in range(6):
                zf.writestr(f"services/{svc}/util_{i}.py", f"def helper_{i}(): ...\n")
        for legacy in ["api", "core", "db"]:
            zf.writestr(f"{legacy}/.gitkeep", "")
    buf.seek(0)
    return buf
