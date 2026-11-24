"""Helpers for CMA_dreaming_with_a_dynamic_workflow.ipynb: exporting one session to a transcript file,
following a session until its workflow run ends, counting what
was analyzed from the run's report and the platform's thread records, measuring where the run differed from what the
message asked, pricing, saving the run's records, deleting the organizer's placeholder files and cleaning up. The
session listing, the uploads, the tool lists, the environment, the agents.create and sessions.create calls and the
message that describes the work are in the notebook; the message's template and the agents' prompts are in
example_data/memory_distill/prompts/."""

import contextlib
import difflib
import itertools
import json
import os
import re
import stat
import tempfile
import threading
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path

import anthropic

# --- Transcript files ---------------------------------------------------------------------------

# The event types that make up a transcript. Status changes, usage spans and thinking markers are left out.
CONVERSATION_EVENTS = {
    "user.message",
    "agent.message",
    "agent.tool_use",
    "agent.tool_result",
    "agent.custom_tool_use",
    "user.custom_tool_result",
    "agent.mcp_tool_use",
    "agent.mcp_tool_result",
    "agent.thread_message_sent",
    "agent.thread_message_received",
    "session.thread_created",
    "session.error",
}
DROPPED_FIELDS = {"processed_at", "evaluation"}  # say nothing about what the agent did or saw
TRANSCRIPT_SUFFIXES = {".json", ".jsonl", ".md", ".txt", ".log"}
MAX_FILES_PER_SESSION = 500  # the platform's limit on file resources in one session


def compact_events(events):
    """The events of one thread that make up its transcript, as plain dicts. Each kept event keeps its content;
    only processed_at, evaluation and empty fields are dropped."""
    kept = []
    for event in events:
        ev = event if isinstance(event, dict) else event.model_dump(mode="json")
        if ev.get("type") in CONVERSATION_EVENTS:
            kept.append({k: v for k, v in ev.items() if k not in DROPPED_FIELDS and v is not None})
    return kept


def export_session(client, session_id, compact=True):
    """One Managed Agents session as plain JSON: the session, the agent it ran, and each thread's conversation
    events in order (status, usage and thinking events are left out; compact=False keeps every event as the
    API returns it). The top-level shape, log_format, session, agent and threads, is the one the agent
    security review cookbook's exports use."""
    sessions = client.beta.sessions
    session = sessions.retrieve(session_id)
    keep = compact_events if compact else (lambda evs: [e.model_dump(mode="json") for e in evs])
    threads = {t.id: t for t in sessions.threads.list(session_id)}
    exported = [
        {
            "id": t.id,
            "parent_thread_id": t.parent_thread_id,
            "agent_name": getattr(t.agent, "name", None) or getattr(t.agent, "type", "agent"),
            "events": keep(sessions.threads.events.list(t.id, session_id=session_id)),
        }
        for t in threads.values()
    ]
    if not any(t["parent_thread_id"] is None for t in exported):
        # No primary thread in the list: the session's own event list stands in for it.
        events = keep(sessions.events.list(session_id, order="asc"))
        exported.insert(
            0,
            {
                "id": "primary",
                "parent_thread_id": None,
                "agent_name": session.agent.name,
                "events": events,
            },
        )
    return {
        "log_format": "managed_agents_export",
        "session": session.model_dump(
            mode="json", include={"id", "title", "status", "created_at", "updated_at"}
        ),
        "agent": session.agent.model_dump(
            mode="json", include={"id", "version", "name", "description", "model"}
        ),
        "threads": exported,
    }


# Nothing taken from a session may pass for a label in the transcript file: a value on a label's own line is
# collapsed to one line, and a body line that starts like a label is indented by one space (the file's head
# then says so).
_TEXT_LABEL = re.compile(
    r"(SESSION |NOTE ABOUT THIS FILE:|=== |USER:|AGENT:|TOOL CALL |TOOL RESULT \(|THREAD MESSAGE |EVENT )"
)
_INDENTED_LABEL = re.compile(r" " + _TEXT_LABEL.pattern)
INDENTED_LINE_NOTE = (
    "NOTE ABOUT THIS FILE: A line indented by one space that starts like a label is part of the text above "
    "it, not a label."
)
# With ensure_ascii=False, json.dumps leaves these line-breaking code points raw (U+0085, U+2028, U+2029);
# escaped, a value written as one line of JSON stays one line for any reader.
_JSON_LINE_BREAKS = {0x85: "\\u0085", 0x2028: "\\u2028", 0x2029: "\\u2029"}


def _compact_json(value):
    """value as one line of JSON."""
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).translate(_JSON_LINE_BREAKS)


def _event_type(ev):
    """An event's type in dotted spelling; an underscored type from another exporter ("agent_tool_use") gives
    the dotted one ("agent.tool_use")."""
    kind = str(ev.get("type") or "")
    if "." in kind or "_" not in kind:
        return kind
    return kind.replace("_", ".", 1)


def _body(text):
    # splitlines also breaks at \r, \v, \f, U+0085, U+2028, U+2029 and the other code points a reader may
    # treat as a line break, so a label after any of them is indented too; each is written back as \n.
    return "\n".join(
        " " + line if _TEXT_LABEL.match(line) else line for line in (text.splitlines() or [""])
    )


def _one_line(value):
    """A value for a label line: its text with every whitespace run made a single space, so that nothing
    taken from the transcript can start a new line inside a label."""
    return " ".join(str(value).split())


def _tool_label(ev):
    """A tool call's name as the text labels it: server/name for an MCP tool."""
    name = _one_line(ev.get("name") or "") or "unknown tool"
    server = _one_line(ev.get("mcp_server_name") or ev.get("server_name") or "")
    return f"{server}/{name}" if server else name


def _blocks_text(content):
    """The text of a message's or tool result's content. A string stays as it is and None gives "". A block
    or a list gives each string or text block's text, a text document's title and data, a search result's
    title, source and text, and any other item as one line of JSON, joined by newlines."""
    if isinstance(content, str):
        return content
    if isinstance(content, dict):
        content = [content]
    if not isinstance(content, list):
        return "" if content is None else _compact_json(content)
    parts = []
    for block in content:
        kind = block.get("type", "text") if isinstance(block, dict) else None
        source = block.get("source") if isinstance(block, dict) else None
        if isinstance(block, str):
            parts.append(block)
        elif kind == "text" and isinstance(block.get("text"), str):
            parts.append(block["text"])
        elif (
            kind == "document"
            and isinstance(source, dict)
            and source.get("type") == "text"
            and isinstance(source.get("data"), str)
        ):
            title = block.get("title")
            parts.append((f"[document: {title}]\n" if title else "") + source["data"])
        elif kind == "search_result":
            inner = _blocks_text(block.get("content"))
            head = " ".join(str(block[k]) for k in ("title", "source") if block.get(k))
            parts.append((f"[search result: {head}]\n" if head else "") + inner)
        else:
            parts.append(_compact_json(block))
    return "\n".join(parts)


def render_text(export):
    """One session's export (export_session's dict) as the plain text of its transcript file: a line for the
    session, a header per thread and a labeled block per event, separated by blank lines. An event with no
    label of its own keeps its other fields as one line of JSON. Texts are written as they are, except that
    every kind of line break becomes a newline and a line that would read as a label is indented by one
    space."""
    session = export.get("session") if isinstance(export.get("session"), dict) else {}
    agent = export.get("agent") if isinstance(export.get("agent"), dict) else {}
    about = "; ".join(
        f"{label} {value}"
        for label, value in (
            ("agent", agent.get("name")),
            ("created", session.get("created_at")),
        )
        if value
    )
    title = _one_line(session.get("title") or "")
    out = [
        f"SESSION {_one_line(session.get('id') or '?')}: {title}".rstrip()
        + (f" ({_one_line(about)})" if about else "")
    ]
    if export.get("export_note"):
        out.append(f"NOTE ABOUT THIS FILE: {_one_line(export['export_note'])}")
    threads = export.get("threads")
    for thread in threads if isinstance(threads, list) else []:
        thread = thread if isinstance(thread, dict) else {}
        tid = _one_line(thread.get("id") or "")
        tid = "" if tid in ("", "primary") else f" {tid}"
        header = "primary thread" if thread.get("parent_thread_id") is None else "sub-thread"
        agent_name = _one_line(thread.get("agent_name") or "") or "agent"
        out.append(f"=== {header}{tid}: {agent_name} ===")
        names = {}  # tool call id: tool name, for the results' labels
        events = thread.get("events")
        for ev in events if isinstance(events, list) else []:
            if not isinstance(ev, dict):
                out.append(f"EVENT {_compact_json(ev)}")
                continue
            kind = _one_line(_event_type(ev))
            if kind == "user.message":
                out.append("USER:\n" + _body(_blocks_text(ev.get("content"))))
            elif kind == "agent.message":
                out.append("AGENT:\n" + _body(_blocks_text(ev.get("content"))))
            elif kind.endswith("tool_use"):
                name = _tool_label(ev)
                if ev.get("id") is not None:
                    names[str(ev["id"])] = name
                fields = ev.get("input")
                if isinstance(fields, dict):
                    body = "\n".join(
                        f"{k}:\n{v}"
                        if isinstance(v, str) and "\n" in v
                        else f"{k}: {v if isinstance(v, str) else _compact_json(v)}"
                        for k, v in fields.items()
                    )
                else:
                    body = _blocks_text(fields)
                out.append(f"TOOL CALL {name}:\n{_body(body)}")
            elif kind.endswith("tool_result"):
                ref = (
                    ev.get("tool_use_id")
                    or ev.get("mcp_tool_use_id")
                    or ev.get("custom_tool_use_id")
                )
                name = names.get(str(ref), "unknown tool") if ref is not None else "unknown tool"
                flag = " [error]" if ev.get("is_error") else ""
                out.append(
                    f"TOOL RESULT ({name}){flag}:\n" + _body(_blocks_text(ev.get("content")))
                )
            elif kind == "agent.thread_message_received":
                who = (
                    ev.get("from_agent_name")
                    or ev.get("from_display_name")
                    or ev.get("from_session_thread_id")
                )
                label = (
                    f"THREAD MESSAGE RECEIVED from {_one_line(who)}"
                    if who
                    else "THREAD MESSAGE RECEIVED"
                )
                out.append(f"{label}:\n" + _body(_blocks_text(ev.get("content"))))
            elif kind == "agent.thread_message_sent":
                who = (
                    ev.get("to_agent_name")
                    or ev.get("to_display_name")
                    or ev.get("to_session_thread_id")
                )
                label = f"THREAD MESSAGE SENT to {_one_line(who)}" if who else "THREAD MESSAGE SENT"
                out.append(f"{label}:\n" + _body(_blocks_text(ev.get("content"))))
            else:
                rest = {k: v for k, v in ev.items() if k not in ("type", "id")}
                out.append(f"EVENT {kind}: {_compact_json(rest)}" if rest else f"EVENT {kind}")
    text = "\n\n".join(out) + "\n"
    if any(_INDENTED_LABEL.match(line) for line in text.splitlines()):
        out.insert(1, INDENTED_LINE_NOTE)
        text = "\n\n".join(out) + "\n"
    return text


@dataclass
class TranscriptFile:
    path: Path
    name: str  # the file name the agents will see
    size: int  # bytes


# A transcript file's name goes into the message to the lead agent as part of its mount path, so only
# plain names are taken: ASCII letters, digits, ".", "_" and "-", starting with a letter, a digit
# or "_".
SAFE_NAME = re.compile(r"[A-Za-z0-9_][A-Za-z0-9._-]*")
NAME_RULE = 'ASCII letters, digits, ".", "_" and "-", starting with a letter, a digit or "_"'


def some_names(names, most=5):
    """Up to most names, quoted, then "and N more"."""
    shown = ", ".join(map(repr, names[:most]))
    return shown + (f" and {len(names) - most} more" if len(names) > most else "")


def transcript_files(folder):
    """(files, skipped): the transcript files directly in a folder, sorted by name (every non-empty .json,
    .jsonl, .md, .txt or .log file), and what was skipped, with the reason. Raises ValueError naming the
    transcript files whose names are not plain (NAME_RULE): a name goes into the message the lead agent
    reads, so rename such a file rather than have it skipped unseen."""
    files, skipped, unsafe = [], [], []
    for p in sorted(Path(folder).iterdir()):
        if p.is_dir():
            skipped.append((p.name, "a folder"))
        elif p.suffix.lower() not in TRANSCRIPT_SUFFIXES:
            skipped.append((p.name, f"not one of {' '.join(sorted(TRANSCRIPT_SUFFIXES))}"))
        elif not SAFE_NAME.fullmatch(p.name):
            unsafe.append(p.name)
        elif p.stat().st_size == 0:
            skipped.append((p.name, "empty"))
        else:
            files.append(TranscriptFile(p, p.name, p.stat().st_size))
    if unsafe:
        raise ValueError(
            f"Rename {plural(len(unsafe), 'transcript file')} in {display_path(folder)}: "
            f"{some_names(unsafe)}. A transcript's file name goes into the message the lead agent reads, "
            f"so it may use only {NAME_RULE}."
        )
    return files, skipped


@dataclass
class Uploaded:
    file_id: str
    name: str
    mount_path: (
        str  # as given in the session's resources; the sandbox sees it under /mnt/session/uploads
    )
    size: int


def sandbox_path(mount_path):
    """Where a file resource with this mount_path appears in the session's sandbox."""
    return "/mnt/session/uploads" + mount_path


def delete_uploads(client, uploaded):
    """Delete the uploaded copies of the transcripts. One that can't be deleted is printed and left."""
    for u in uploaded:
        remove(
            f"delete file {u.file_id} ({u.name})",
            client.files.delete,
            u.file_id,
            later=f"client.files.delete({u.file_id!r})",
        )


# --- The records folder -------------------------------------------------------------------------


def private_dir(path):
    """Create a folder (and any missing parents) readable only by you, mode 0o700, and return it. A folder that
    already exists keeps its mode."""
    path = Path(path)
    for folder in reversed([p for p in (path, *path.parents) if not p.exists()]):
        folder.mkdir(mode=0o700, exist_ok=True)
        os.chmod(folder, 0o700)  # mkdir's mode is filtered by the umask
    return path


def private_write(path, text):
    """Write a file readable only by you, mode 0o600, creating its folder privately if it is new. A symbolic
    link at the path is not followed and a file that isn't yours is not written into: both raise ValueError."""
    path = Path(path)
    private_dir(path.parent)
    flags = os.O_WRONLY | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(path, flags, 0o600)
    except OSError as why:
        if os.path.islink(path):
            raise ValueError(f"{path} is a link; remove it or use another folder.") from why
        raise
    found = os.fstat(fd)
    if not stat.S_ISREG(found.st_mode) or (hasattr(os, "getuid") and os.getuid() != found.st_uid):
        os.close(fd)
        raise ValueError(f"{path} is not a file of yours; remove it or use another folder.")
    if hasattr(os, "fchmod"):
        os.fchmod(fd, 0o600)
    os.ftruncate(fd, 0)
    with os.fdopen(fd, "w", encoding="utf-8", errors="backslashreplace") as handle:
        handle.write(text)


def records_root():
    """The folder runs are recorded under: COOKBOOK_RECORDS_DIR if set, else a folder of your own under
    the system's temporary directory (/tmp/memory_distill-<uid>/runs on Linux), which most systems clear on
    restart. Either way it is meant to be outside any repository. The temporary folder is created with mode
    0o700 (and set back to it if it was wider); if a file, a link or another user's folder is already at that
    path, ValueError says to set COOKBOOK_RECORDS_DIR (or to remove the file or link, if it is yours)."""
    configured = os.getenv("COOKBOOK_RECORDS_DIR")
    if configured:
        return Path(configured)
    uid = os.getuid() if hasattr(os, "getuid") else os.getlogin()
    root = Path(tempfile.gettempdir()) / f"memory_distill-{uid}"
    if not os.path.lexists(root):
        root.mkdir(mode=0o700)
    found = root.lstat()  # the path itself: a link planted there is not followed
    mine = not hasattr(os, "getuid") or found.st_uid == os.getuid()
    if not stat.S_ISDIR(found.st_mode) or not mine:
        raise ValueError(
            f"{root} already exists and is not a folder you own (it is a file, a link or "
            "another user's folder). Set COOKBOOK_RECORDS_DIR to a private folder of yours, or "
            "remove the file or link if it is yours."
        )
    if hasattr(os, "getuid") and found.st_mode & 0o077:
        os.chmod(root, 0o700)  # POSIX: keep the folder private
    return root / "runs"


def new_run_dir():
    """A new time-stamped folder under records_root() for this run's records (not created yet)."""
    return records_root() / datetime.now(UTC).strftime("%Y-%m-%dT%H-%M-%SZ")


def display_path(path):
    """A path as printed: ~/... when it is under your home directory, in full when it is under the system's
    temporary directory (the records' default place; on Linux and macOS that path holds no name of yours),
    otherwise just its last two components, so a run on a server doesn't print that server's paths."""
    path = Path(path)
    try:
        return "~/" + str(path.relative_to(Path.home()))
    except ValueError:
        pass
    if path.is_relative_to(tempfile.gettempdir()):
        return str(path)
    return str(Path("...") / Path(*path.parts[-2:]))


# --- Memory stores ----------------------------------------------------------------------------------


def fill(template, **values):
    """A prompt template with each {name} placeholder replaced by its value, in one pass. Only the named
    placeholders are touched, so the JSON braces elsewhere in the templates survive (which str.format would not
    allow), and a placeholder-like string inside a value is left as it is."""
    return re.sub(
        r"\{(\w+)\}",
        lambda m: str(values[m.group(1)]) if m.group(1) in values else m.group(0),
        template,
    )


def list_memories(client, store_id, path_prefix="/"):
    """Every memory in a store under path_prefix, without content, in the server's order."""
    listing = client.beta.memory_stores.memories.list(store_id, path_prefix=path_prefix, limit=100)
    return [m for m in listing if getattr(m, "type", "memory") == "memory"]


def memory_text(client, store_id, path):
    """The content of the memory file at path in a store ("" when there is no such file)."""
    folder = path.rpartition("/")[0] + "/"  # the listing takes a folder prefix ending in "/"
    for m in list_memories(client, store_id, path_prefix=folder):
        if m.path == path:
            full = client.beta.memory_stores.memories.retrieve(
                m.id, memory_store_id=store_id, view="full"
            )
            return full.content or ""
    return ""


def download_store(client, store_id, out_dir):
    """Write every memory of a store into out_dir, one file per memory at its path, and return the paths. A
    memory whose path would land outside out_dir is printed and skipped."""
    out_dir = private_dir(out_dir).resolve()
    written = []
    for m in list_memories(client, store_id):
        target = (out_dir / m.path.lstrip("/")).resolve()
        if out_dir not in target.parents:
            print(f"Skipped {m.path}: it would be written outside {out_dir.name}/")
            continue
        full = client.beta.memory_stores.memories.retrieve(
            m.id, memory_store_id=store_id, view="full"
        )
        private_write(target, full.content or "")
        written.append(target)
    return written


def written_by_session(client, store_id, session_id, limit=2000):
    """The memory versions in a store that a given session wrote, newest first (at most limit): each create,
    change or delete its agents made through the store's mount."""
    listing = client.beta.memory_stores.memory_versions.list(
        store_id, session_id=session_id, limit=100
    )
    return list(itertools.islice(listing, limit))


# --- Prices and the estimate ------------------------------------------------------------------------

# US dollars per million tokens at list price, from https://platform.claude.com/docs/en/about-claude/pricing.
# cache_write is the 5-minute rate; a 1-hour cache write costs twice the input price. Prices change: check the
# page before relying on a figure. These feed the estimate; what a run actually cost is read from the platform.
PRICES = {
    "claude-opus-5-5": {"input": 4.00, "cache_write": 5.00, "cache_read": 0.20, "output": 20.00},
    "claude-sonnet-5-5": {"input": 2.00, "cache_write": 2.50, "cache_read": 0.10, "output": 10.00},
    "claude-haiku-5-5": {"input": 0.10, "cache_write": 0.125, "cache_read": 0.01, "output": 0.50},
}
# A Claude Haiku 5.5 request whose prompt is over 100,000 tokens pays these instead (same page, "Long context
# pricing"). The estimate applies them to an analyzer whose transcript would take its context past that size.
LONG_PROMPT_PRICES = {
    "claude-haiku-5-5": {
        "over": 100_000,
        "input": 0.50,
        "cache_write": 0.625,
        "cache_read": 0.05,
        "output": 2.50,
    }
}
DEFAULT_PRICED_AS = "claude-opus-5-5"
SESSION_HOUR_USD = 0.08  # session running time, per hour

# What the estimate assumes about one analyzer's work: rough figures, calibrated once against a run of this
# notebook's example data (eleven files) and rounded. Analyzers read the memory written so far and read back what
# they write, so most of their tokens are cache reads; they also think, which counts as output. After a run the
# notebook prints what the run used beside the estimate, so you can adjust these for your own transcripts.
CHARS_PER_TOKEN = 3.0  # rough: transcripts are mostly code and tool output
# Model requests one analyzer makes: reading pages, grep, writes and read-backs.
REQUESTS_PER_ANALYZER = 24
# System prompt, tool definitions and task, present on every request.
ANALYZER_FIXED_TOKENS = 8_000
# Tokens of existing memory and tool output an analyzer reads, and tokens it writes (thinking included), as
# shares of its transcript's tokens.
MEMORY_READ_SHARE = 1.5
OUTPUT_SHARE = 1.2
MIN_OUTPUT_TOKENS = 5_000
LEAD_TOKENS = {
    "cache_write": 20_000,
    "cache_read": 60_000,
    "output": 4_000,
}  # writing and watching one run
# The organizer reads the whole store and writes about as many tokens as the store holds (rewrites and
# thinking). The store's size is guessed from the transcripts (memory comes out at roughly a fifth of their
# tokens). Calibrated on one run over the examples; rough, like the rest; a store built from many
# runs is larger than one run's transcripts.
STORE_SHARE = 0.2
# Its context, store-sized, is written to the cache a few times as it grows,
ORGANIZER_CACHE_WRITES = 3
# and re-read from the cache on each of its several dozen tool calls.
ORGANIZER_READ_PASSES = 40
ORGANIZER_MIN_TOKENS = 20_000


def prices_of(model, prompt_tokens=0):
    """(prices, note): the list prices for a model at this prompt size, or DEFAULT_PRICED_AS's with a note
    saying so."""
    long_prices = LONG_PROMPT_PRICES.get(model)
    if long_prices and prompt_tokens > long_prices["over"]:
        return long_prices, ""
    if model in PRICES:
        return PRICES[model], ""
    return PRICES[DEFAULT_PRICED_AS], (
        f"{model} has no price in memory_distill_utils.PRICES, so the estimate uses {DEFAULT_PRICED_AS}'s "
        "prices for it and may be off."
    )


def dollars(tokens, prices):
    """The list price of {input, cache_write, cache_write_1h, cache_read, output} token counts."""
    usd_amount = sum(
        tokens.get(k, 0) * prices[k] for k in ("input", "cache_write", "cache_read", "output")
    )
    usd_amount += tokens.get("cache_write_1h", 0) * prices["input"] * 2
    return usd_amount / 1e6


def usd(amount):
    """A dollar amount for printing, such as $1,234.56."""
    return f"${amount:,.2f}"


def plural(count, word, many=None):
    """'1 file', '2 files': the count with the word in the singular or the plural (many, or word + 's')."""
    return f"{count:,} {word if count == 1 else (many or word + 's')}"


def analyzer_tokens(size_bytes):
    """The token counts the estimate assumes for one analyzer on a transcript of this size. The transcript, the
    memory it reads and what it writes enter the context once (cache writes); every later request re-reads the
    context so far (cache reads), taken as half the final context on average."""
    transcript = size_bytes / CHARS_PER_TOKEN
    context = ANALYZER_FIXED_TOKENS + transcript * (1 + MEMORY_READ_SHARE)
    output = max(MIN_OUTPUT_TOKENS, transcript * OUTPUT_SHARE)
    return {
        "cache_write": context + output,
        "cache_read": REQUESTS_PER_ANALYZER * (context + output) / 2,
        "output": output,
    }


def organizer_tokens(total_transcript_bytes):
    """Rough token counts for the one organizer pass: the store it reads, several times over, and rewrites."""
    store = max(ORGANIZER_MIN_TOKENS, int(total_transcript_bytes / CHARS_PER_TOKEN * STORE_SHARE))
    return {
        "cache_write": store * ORGANIZER_CACHE_WRITES,
        "cache_read": store * ORGANIZER_READ_PASSES,
        "output": store,
    }


def estimate_cost(files, analyzer_model, lead_model, organizer_model=None):
    """(usd, lines): a rough list-price estimate for one run over these transcript files, and the lines that
    explain it: the analyzers, the lead agent and, when organizer_model is given, the organizer's pass. It
    is built from file sizes and the assumptions above, not from a measurement of your data. With no files it
    returns (0.0, ["0 transcripts: nothing to estimate."])."""
    if not files:
        return 0.0, ["0 transcripts: nothing to estimate."]
    notes, per_file = [], []
    for f in files:
        tokens = analyzer_tokens(f.size)
        prices, note = prices_of(analyzer_model, prompt_tokens=tokens["cache_write"])
        notes.append(note)
        per_file.append(dollars(tokens, prices))
    analyzers = sum(per_file)
    lead_prices, note = prices_of(lead_model)
    notes.append(note)
    lead = dollars(LEAD_TOKENS, lead_prices)
    size = sum(f.size for f in files)
    organizer, organizer_part = 0.0, ""
    if organizer_model:
        organizer_prices, note = prices_of(organizer_model)
        notes.append(note)
        organizer = dollars(organizer_tokens(size), organizer_prices)
        organizer_part = f", organizer on {organizer_model} {usd(organizer)}"
    total = analyzers + lead + organizer
    lines = [
        f"{plural(len(files), 'transcript')}, {size / 1024:,.0f} KB in all "
        f"(about {round(size / CHARS_PER_TOKEN, -3 if size / CHARS_PER_TOKEN >= 10_000 else 0):,.0f} tokens).",
        f"Estimated list price {usd(total)}: analyzers on {analyzer_model} {usd(analyzers)} (most expensive "
        f"file {usd(max(per_file, default=0))}), lead agent on {lead_model} {usd(lead)}{organizer_part}. "
        f"Session running time is extra, at {usd(SESSION_HOUR_USD)} an hour.",
    ]
    lines += sorted({n for n in notes if n})
    return total, lines


def usage_tokens(usage):
    """A thread's or session's usage object as token counts: input, cache_write (5-minute), cache_write_1h,
    cache_read and output."""
    counts = {"input": 0, "cache_write": 0, "cache_write_1h": 0, "cache_read": 0, "output": 0}
    if usage is None:
        return counts
    u = usage if isinstance(usage, dict) else usage.model_dump(mode="json")
    counts["input"] = int(u.get("input_tokens") or 0)
    counts["cache_read"] = int(u.get("cache_read_input_tokens") or 0)
    counts["output"] = int(u.get("output_tokens") or 0)
    creation = u.get("cache_creation") if isinstance(u.get("cache_creation"), dict) else {}
    counts["cache_write_1h"] = int(creation.get("ephemeral_1h_input_tokens") or 0)
    five_minute = creation.get("ephemeral_5m_input_tokens")
    if five_minute is None:  # older shape: one total for all cache writes
        five_minute = (u.get("cache_creation_input_tokens") or 0) - counts["cache_write_1h"]
    counts["cache_write"] = max(0, int(five_minute or 0))
    return counts


def model_id(model):
    """A model id from an agent's model field, which the platform returns as a config object with an id."""
    return getattr(model, "id", model) if model else None


def thread_model(thread):
    """The model id that the thread's agent snapshot names, or None."""
    return model_id(getattr(thread.agent, "model", None))


def request_usages(export):
    """{thread id: [token counts of each model request]} from a session export's span.model_request_end
    events; threads with no such event are left out. cache_write counts 5-minute and 1-hour cache writes
    together: the events do not split them (a thread's totals do)."""
    per_thread = {}
    for thread in (export or {}).get("threads") or []:
        requests = []
        for event in thread.get("events") or []:
            if event.get("type") != "span.model_request_end":
                continue
            u = event.get("model_usage") or event.get("usage") or {}
            requests.append(
                {
                    "input": int(u.get("input_tokens") or 0),
                    "cache_write": int(u.get("cache_creation_input_tokens") or 0),
                    "cache_read": int(u.get("cache_read_input_tokens") or 0),
                    "output": int(u.get("output_tokens") or 0),
                }
            )
        if thread.get("id") and requests:
            per_thread[thread["id"]] = requests
    return per_thread


def priced_by_request(requests, model):
    """(usd, long_requests): each request priced on its own, at LONG_PROMPT_PRICES when its prompt (input +
    cache_write + cache_read) is over the model's "over" threshold, else at PRICES; long_requests counts the
    former."""
    total, long_requests = 0.0, 0
    threshold = (LONG_PROMPT_PRICES.get(model) or {}).get("over")
    for r in requests:
        prompt = r["input"] + r["cache_write"] + r["cache_read"]
        if threshold is not None and prompt > threshold:
            long_requests += 1
        prices, _ = prices_of(model, prompt_tokens=prompt)
        total += dollars(r, prices)
    return total, long_requests


def requests_match_totals(requests, tokens):
    """True when the requests' summed tokens equal the thread's own totals (input, all cache writes, cache
    reads, output), i.e. the export holds every request the thread's usage counts."""
    sums = {
        k: sum(r[k] for r in requests) for k in ("input", "cache_write", "cache_read", "output")
    }
    return (
        sums["input"] == tokens["input"]
        and sums["cache_write"] == tokens["cache_write"] + tokens["cache_write_1h"]
        and sums["cache_read"] == tokens["cache_read"]
        and sums["output"] == tokens["output"]
    )


def usage_rows(threads, default_model, export=None):
    """One row per thread: agent name, model, status, token counts, the platform's own list_cost (tokens at
    public list rates, rounded per thread; None until the thread has been idle once) and priced_usd, the same
    tokens priced from PRICES for comparison: request by request (priced_by_request) when the session export
    holds that thread's requests and they add up to its totals, else from its totals at standard prices.
    priced_basis says which, requests and long_prompt_requests count them. No model named: default_model."""
    per_request = request_usages(export)
    rows = []
    for t in threads:
        model = thread_model(t) or default_model
        tokens = usage_tokens(t.usage)
        list_cost = getattr(t.usage, "list_cost", None) if t.usage else None
        requests = per_request.get(t.id)
        standard, _ = prices_of(model)
        if requests and requests_match_totals(requests, tokens):
            priced, long_requests = priced_by_request(requests, model)
            # The events give one cache-write total; the thread's totals say how much of it was 1-hour writes,
            # which cost twice the input price instead of the 5-minute write price. The surcharge is added at
            # standard prices (the events don't say which requests made them), so it is a lower bound.
            priced += (
                tokens["cache_write_1h"] * (2 * standard["input"] - standard["cache_write"]) / 1e6
            )
            basis = "per request"
        else:
            priced, long_requests = dollars(tokens, standard), 0
            if export is None:
                basis = "totals: no session export"
            elif not requests:
                basis = "totals: no requests for this thread in the session export"
            else:
                basis = "totals: the export's requests do not add up to the thread's usage"
        rows.append(
            {
                "thread": t.id,
                "agent": getattr(t.agent, "name", None) or getattr(t.agent, "type", ""),
                "model": model,
                "status": t.status,
                "workflow_run_id": t.workflow_run_id,
                **tokens,
                "list_cost_usd": int(list_cost.amount) / 100 if list_cost else None,
                "priced_usd": priced,
                "priced_basis": basis,
                "requests": len(requests) if basis == "per request" else None,
                "long_prompt_requests": long_requests,
                "active_seconds": getattr(t.usage, "active_seconds", None) if t.usage else None,
            }
        )
    return rows


def not_yet_reported(n):
    """The note added after a platform list price when n threads have no list cost yet (empty when n is 0)."""
    return f" (leaves out {plural(n, 'thread')} not yet reported)" if n else ""


def usage_summary(rows):
    """Totals over usage_rows, per agent name and overall, as printable lines. "list" is the platform's figure,
    "priced" the same tokens at the prices in PRICES. The last line says how many model requests were priced at
    long-prompt prices and how many threads, if any, were priced from their totals instead."""
    lines, by_agent = [], {}
    for r in rows:
        a = by_agent.setdefault(
            r["agent"],
            {"threads": 0, "list": 0.0, "priced": 0.0, "out": 0, "in": 0, "unreported": 0},
        )
        a["threads"] += 1
        a["list"] += r["list_cost_usd"] or 0.0
        a["unreported"] += int(r["list_cost_usd"] is None)
        a["priced"] += r["priced_usd"]
        a["out"] += r["output"]
        a["in"] += r["input"] + r["cache_write"] + r["cache_write_1h"] + r["cache_read"]
    for name, a in by_agent.items():
        lines.append(
            f"{name:>20}: {plural(a['threads'], 'thread'):>10}, {a['in']:>12,} tokens in, {a['out']:>10,} out, "
            f"{usd(a['list'])} by the platform's meter{not_yet_reported(a['unreported'])}, "
            f"{usd(a['priced'])} at this notebook's prices"
        )
    total_list = sum((r["list_cost_usd"] or 0.0) for r in rows)
    unreported = sum(1 for r in rows if r["list_cost_usd"] is None)
    total_priced = sum(r["priced_usd"] for r in rows)
    requests = sum((r.get("requests") or 0) for r in rows)
    long_requests = sum((r.get("long_prompt_requests") or 0) for r in rows)
    from_totals = sum(1 for r in rows if r.get("priced_basis") != "per request")
    if rows and all(r.get("priced_basis") == "totals: no session export" for r in rows):
        basis = "no session export, so each thread is priced from its totals at standard prices"
    elif from_totals == len(rows):
        basis = (
            "no matching per-request usage in the session export, so each thread is priced from its totals "
            "at standard prices"
        )
    else:
        basis = (
            f"{long_requests} of {plural(requests, 'model request')} priced at long-context rates"
        )
        if from_totals:
            basis += (
                f"; {plural(from_totals, 'thread')} without matching requests in the session export "
                "priced from totals at standard prices"
            )
    lines.append(
        f"{'all threads':>20}: {usd(total_list)} by the platform's meter{not_yet_reported(unreported)}, "
        f"{usd(total_priced)} at this notebook's prices "
        f"(token prices only, not session running time; {basis})"
    )
    return lines


# --- Following the session until the work is done -------------------------------------------------


@dataclass
class RunRecord:
    """What the event stream showed of one workflow run. Times are seconds since the message was sent."""

    id: str
    name: str = ""
    description: str | None = None
    phases: dict = field(default_factory=dict)  # phase id: phase name, from workflow_run.created
    phase_log: list = field(default_factory=list)  # (seconds, "started" or "ended", phase name)
    result: dict | None = None  # from workflow_run.status_ended
    threads: dict = field(
        default_factory=dict
    )  # thread id: {"agent": name, "started": s, "ended": s}
    errors: list = field(default_factory=list)


@dataclass
class Followed:
    """What follow() saw: every run by id, why it stopped, the agent's last message, how long it took, the tool
    confirmations it denied, and the session errors it saw."""

    runs: dict = field(default_factory=dict)
    stop: str = ""
    request: str = ""  # the user message that started the work, as the session recorded it
    last_message: str = ""
    seconds: float = 0.0
    # (thread id, tool name or event id) of each call answered with deny
    denied: list = field(default_factory=list)
    # (error type, message) of each session.error; those the server said it was retrying go in retried
    errors: list = field(default_factory=list)
    retried: list = field(default_factory=list)


STOP_REASONS = {
    "idle": "the run ended and the lead agent replied",
    "budget_reached": "the session reached BUDGET_USD and stopped; the store holds what was written before "
    'that. For a complete run, raise BUDGET_USD and, after "Clean up", run the dream again from '
    '"Create the store"',
    "retries_exhausted": "the agent's turn failed after retries; the session errors are printed above",
    "refusal": "the model declined the request",
    "terminated": "the session was terminated; any session errors are printed above",
    "timeout": 'this notebook stopped waiting; the run may still be going ("Clean up" stops it; to '
    'wait longer, raise RUN_TIMEOUT_MINUTES and start again from "Create the store")',
}


def describe_stop(stop):
    """A stop code from follow() in words."""
    return STOP_REASONS.get(stop, stop)


def text_of(content):
    """The text of a message's content blocks (objects or plain dicts)."""
    parts = []
    for b in content or []:
        kind = b.get("type") if isinstance(b, dict) else getattr(b, "type", "")
        if kind == "text":
            parts.append(b.get("text", "") if isinstance(b, dict) else b.text)
    return "".join(parts)


def deny_event(event_id):
    """The event that denies one tool call waiting for confirmation."""
    return {
        "type": "user.tool_confirmation",
        "tool_use_id": event_id,
        "result": "deny",
        "deny_message": "This run is unattended; calls that need confirmation are denied.",
    }


SILENT_STREAM_S = 15 * 60  # reconnect if a connection has sent nothing at all for this long


def follow(
    client, session_id, message=None, timeout_s=6 * 3600, quiet=False, on_event=None, out=None
):
    """Send message as a user message (when it is None, the caller has sent it: read the session's
    event list first), then follow the event stream, reconnecting as needed, until every workflow
    run it saw start has ended and the session is idle with end_turn. Unless quiet, prints
    progress; denies tool calls that wait for confirmation. Returns a Followed whose stop is "idle",
    budget_reached, retries_exhausted, refusal, terminated or timeout (after timeout_s). A string
    returned by on_event(event) stops it with that stop; pass your own Followed as out to keep what
    was seen if the call is interrupted."""
    events = client.beta.sessions.events
    out = Followed() if out is None else out
    seen, answered, pending = set(), set(), {}
    started = time.monotonic()
    last_retry = {"at": 0.0}
    deadline = started + timeout_s
    grace = {
        "until": None
    }  # after retries_exhausted with no run open, wait this long for a new turn

    def say(text):
        if not quiet:
            print(f"[{time.monotonic() - started:5.0f}s] {text}", flush=True)

    def now():
        return round(time.monotonic() - started)

    def run_of(ev):
        return out.runs.setdefault(ev.workflow_run_id, RunRecord(ev.workflow_run_id))

    def deny(event_id, thread_id, label):
        if event_id in answered:
            return
        try:
            events.send(session_id, events=[deny_event(event_id)])
        except anthropic.APIError as exc:
            # A 400 can mean the call's own event hasn't reached this stream yet (or that it was already
            # answered); other errors are transient. The id stays pending and is tried again on later events.
            pending[event_id] = (thread_id, label)
            say(f"could not deny the {label} call yet: {exc}")
        else:
            answered.add(event_id)
            pending.pop(event_id, None)
            out.denied.append((thread_id, label))

    def retry_pending():
        if pending and time.monotonic() - last_retry["at"] > 10:
            last_retry["at"] = time.monotonic()
            for event_id, (thread_id, label) in list(pending.items()):
                deny(event_id, thread_id, label)

    def handle(ev):
        if ev.id in seen:
            return None
        seen.add(ev.id)
        retry_pending()
        if on_event:
            stop = on_event(ev)
            if stop:
                return stop
        kind = ev.type
        if kind == "user.message" and not out.request:
            out.request = text_of(getattr(ev, "content", None))
        if kind == "workflow_run.created":
            run = run_of(ev)
            run.name, run.description = ev.name, ev.description
            run.phases = {p.id: p.name for p in ev.phases}
            say(f"run started: {ev.name!r}, phases {list(run.phases.values())}")
        elif kind in ("workflow_run.phase_started", "workflow_run.phase_ended"):
            run = run_of(ev)
            name = run.phases.get(ev.workflow_run_phase_id, ev.workflow_run_phase_id)
            verb = kind.rsplit("_", 1)[1]
            run.phase_log.append((now(), verb, name))
            say(f"phase {verb}: {name}")
        elif kind == "workflow_run.status_ended":
            run = run_of(ev)
            run.result = ev.result.model_dump(mode="json")
            error = run.result.get("error") or {}
            detail = f" ({error.get('type')}: {error.get('message')})" if error else ""
            say(f"run ended: {run.result.get('type')}{detail}")
        elif kind == "workflow_run.status_idle":
            say("run paused; the event doesn't say why (a session at its budget is one cause)")
        elif kind == "workflow_run.error":
            error = f"{ev.error.type}: {ev.error.message}"
            if ev.workflow_run_id:
                run_of(ev).errors.append(error)
            out.errors.append(("workflow_run.error", error))
            say(f"workflow error: {error}")
        elif kind == "session.thread_created" and getattr(ev, "workflow_run_id", None):
            run = run_of(ev)
            run.threads[ev.session_thread_id] = {
                "agent": ev.agent_name,
                "started": now(),
                "ended": None,
            }
            counts = {}
            for t in run.threads.values():
                counts[t["agent"]] = counts.get(t["agent"], 0) + 1
            shown = ", ".join(plural(c, f"{n} thread") for n, c in counts.items())
            say(f"thread started: {ev.agent_name} ({shown} so far)")
        elif kind in ("session.thread_status_idle", "session.thread_status_terminated"):
            thread_id = getattr(ev, "session_thread_id", None)
            stop_reason = getattr(ev, "stop_reason", None)
            if getattr(stop_reason, "type", None) == "requires_action":
                # A run thread waits for a confirmation: deny it; the thread has not ended.
                for event_id in getattr(stop_reason, "event_ids", None) or []:
                    deny(event_id, thread_id, event_id)
            else:
                for run in out.runs.values():
                    if thread_id in run.threads and run.threads[thread_id]["ended"] is None:
                        run.threads[thread_id]["ended"] = now()
        elif kind in ("agent.tool_use", "agent.mcp_tool_use"):
            # A tool whose permission policy asks for confirmation waits on your client; nobody is watching
            # this run, so the call is denied. A run thread's waiting call arrives on this stream too.
            if getattr(ev, "evaluated_permission", None) == "ask":
                deny(ev.id, getattr(ev, "session_thread_id", None), getattr(ev, "name", ev.id))
        elif kind == "agent.message":
            out.last_message = text_of(ev.content)
        elif kind == "session.error":
            error = getattr(ev, "error", None)
            entry = (getattr(error, "type", ""), getattr(error, "message", ""))
            retrying = getattr(getattr(error, "retry_status", None), "type", None) == "retrying"
            (out.retried if retrying else out.errors).append(entry)
            say(f"session error{' (server retrying)' if retrying else ''}: {entry[0]} {entry[1]}")
        elif kind == "session.status_running":
            grace["until"] = None  # the server started another turn
        elif kind == "session.status_idle":
            reason = getattr(ev.stop_reason, "type", None)
            open_runs = [r for r in out.runs.values() if r.result is None]
            if reason == "requires_action":
                # Deny whatever is still waiting, in case its tool_use event was missed.
                for event_id in getattr(ev.stop_reason, "event_ids", None) or []:
                    deny(event_id, None, event_id)
            elif reason == "budget_reached":
                return reason
            elif reason in ("end_turn", "refusal") and not open_runs:
                return "idle" if reason == "end_turn" else reason
            elif reason == "retries_exhausted" and not open_runs:
                # The server may start one more turn by itself (a run ended unread); give it two minutes.
                grace["until"] = time.monotonic() + 120
            # With a run still open, keep reading: the agent gets another turn when the run ends.
        elif kind in ("session.status_terminated", "session.deleted"):
            return "terminated"
        return None

    def finish(stop):
        out.stop, out.seconds = stop, time.monotonic() - started
        return out

    # With no message to send, the first connection reads the session's events from the start.
    sent, last_seen, failures = message is None, None, 0
    while time.monotonic() < deadline:
        fired = threading.Event()
        timer = None
        # One connection is held until the work is done. A timer closes it at the deadline, at the end of a grace
        # period, or half a minute after a denial failed, so that it can be tried again. The read timeout only
        # catches a connection that has sent nothing at all for a quarter of an hour. On a disconnect, an error
        # or that timeout it reconnects and catches up from the event list.
        wake = min(deadline, grace["until"] or deadline)
        if pending:  # a denial failed: reopen within half a minute to try it again
            wake = min(wake, time.monotonic() + 30)
        read_timeout = min(max(5.0, wake - time.monotonic()), SILENT_STREAM_S) + 5
        try:
            retry_pending()
            with events.stream(session_id, timeout=read_timeout) as stream:

                def cut(stream=stream, fired=fired):
                    fired.set()
                    with contextlib.suppress(Exception):
                        stream.close()

                timer = threading.Timer(max(0.0, wake - time.monotonic()), cut)
                timer.daemon = True
                timer.start()
                if sent:
                    # Catch up on what arrived while disconnected; handle() skips what it has seen.
                    query = {"order": "asc"}
                    if last_seen is not None:
                        query["created_at_gte"] = last_seen - timedelta(minutes=1)
                    missed = events.list(session_id, **query)
                else:
                    content = [{"type": "text", "text": message}]
                    events.send(session_id, events=[{"type": "user.message", "content": content}])
                    sent, missed = True, []
                for ev in itertools.chain(missed, stream):
                    if getattr(ev, "processed_at", None):
                        last_seen = (
                            ev.processed_at
                            if last_seen is None
                            else max(last_seen, ev.processed_at)
                        )
                    stop = handle(ev)
                    if stop:
                        return finish(stop)
                    if time.monotonic() > deadline:
                        return finish("timeout")
                    # A connection that stays open but quiet is not cut by the read timeout soon enough: when
                    # a grace period starts or a denial fails, reopen the stream so that the timer covers it.
                    retry_by = time.monotonic() + 30 if pending else deadline
                    if min(grace["until"] or deadline, retry_by) < wake:
                        break
                failures = 0
        except Exception as exc:
            if not sent:
                raise
            timed_out = (
                "Timeout" in type(exc).__name__
            )  # the connection's own read timeout: reconnect now
            if not fired.is_set() and not timed_out:
                if isinstance(exc, (AttributeError, TypeError, KeyError, NameError)):
                    raise  # a bug, not a connection problem
                if isinstance(exc, anthropic.APIStatusError) and exc.status_code in (
                    400,
                    401,
                    403,
                    404,
                    422,
                ):
                    raise  # retrying won't help
                failures += 1
                say(f"stream error ({type(exc).__name__}); reconnecting")
                time.sleep(min(60, 2**failures))
        else:
            say("(stream closed; reconnecting)")
            time.sleep(1)
        finally:
            if timer is not None:
                timer.cancel()
        if grace["until"] is not None and time.monotonic() >= grace["until"]:
            return finish("retries_exhausted")
    return finish("timeout")


def waiting_confirmations(client, session_id):
    """The event ids the session is waiting on a confirmation for, from its latest idle event, or []."""
    listing = client.beta.sessions.events.list(
        session_id, order="desc", types=["session.status_idle"], limit=1
    )
    for ev in listing:
        if getattr(ev.stop_reason, "type", None) == "requires_action":
            return list(getattr(ev.stop_reason, "event_ids", None) or [])
        break
    return []


def open_run_ids(client, session_id, followed=None):
    """The ids of workflow runs created in the session and not ended, rebuilt from the event list, which is where
    runs are recorded, plus any that followed saw open."""
    events = client.beta.sessions.events
    created = {
        e.workflow_run_id
        for e in events.list(session_id, types=["workflow_run.created"], limit=100)
    }
    ended = {
        e.workflow_run_id
        for e in events.list(session_id, types=["workflow_run.status_ended"], limit=100)
    }
    seen_open = {rid for rid, r in (followed.runs.items() if followed else []) if r.result is None}
    return (created | seen_open) - ended


def stop_runs(client, session_id, followed=None, wait_s=180):
    """Deny any confirmation the session is waiting on; if any workflow run is open (by the server's events,
    plus what followed saw), ask the agent to stop its runs and wait up to wait_s in all for them to end;
    then interrupt the session if it is still running and deny anything left waiting. Returns the ids of
    runs still open afterwards. A session idle at its budget can't take a message, so its runs are left to
    the delete or archive that follows."""
    sessions = client.beta.sessions
    for event_id in waiting_confirmations(client, session_id):
        with contextlib.suppress(anthropic.APIError):
            sessions.events.send(session_id, events=[deny_event(event_id)])
    open_runs = open_run_ids(client, session_id, followed)
    at_budget = followed is not None and followed.stop == "budget_reached"
    if open_runs and not at_budget:
        content = [
            {"type": "text", "text": "Stop all of your workflow runs now and end your turn."}
        ]
        try:
            sessions.events.send(session_id, events=[{"type": "user.message", "content": content}])
        except anthropic.BadRequestError as exc:
            print(
                f"Could not ask the agent to stop its runs ({exc}); removing the session may end them, and "
                "any run still open is listed below."
            )
        else:
            deadline = time.monotonic() + wait_s
            while open_runs and time.monotonic() < deadline:
                time.sleep(10)
                open_runs = open_run_ids(client, session_id)
    status = sessions.retrieve(session_id).status
    if status == "running":
        with contextlib.suppress(anthropic.APIError):
            sessions.events.send(session_id, events=[{"type": "user.interrupt"}])
        deadline = time.monotonic() + 60
        while status == "running" and time.monotonic() < deadline:
            time.sleep(3)
            status = sessions.retrieve(session_id).status
    for event_id in waiting_confirmations(client, session_id):
        with contextlib.suppress(anthropic.APIError):
            sessions.events.send(session_id, events=[deny_event(event_id)])
    return sorted(open_runs)


ASK_FOR_WORKFLOW = (
    "Print the workflow you last started a run with, word for word, in one code block. "
    "Do not start another run."
)


def ask_for_workflow(client, session_id, timeout_s=900):
    """Ask the agent to print the workflow it started the run with; returns (code, the whole reply,
    what follow() saw). Send it only once the run has ended and the session is idle. code is the
    reply's first fenced block, or "". It is the agent's own account: the platform does not return
    the program it ran."""
    reply = follow(client, session_id, ASK_FOR_WORKFLOW, timeout_s=timeout_s, quiet=True)
    return extract_code_block(reply.last_message), reply.last_message, reply


FENCE = chr(96) * 3  # three backticks


def extract_code_block(text):
    """The contents of the first fenced code block in text, or an empty string if there is none."""
    m = re.search(FENCE + r"[^\n]*\n(.*?)" + FENCE, text or "", flags=re.DOTALL)
    return m.group(1).strip() if m else ""


def extract_json_object(text):
    """The last top-level JSON object in text, parsed, or None: the report the lead agent is asked to end
    its reply with."""
    decoder, found, position = json.JSONDecoder(), None, 0
    text = text or ""
    while (start := text.find("{", position)) != -1:
        try:
            value, end = decoder.raw_decode(text, start)
        except json.JSONDecodeError:
            position = start + 1
            continue
        if isinstance(value, dict):
            found = value
        position = end
    return found


# --- What ran: the run's threads and what was analyzed --------------------------------------------


def complete_threads(client, session_id, threads, followed):
    """The session's threads, each once, plus any run thread that the event stream announced but the list left
    out, fetched by id. The list includes archived threads, so the fetch by id is usually unneeded."""
    by_id = {}
    for t in threads:
        by_id.setdefault(t.id, t)
    announced = [tid for run in (followed.runs.values() if followed else []) for tid in run.threads]
    for thread_id in announced:
        if thread_id not in by_id:
            with contextlib.suppress(anthropic.APIError):
                by_id[thread_id] = client.beta.sessions.threads.retrieve(
                    thread_id, session_id=session_id
                )
    return sorted(by_id.values(), key=lambda t: t.created_at)


def thread_prompt(client, session_id, thread_id):
    """The prompt a run thread was given: the text of its first agent.thread_message_received (the docs say a
    workflow's prompt arrives as that event and don't guarantee its wording), else of its first user.message."""
    first_user = ""
    for ev in client.beta.sessions.threads.events.list(thread_id, session_id=session_id):
        if ev.type == "agent.thread_message_received":
            return text_of(ev.content)
        if ev.type == "user.message" and not first_user:
            first_user = text_of(ev.content)
    return first_user


def thread_prompts(client, session_id, threads):
    """{thread id: prompt} for a run's threads."""
    return {t.id: thread_prompt(client, session_id, t.id) for t in threads}


def squash(text):
    """Text with its whitespace runs collapsed, for comparisons that ignore wrapping."""
    return " ".join((text or "").split())


def has_path(text, path):
    """Whether text carries this path as a whole, not as the start of a longer one (x.json inside x.jsonl
    or x.json.bak); a full stop or other punctuation straight after the path is fine."""
    return re.search(re.escape(path) + r"(?![\w-]|\.[\w-])", text) is not None


def ended_turns(export):
    """The ids of the threads that ended a turn normally, from a session export: every thread named by a
    session.thread_status_idle event whose stop reason is end_turn. None when there is no export or it holds
    no thread status events (a compact export)."""
    if not export:
        return None
    ended, any_status_event = set(), False
    for thread in export.get("threads") or []:
        for event in thread.get("events") or []:
            if not str(event.get("type", "")).startswith("session.thread_status_"):
                continue
            any_status_event = True
            if event.get("type") != "session.thread_status_idle":
                continue
            if (event.get("stop_reason") or {}).get("type") == "end_turn":
                ended.add(event.get("session_thread_id") or thread.get("id"))
    # A compact export (export_session's default) keeps no status events: nothing to go by.
    return ended if any_status_event else None


def agent_thread(threads, agent):
    """The first thread (by creation time) that ran this agent, or None."""
    found = [t for t in threads if agent is not None and getattr(t.agent, "id", None) == agent.id]
    return min(found, key=lambda t: as_datetime(t.created_at)) if found else None


def refused_calls(export):
    """How many tool calls the platform's permission policy refused outright (evaluated_permission "deny") in
    the session export; such a call reaches the agent as an error."""
    count = 0
    for thread in (export or {}).get("threads") or []:
        for event in thread.get("events") or []:
            if event.get("evaluated_permission") == "deny":
                count += 1
    return count


def organizer_finished(threads, organizer, export=None):
    """True when a thread that ran the organizer agent ended its turn normally: an end_turn in the session export
    (ended_turns), or, without the export, a thread that is no longer running."""
    ended = ended_turns(export)
    for t in threads:
        if getattr(t.agent, "id", None) != getattr(organizer, "id", None):
            continue
        if (t.id in ended) if ended is not None else (t.status not in ("running", "rescheduling")):
            return True
    return False


def input_coverage(threads, analyzer, input_paths, prompts, followed=None, export=None):
    """{input path: thread id} for each input whose path, as a whole path, is in the first message of
    a run thread that ran the analyzer and ended its turn normally (as in analyzer_threads). An
    empty result can mean that no such thread ended normally or that their first messages, whose
    text the API does not guarantee, name no file."""
    analyzer_id = getattr(analyzer, "id", None)
    ended = ended_turns(export)
    run_ids = set(followed.runs) if followed else None
    covered = {}
    for t in threads:
        if analyzer_id is None or getattr(t.agent, "id", None) != analyzer_id:
            continue
        if t.workflow_run_id is None or (run_ids is not None and t.workflow_run_id not in run_ids):
            continue
        if (t.id not in ended) if ended is not None else (t.status in ("running", "rescheduling")):
            continue
        text = squash(prompts.get(t.id, ""))
        for p in input_paths:
            if p not in covered and has_path(text, p):
                covered[p] = t.id
    return covered


def as_count(value):
    """A count from a JSON report as an int: an integer, a float with no fraction, or a string of digits; else
    None."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return None


def analyzer_threads(threads, analyzer, followed=None, export=None):
    """Count the run threads that ran the analyzer agent; returns (finished, started, by_export). A
    thread finished if the export shows an end_turn for it (by_export True) or, with no export, if
    it is no longer running, a weaker test. With followed, only threads of the followed runs count.
    What each thread was asked is not read here."""
    analyzer_id = getattr(analyzer, "id", None)
    ended = ended_turns(export)
    run_ids = set(followed.runs) if followed else None
    finished = started = 0
    for t in threads:
        if analyzer_id is None or getattr(t.agent, "id", None) != analyzer_id:
            continue
        if t.workflow_run_id is None or (run_ids is not None and t.workflow_run_id not in run_ids):
            continue
        started += 1
        if ended is not None:
            finished += t.id in ended
        elif t.status not in ("running", "rescheduling"):
            finished += 1
    return finished, started, ended is not None


# --- Notebook chores: data files, the store to update, instructions, usage, tool sets and the environment ------


def load_text(path):
    """A data file's text (UTF-8)."""
    return Path(path).read_text(encoding="utf-8")


def load_prompts(folder):
    """Each .md file in folder, keyed by file name without extension, read by load_text."""
    return {p.stem: load_text(p) for p in Path(folder).iterdir() if p.suffix == ".md"}


def store_to_update(client, store_id, records):
    """The existing store a run will update in place, after saving a copy of its files as they are now to
    records/memory-before (compare against it afterwards, or put a file back from it)."""
    store = client.beta.memory_stores.retrieve(store_id)
    saved = download_store(client, store.id, Path(records) / "memory-before")
    print(
        f"Updating {store.id} ({store.name}) in place; {plural(len(saved), 'file')} saved to "
        f"{display_path(Path(records) / 'memory-before')} first"
    )
    return store


def print_usage(run, default_model, budget_usd, estimate=None):
    """Print the run's usage per agent, priced two ways, the session total as the platform metered it, how
    long the run took and the estimate for comparison (recomputed from what was uploaded and created when
    none is given); write usage.json to the run's records. Prints nothing when no thread ran."""
    if not run.threads:
        return
    if estimate is None and run.uploaded and {"analyzer", "lead"} <= set(run.created):
        # The same estimate ready_to_run printed before the run, recomputed from what was uploaded and created.
        files = [TranscriptFile(Path(u.mount_path), u.name, u.size) for u in run.uploaded]
        model = {
            r: model_id(run.created[r].model)
            for r in ("analyzer", "lead", "organizer")
            if r in run.created
        }
        estimate, _ = estimate_cost(files, model["analyzer"], model["lead"], model.get("organizer"))
    rows = usage_rows(run.threads, default_model, run.export)
    print("\n".join(usage_summary(rows)))
    cost = getattr(getattr(run.session_usage, "list_cost", None), "amount", None)
    if cost is not None:
        print(
            f"Session total as the platform metered it: ${int(cost) / 100:,.2f} (budget ${budget_usd})"
        )
    minutes = run.followed.seconds / 60
    if estimate is None:
        print(f"The run took {minutes:.1f} minutes.")
    else:
        print(f"The estimate was ${estimate:,.2f}; the run took {minutes:.1f} minutes.")
    private_write(run.records / "usage.json", json.dumps(rows, indent=1, default=str))


# The comparison after the run reads from the message only what it states: a message may name the
# run ('named "..."'), its phases ('phases, "..." then "..."'), a cap ("at most N at a time") or a
# time limit ("time limit of N minutes"), and the run is then compared with each one stated (with a
# time limit only when the lead agent's reply after the run names one). This
# notebook's message (prompts/work_request.md) states none of them (its "about 20" is not read as a
# cap), so they matter only for wording a developer adds to that template. Task texts in a message
# (a BEGIN ANALYZER TASK ... END ANALYZER TASK block) are compared with what each thread received
# only when run.analyzer_task also holds the analyzer's text, which this notebook never sets;
# otherwise the lead's own task texts are recorded.
def asked_in_request(request):
    """What the message asks of the run, read from its wording: {"name": the run's name (from
    'named "..."'), "phases": the phase titles (from 'phases, "..." then "..."'), "cap": how many
    analyzers may run at a time (from "at most N at a time" or "at most N running at a time"),
    "minutes": the run's time limit (from "time limit to/of N minutes"), "tasks_given": whether the
    message carries the agents' task texts (its BEGIN ANALYZER TASK block)}. A value the message
    does not state is None ([] for phases, False for tasks_given), and the run is then not compared
    with it."""
    # The agents' task texts and any INSTRUCTIONS block are the developer's own words for the agents,
    # not the message's requests of the run, so they are left out before reading the rest (a
    # literal "</user_instructions>" inside INSTRUCTIONS would defeat this; only the comparison's
    # wording can then be off, never the run).
    text = re.sub(r"<user_instructions>.*?</user_instructions>", "", request or "", flags=re.DOTALL)
    tasks_given = "BEGIN ANALYZER TASK" in text
    text = re.sub(r"BEGIN (ANALYZER|ORGANIZER) TASK\n.*?\nEND \1 TASK", "", text, flags=re.DOTALL)
    name = re.search(r'named "([^"]*)"', text)
    phases = re.search(r'phases, "([^"]*)" then "([^"]*)"', text)
    cap = re.search(r"at most (\d+) (?:running )?at a time", text)
    minutes = re.search(r"time limit (?:to|of) (\d+) minutes", text)
    return {
        "name": name.group(1) if name else None,
        "phases": list(phases.groups()) if phases else [],
        "cap": int(cap.group(1)) if cap else None,
        "minutes": int(minutes.group(1)) if minutes else None,
        "tasks_given": tasks_given,
    }


# --- Running the distillation (the notebook's "Run the dream" cells call these) ----------------------


class DistillError(RuntimeError):
    """The run needs a look before anyone relies on the store: a transcript with no analyzer thread
    that finished normally (or, when no such thread names a file, a report count that is missing,
    short of the inputs, or above the threads that finished normally), a workflow run that did not
    complete or was never started, failures the agent reported, or an organizer that did not finish.
    Also raised before anything is created: an estimate over the budget, more files than one session
    mounts, or (in the notebook's export cell) a session that could not be exported."""


class AlreadyDone(RuntimeError):
    """A step was run again, or after the run was cleaned up: nothing is sent or created, and no
    clean-up follows from it."""


class NothingToDistill(RuntimeError):
    """There are no transcript files to distill; raised before anything is created."""


class Distilled:
    """What one distillation run produced, for report_run and print_usage. Creating it checks how long
    the notebook will wait for the run (timeout_minutes, 30 to 1440) and that group_size, recorded in
    settings.json when given, is at least 1, and raises ValueError otherwise, before any agent,
    environment or session is created; then writes settings.json to the records folder (the store,
    whether this run created it, the budget, the group size if any, and that wait). finish_run adds the
    agents, the environment and the files once they exist."""

    last = None  # newest run here; ready_to_run refuses while its agents, files or session remain

    def __init__(
        self,
        records,
        output_store,
        store_created,
        budget_usd,
        group_size=None,
        timeout_minutes=180,
        delete_session=True,
    ):
        if group_size is not None and int(group_size) < 1:  # None: the message names no exact size
            raise ValueError(f"group_size must be at least 1 (it is {group_size})")
        if not 30 <= int(timeout_minutes) <= 1440:
            # RUN_TIMEOUT_MINUTES is between half an hour and a day; the notebook waits 30 minutes more.
            raise ValueError(
                f"RUN_TIMEOUT_MINUTES must be between 30 and 1440 (it is {timeout_minutes})"
            )
        self.records, self.output_store = records, output_store
        self.settings = {
            "output_store": output_store.id,
            "store_name": output_store.name,
            "store_created": bool(store_created),
            "budget_usd": budget_usd,
            "group_size": group_size,
            "run_timeout_minutes": timeout_minutes,
        }
        self.timeout_s = (timeout_minutes + 30) * 60  # how long follow_run waits for the run to end
        self.created, self.uploaded, self.input_paths = {}, [], []
        self.request = self.analyzer_task = self.organizer_task = self.mem_dir = ""
        self.followed = self.report = self.export = self.session_usage = None
        # The lead agent's stated reason, when its report on the first run counted no transcript as
        # processed and read_results asked it once for a new run; else None.
        self.retry_reason = None
        # The workflow the lead agent wrote, as it printed it when asked, and that whole reply.
        self.workflow = self.workflow_reply = ""
        # Where the run differed from what the message asked (measurements()), filled in once the run has been read.
        self.measurements = None
        # _index.md as read_results read it back once the run had ended; None when it was not read.
        self.index_text = None
        # After the run the session is deleted (the records keep its export); False archives it instead.
        self.delete_session = delete_session
        self.problems = []  # set by report_run; raise_if_problems raises DistillError for them
        self.finished = False  # set by finish_run after its clean-up
        self.done = set()  # the steps (cells) that ran to their end, so that none runs twice (step)
        # True when every workflow run had ended with the session idle (set by read_results).
        self.ended = False
        self.swept = False  # the organizer's placeholder files were looked for
        self.threads, self.prompts = [], {}
        self.runs_left_open, self.stubs_removed, self.stubs_left = [], [], []
        self.save_settings()
        Distilled.last = self

    def save_settings(self):
        """Write settings.json: the fields given at creation plus, once they exist, the files uploaded, both
        worker agents and the lead agent as the platform recorded them, and the environment."""
        settings = dict(self.settings, files=[Path(u.mount_path).name for u in self.uploaded])
        for role in ("analyzer", "organizer", "lead", "environment"):
            if role in self.created:
                settings[role] = self.created[role].model_dump(mode="json")
        roles = ("lead", "analyzer", "organizer")
        settings["models"] = {
            r: model_id(self.created[r].model) for r in roles if r in self.created
        }
        private_write(
            Path(self.records) / "settings.json", json.dumps(settings, indent=1, default=str)
        )


def ready_to_run(files, analyzer_model, lead_model, organizer_model, budget_usd):
    """Print the estimate and return True. Raises
    NothingToDistill when there are no transcript files, DistillError when the estimate is over the
    budget or there are more files than one session mounts (each before anything is created) and AlreadyDone while the previous run in this
    process still has agents, files or a session."""
    last = Distilled.last
    if last is not None and (last.created or last.uploaded) and not last.finished:
        raise AlreadyDone(
            'The previous run still has its agents, files or session; run "Clean up" first.'
        )
    if not files:
        raise NothingToDistill("No transcript files: nothing to distill, so nothing was created.")
    if len(files) > MAX_FILES_PER_SESSION:
        raise DistillError(
            f"{len(files)} files is more than one session mounts ({MAX_FILES_PER_SESSION}); nothing was "
            "started. Split them into batches of at most 500: the first run prints the store's id after "
            "'Memory store:'; set COOKBOOK_STORE_ID to it for the other batches."
        )
    estimate, lines = estimate_cost(files, analyzer_model, lead_model, organizer_model)
    print("\n".join(lines))
    if estimate > budget_usd:
        raise DistillError(
            f"The estimate, ${estimate:.2f}, is above the budget (${budget_usd}); nothing was started. "
            "Raise BUDGET_USD or distill fewer files."
        )
    return True


def memory_mount_path(client, session, store_id):
    """Where the store is mounted in this session's sandbox, as the platform reports it on the session's
    memory_store resource. Read once more if the create response didn't carry it yet."""
    for attempt in range(2):
        for r in session.resources:
            if r.type == "memory_store" and r.memory_store_id == store_id and r.mount_path:
                return r.mount_path
        if attempt == 0:
            session = client.beta.sessions.retrieve(session.id)
    raise RuntimeError(
        f"Session {session.id} reports no mount path for store {store_id}. Check that the store still exists, "
        'then run the dream again from "Create the store".'
    )


def mount_paths(client, session, store_id, uploaded, expected=None):
    """(the store's folder, the transcripts' paths) as the session's sandbox sees them. When expected is
    given (the folder memory_path() worked out before the session existed, already written into the
    agents' prompts), a different folder raises DistillError before anything is sent."""
    mem_dir = memory_mount_path(client, session, store_id)
    if expected is not None and mem_dir.rstrip("/") != expected.rstrip("/"):
        raise DistillError(
            f"The session mounts the memory store at {mem_dir}, but the agents' prompts name {expected}, "
            "so nothing was sent and the run was cleaned up. memory_path() in memory_distill_utils.py "
            "builds that folder from MEMORY_MOUNT_ROOT and the store's name by the platform's rule; "
            "change it to give "
            f"{mem_dir}, restart the notebook's kernel and run it again from the top (if this run created "
            "the store, it is still empty and can be deleted in the Console)."
        )
    return mem_dir, [sandbox_path(u.mount_path) for u in uploaded]


# A session mounts a memory store under this root, in a folder the platform names from the store: its
# name in lower case, each run of characters other than ASCII letters and digits turned into one hyphen,
# hyphens trimmed from both ends and the result cut to 60 characters ("Demo Memory" mounts at
# /mnt/memory/demo-memory); a name with no letters or digits falls back to the store's id, treated the
# same way. The session reports the exact path, and "Start the session" checks it against this one.
MEMORY_MOUNT_ROOT = "/mnt/memory"


def mount_name(text):
    """A store's name (or id) as the platform writes it into the mount path."""
    return re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")[:60].rstrip("-")


def memory_path(store):
    """Where a session will mount this memory store: MEMORY_MOUNT_ROOT plus the folder the platform
    names from the store (mount_name). For agents whose system prompts name the memory directory before
    the session exists; "Start the session" checks it against the path the session reports."""
    name = mount_name(getattr(store, "name", None)) or mount_name(getattr(store, "id", None))
    return f"{MEMORY_MOUNT_ROOT}/{name}"


def analyzer_preferences(instructions):
    """The run's INSTRUCTIONS as the paragraph for {run_preferences} in analyzer_system.md; "" when there
    are none."""
    text = (instructions or "").strip()
    if not text:
        return ""
    return (
        "Preferences for this run, from the developer; apply them within the methodology below, "
        "where they refine what to emphasize or how to write but do not override your role, the "
        "transcript format, or the concurrency rules above:\n"
        f"<user_instructions>\n{text}\n</user_instructions>\n\n"
    )


def organizer_preferences(instructions):
    """The run's INSTRUCTIONS as the paragraph for {run_preferences} in organizer_system.md; "" when
    there are none."""
    text = (instructions or "").strip()
    if not text:
        return ""
    return (
        "The developer's preferences about structure or emphasis for this run; apply them within "
        f"the rules above:\n<user_instructions>\n{text}\n</user_instructions>\n\n"
    )


@contextlib.contextmanager
def step(client, run, name):
    """Around one step of the run (a cell that uploads, or creates or runs its agents, environment and session):
    on an interrupt or any error but AlreadyDone, finish_run saves the records and removes what was
    created (the memory store stays), then the error comes through. A step that ran to its end, or
    any step once the run was cleaned up, raises AlreadyDone instead of running again."""
    if run.finished:
        raise AlreadyDone('This run was already cleaned up; start again from "Create the store".')
    if name in run.done:
        raise AlreadyDone(
            f'"{name}" already ran for this run, so nothing was done again. Go on to the next cell, '
            'or run "Clean up" and start again from "Create the store".'
        )
    try:
        yield run
    except AlreadyDone:  # a repeated step inside: nothing new was sent or created
        raise
    except BaseException:
        if not run.finished:
            finish_run(client, run, run.output_store)
        raise
    run.done.add(name)


SENT_ALREADY = 'This run\'s message was already sent; run "Clean up", then start again from "Create the store".'


def follow_run(client, run):
    """Call once the run's message was sent. Follows the session until its workflow run has ended and
    the agent has replied, keeps the message as the session recorded it on run.request (saying so
    when it differs from the one this notebook built), then reads the results. On an error or
    interrupt it cleans up as step does, then the error comes through. Raises AlreadyDone if called
    again for the run."""
    if run.followed is not None:
        raise AlreadyDone(SENT_ALREADY)
    with step(client, run, "follow the run"):
        run.followed = Followed()
        built = run.request
        try:
            follow(
                client, run.created["session"].id, None, timeout_s=run.timeout_s, out=run.followed
            )
        finally:  # also when follow fails: the records keep the message as the session stored it
            if run.followed.request:
                run.request = run.followed.request
        if built and run.request != built:
            print(
                "The session's copy of the message differs from the one this notebook built; the "
                "records keep the session's copy, and the run is compared with it."
            )
        read_results(client, run)


# Sent once by read_results when the lead agent's report counts no transcript as processed and lists
# failures, which usually means the workflow engine rejected an option in the lead agent's script. The
# lead agent's prompt allows a second run only when a later message asks for one.
ASK_TO_RUN_AGAIN = (
    "Your report counts no transcript as processed. Start the run once more with the same agents and "
    "the same tasks, correcting your script if it caused the error, and reply with the same one-line "
    "report when that run has ended."
)


def nothing_processed(report):
    """The lead agent's stated reason (the first failure's), when its report counts no transcript as
    processed and lists at least one failure. None for any other report."""
    report = report if isinstance(report, dict) else {}
    failures = report.get("failures")
    if as_count(report.get("inputs_processed")) != 0:
        return None
    if not isinstance(failures, list) or not failures:
        return None
    first = failures[0]
    reason = first.get("reason") if isinstance(first, dict) else first
    return str(reason or "").strip() or "no reason given"


def counted_threads(run):
    """run.threads; after a retry, only the newest run's threads (the run that is counted)."""
    if not run.retry_reason or not run.followed or not run.followed.runs:
        return run.threads
    newest = list(run.followed.runs)[-1]
    return [t for t in run.threads if t.workflow_run_id == newest]


def print_report(run):
    """Print the lead agent's JSON report (run.report), or say what its last message was instead."""
    if run.report:
        # report_run prints the organizer's changes one per line, so a finished organizer's list is left
        # out of this line.
        listed = bool(run.report.get("changes")) and run.report.get("organized") is not False
        listed = listed and not run.report.get("organizer_error")
        shown = {k: v for k, v in run.report.items() if not (listed and k == "changes")}
        more = " (the organizer's changes are listed below)" if listed else ""
        print("The lead agent's report:", json.dumps(shown) + more)
    elif run.followed.last_message.strip():
        print("The lead agent's last message had no JSON report; it is in the records. It begins:")
        print(run.followed.last_message[:300])
    else:
        print("No JSON report: the lead agent sent no message, or its last message was empty.")


def ask_to_run_again(client, run, reason):
    """Send ASK_TO_RUN_AGAIN once and follow the new run; run.followed then covers both turns (both
    runs, all denials and errors, the time of both) and run.report is the new reply's report."""
    first = run.followed
    print(
        "The lead agent's report counts no transcript as processed. Asking it once to start the run again."
    )
    again = Followed(request=first.request)
    try:
        follow(
            client, run.created["session"].id, ASK_TO_RUN_AGAIN, timeout_s=run.timeout_s, out=again
        )
    finally:  # also when follow fails: keep what both turns saw
        again.runs = {**first.runs, **again.runs}
        again.seconds += first.seconds
        again.denied, again.errors = first.denied + again.denied, first.errors + again.errors
        again.retried = first.retried + again.retried
        run.followed, run.retry_reason = again, reason
    outcome = describe_stop(again.stop)
    if again.stop == "idle" and len(again.runs) == len(first.runs):
        outcome = "the lead agent replied without starting a new run"
    print(f"After {again.seconds / 60:.1f} minutes in all: {outcome}.")
    run.report = extract_json_object(again.last_message)
    print_report(run)


def read_results(client, run):
    """After follow(): print how the run ended and the agent's JSON report; when that report counts
    no transcript as processed, ask once for a new run and follow it; ask the agent to print its
    workflow if the session went idle after a run; collect into run the threads, each thread's
    prompt, the session's usage and its full export; only if the run has ended, also delete the
    organizer's one-line "MOVED TO" files."""
    session_id = run.created["session"].id
    outcome = describe_stop(run.followed.stop)
    if run.followed.stop == "idle" and not run.followed.runs:
        outcome = "the lead agent replied without starting a workflow run"
    print(f"After {run.followed.seconds / 60:.1f} minutes: {outcome}.")
    run.report = extract_json_object(run.followed.last_message)
    print_report(run)
    idle_after_run = run.followed.stop == "idle" and bool(run.followed.runs)
    reason = nothing_processed(run.report) if idle_after_run else None
    if reason is not None and run.retry_reason is None:
        ask_to_run_again(client, run, reason)
    if run.followed.stop == "idle" and run.followed.runs:
        run.workflow, run.workflow_reply, asked = ask_for_workflow(client, session_id)
        if asked.runs:
            print("Asking for the workflow started another run; its threads are in the records.")
    listed = client.beta.sessions.threads.list(session_id)
    run.threads = complete_threads(client, session_id, listed, run.followed)
    in_runs = [t for t in counted_threads(run) if t.workflow_run_id in run.followed.runs]
    run.prompts = thread_prompts(client, session_id, in_runs)
    run.session_usage = client.beta.sessions.retrieve(session_id).usage
    run.ended = run.followed.stop == "idle" and all(r.result for r in run.followed.runs.values())
    try:  # the full transcript: report_run reads each thread's end from it; the records keep it
        run.export = export_session(client, session_id, compact=False)
    except anthropic.APIError as exc:
        print(f"Could not export the session ({exc}); the clean-up will try once more.")
    if run.ended:  # otherwise finish_run stops the run first, exports again and sweeps
        sweep_placeholders(client, run)
        try:  # report_run counts the entries of the index the organizer left
            run.index_text = memory_text(client, run.output_store.id, "/_index.md")
        except anthropic.APIError as exc:
            print(f"Could not read _index.md back ({exc}); the organizer's own count is used.")


def sweep_placeholders(client, run):
    """Delete, at most once per run, the one-line "MOVED TO" files the organizer left where it
    merged or renamed a file (sweep_stubs); run.stubs_removed and run.stubs_left say what went
    and what stayed."""
    organizer_thread = agent_thread(counted_threads(run), run.created.get("organizer"))
    if run.swept or organizer_thread is None or "session" not in run.created:
        return
    run.swept = True
    try:
        run.stubs_removed, run.stubs_left = sweep_stubs(
            client,
            run.output_store.id,
            run.created["session"].id,
            since=organizer_thread.created_at,
        )
    except anthropic.APIError as exc:
        print(
            "Could not delete the organizer's placeholder files, each a single line "
            f'"MOVED TO [[…]]" ({exc}); delete them in the Console.'
        )
    if not run.ended:  # at clean-up, after report_run has printed: say here what it would have said
        if run.stubs_removed:
            print(
                f"Deleted {plural(len(run.stubs_removed), 'placeholder file')} the organizer left after "
                "merging or renaming files."
            )
        print_placeholders_left(run)


def print_placeholders_left(run):
    """Print the placeholder files the sweep left: those whose target file does not exist (what they
    held may be lost) and those that could not be deleted."""
    missing = [(p, t) for p, t, why in run.stubs_left if why == "missing target"]
    failed = [p for p, t, why in run.stubs_left if why != "missing target"]
    if missing:
        print(
            "These placeholder files point to a file that does not exist, so what they held may be lost; "
            "restore it from each file's earlier memory version: "
            + ", ".join(f"{p} → [[{t}]]" for p, t in missing)
        )
    if failed:
        print(
            "Placeholder files that could not be deleted (delete them in the Console): "
            + ", ".join(failed)
        )


def save_records(client, run, output_store):
    """Write what this run sent and got to its records folder: the message, the agent's report and the
    workflow it wrote as it printed it when asked, where the run differed from what the message asked
    (measurements.json), the thread list with each thread's prompt, the session's full export, and the memory."""
    if run.followed:
        # A comparison that fails must not stop the records from being saved.
        try:
            run.measurements = measurements(run)
        except Exception as exc:
            print(
                f"Could not compare the run with what the message asked ({exc}); measurements.json in "
                "the records keeps the comparison printed after the run, if one was printed."
            )
    saved = {
        "report.json": json.dumps(run.report, indent=1),
        "work_request.md": run.request,
        "workflow_from_agent.md": run.workflow_reply,
        "measurements.json": json.dumps(run.measurements, indent=1) if run.measurements else "",
        "placeholders.json": json.dumps(
            {"deleted": run.stubs_removed, "left": run.stubs_left}, indent=1
        ),
        "threads.json": json.dumps([t.model_dump(mode="json") for t in run.threads], indent=1),
        "thread_prompts.json": json.dumps(run.prompts, indent=1),
        "session_export.json": json.dumps(run.export, indent=1) if run.export else "",
    }
    if run.followed:
        followed = {
            "stop": run.followed.stop,
            "seconds": run.followed.seconds,
            "denied": run.followed.denied,
            "errors": run.followed.errors,
            "runs": {k: vars(v) for k, v in run.followed.runs.items()},
        }
        saved["followed.json"] = json.dumps(followed, indent=1, default=str)
    for name, text in saved.items():
        if text:
            private_write(run.records / name, text)
    download_store(client, output_store.id, run.records / "memory")
    print(f"Records saved in {display_path(run.records)}")


def remove_everything(client, created, uploaded, delete_session=True):
    """Delete (or, with delete_session False, archive) the session, archive the environment and the agents,
    delete the uploaded files. Whatever can't be done is printed with the call that does it later, and the
    rest still runs. Returns True when everything is gone (or archived)."""
    gone, session_gone = True, True
    if "session" in created:
        sid = created["session"].id
        deleted = delete_session and remove(
            f"delete session {sid}", client.beta.sessions.delete, sid
        )
        session_gone = deleted or remove(
            f"archive session {sid}",
            client.beta.sessions.archive,
            sid,
            later=f"client.beta.sessions.archive({sid!r}), once it has stopped running",
        )
        if delete_session and not deleted and session_gone:
            print(
                f"Session {sid} was archived instead; delete it with client.beta.sessions.delete({sid!r})."
            )
        gone = bool(session_gone)
    if "environment" in created:
        eid = created["environment"].id
        gone &= remove(
            f"archive environment {eid}",
            client.beta.environments.archive,
            eid,
            later=f"client.beta.environments.archive({eid!r})",
        )
    for role in ("lead", "analyzer", "organizer"):
        if role in created:
            aid = created[role].id
            gone &= remove(
                f"archive agent {aid} ({created[role].name})",
                client.beta.agents.archive,
                aid,
                later=f"client.beta.agents.archive({aid!r})",
            )
    if session_gone:
        delete_uploads(client, uploaded)
    elif uploaded:
        # The session is still there (a workflow run may still be open), so its inputs are left with it; the
        # uploaded copies expire within a day by themselves.
        print(
            f"The uploaded transcripts were left in place for session {created['session'].id}; they expire "
            "by themselves within a day."
        )
    return bool(gone)


def finish_run(client, run, output_store, delete_session=None):
    """Stop any open workflow run; unless read_results did after the run ended, export the session
    in full and delete the organizer's placeholder files; save the records and a copy of the memory;
    delete (or archive) the session, archive the agents and the environment, delete the uploads. The
    store stays; delete_session defaults to run.delete_session; a second call does nothing."""
    if run.finished:  # a cell that failed or was interrupted has already cleaned up after itself
        return
    delete_session = run.delete_session if delete_session is None else delete_session
    try:
        if "session" in run.created:
            sid = run.created["session"].id
            try:
                run.runs_left_open = stop_runs(client, sid, run.followed)
            except anthropic.APIError as exc:
                print(f"Could not check or stop the session's runs ({exc}).")
            try:  # the full transcript, unless read_results took it after the run had ended
                if run.export is None or not run.ended or run.runs_left_open:
                    run.export = export_session(client, sid, compact=False)
            except anthropic.APIError as exc:
                print(
                    f"Could not export the session ({exc}); the records hold what the stream showed."
                )
            if run.threads:  # the organizer's placeholder files, unless read_results swept them
                sweep_placeholders(client, run)
        run.save_settings()
        if run.created:
            save_records(client, run, output_store)
    finally:
        remove_everything(client, run.created, run.uploaded, delete_session)
        run.finished = True
        if run.runs_left_open:
            print(f"Workflow runs that were still open at clean-up: {run.runs_left_open}")


def problems_text(run):
    """The text naming the problems report_run recorded and where the run's records are."""
    return (
        "The run needs a look: "
        + "; ".join(run.problems)
        + f". Read the run's records ({display_path(run.records)}) before relying on the store."
    )


def raise_if_problems(run):
    """Raise DistillError for the problems report_run recorded. Call it last, after finish_run and
    print_usage, so that the run is cleaned up and its usage printed before the error."""
    if run.problems:
        raise DistillError(problems_text(run))


def index_entries(index_text):
    """How many files an _index.md text lists: its lines that begin with a [[slug]] link, bulleted or
    numbered or not. None when the index was not read."""
    if index_text is None:
        return None
    entry = re.compile(r"\s*(?:[-*+]\s+|\d+[.)]\s+)?\[\[")
    return sum(1 for line in index_text.splitlines() if entry.match(line))


def report_run(run):
    """Print how many transcripts were analyzed, any tool calls this notebook declined, the workflow
    the lead agent wrote and where the run differed from what the message asked, and record in
    run.problems what needs a look; raise_if_problems raises for them."""
    if not run.created:
        return
    expected = len(run.input_paths)
    report = run.report if isinstance(run.report, dict) else {}
    claimed = as_count(report.get("inputs_processed"))
    analyzer = run.created.get("analyzer")
    threads = counted_threads(run)  # after a retry, the new run's threads only
    finished, started, by_export = analyzer_threads(threads, analyzer, run.followed, run.export)
    covered = input_coverage(
        threads, analyzer, run.input_paths, run.prompts, run.followed, run.export
    )
    how = "" if by_export else " (thread status alone, without the session export)"
    restated = (
        f"the lead agent's report says {claimed} processed"
        + (", no failures" if not report.get("failures") else ", with failures")
        if claimed is not None
        else "the lead agent's report gives no count"
    )
    problems = []
    if covered:
        # The thread records name the files: each transcript counts as analyzed when its path is in
        # the first message of an analyzer thread that ended its turn normally.
        print(
            f"{len(covered)} of {plural(expected, 'transcript')} analyzed, going by the platform's thread "
            f"records{how}; {restated}."
        )
        missing = [p for p in run.input_paths if p not in covered]
        if missing:
            problems.append("no analyzer thread finished normally for " + ", ".join(missing))
    elif claimed is not None:
        # No analyzer thread that ended normally names an input file: none ended normally, or their
        # first messages (whose text the API does not guarantee) name none. So the count is the
        # report's, checked against how many analyzer threads finished normally.
        print(
            f"{claimed} of {plural(expected, 'transcript')} analyzed, going by the lead agent's "
            f"report; by the platform's records, {finished} of {plural(started, 'analyzer thread')} "
            f"finished normally{how}."
        )
        if claimed != expected:
            problems.append(f"the report counts {claimed} of {expected} transcripts as processed")
        if finished < claimed:
            problems.append(
                f"the platform's records show {plural(finished, 'analyzer thread')} that finished "
                f"normally, fewer than the {claimed} transcripts the report counts as processed"
            )
    else:
        print(
            f"Could not tell how many transcripts were analyzed ({expected} in all): no analyzer thread that ended "
            f"normally names an input file, and the lead agent's report gives no count; {finished} of "
            f"{plural(started, 'analyzer thread')} finished normally{how}."
        )
        problems.append(
            "neither the thread records nor the report say which transcripts were analyzed"
        )
    runs = list(run.followed.runs.values()) if run.followed else []
    if run.retry_reason:  # after a retry, the first run's end is not judged
        runs = runs[-1:]
    for r in runs:
        if (r.result or {}).get("type") != "completed":
            problems.append(
                f"the workflow run {r.name or r.id!r} did not complete "
                f"({json.dumps(r.result) if r.result else 'no end event'})"
            )
    if not runs:
        problems.append("the lead agent started no workflow run")
    failures = (run.report or {}).get("failures") or []
    if not isinstance(failures, list):  # a list is asked for; show anything else as it came
        failures = [failures]
    if failures:
        problems.append(
            f"the lead agent's report lists {plural(len(failures), 'failure')}: {json.dumps(failures)}"
        )
    organizer = run.created.get("organizer")
    if organizer is not None and runs:
        # Whether the organizer finished comes from the platform's records (a thread that ran it
        # ended its turn normally), unless the lead agent's report says it failed or did not run;
        # the report also gives the organizer's count and changes.
        failed = report.get("organized") is False or bool(report.get("organizer_error"))
        if organizer_finished(threads, organizer, run.export) and not failed:
            n = as_count(report.get("index_entries"))
            listed = index_entries(run.index_text)
            reported = (
                f"the organizer reported {n}" if n is not None else "the organizer gave no count"
            )
            if run.index_text is not None and not run.index_text.strip():
                counted = f"no _index.md was found in the store, or it is empty ({reported})"
            elif listed is not None:
                counted = f"_index.md lists {plural(listed, 'file')}" + (
                    f" ({reported})" if n != listed else ""
                )
            elif n is not None:
                counted = f"by its own count, _index.md lists {n} files"
            else:
                counted = "the lead agent's report does not say how many files _index.md lists"
            swept = len(run.stubs_removed)
            print(
                f"The organizer finished; {counted}."
                + (
                    f" {plural(swept, 'placeholder file')} it left after merging or renaming "
                    + ("was" if swept == 1 else "were")
                    + " deleted."
                    if swept
                    else ""
                )
            )
            changes = report.get("changes") or []
            changes = [str(c) for c in (changes if isinstance(changes, list) else [changes])]
            if changes:
                print("Its changes:")
                for change in changes[:20]:
                    print(f"- {change}")
                if len(changes) > 20:
                    print(f"- and {len(changes) - 20} more, in the records")
        else:
            error = report.get("organizer_error")
            if not failed:  # the report claims changes, but no organizer thread finished: show them
                listed = report.get("changes") or []
                listed = [str(c) for c in (listed if isinstance(listed, list) else [listed])]
                for change in listed[:20]:
                    print(f"- a change the lead agent's report lists: {change}")
                if len(listed) > 20:
                    print(f"- and {len(listed) - 20} more, in the records")
            problems.append(
                (
                    "the lead agent's report says the organizer did not run or failed"
                    if failed
                    else "no thread that ran the organizer finished normally"
                )
                + (f" (the run returned: {error})" if error else "")
            )
        print_placeholders_left(run)
    refused = refused_calls(run.export)
    if refused:
        print(
            f"{plural(refused, 'tool call')} refused by the platform's permission policy (each reached its "
            "agent as an error)."
        )
    if run.followed and run.followed.denied:
        n = len(run.followed.denied)
        print(
            f"{plural(n, 'tool call')} paused for approval and this notebook declined {'it' if n == 1 else 'them'}."
        )
    if run.workflow:
        print(WORKFLOW_LINE)
        print(run.workflow)
    if run.followed:
        try:
            if run.measurements is None:
                run.measurements = measurements(run)
            print("\n".join(measurement_lines(run.measurements)))
        except Exception as exc:  # a measurement: it never decides whether the run needs a look
            print(
                f"Could not compare the run with what the message asked ({exc}). To compare them "
                "by hand, see the records folder: work_request.md (the message), "
                "workflow_from_agent.md (the workflow the lead agent wrote, as it printed it) and "
                "thread_prompts.json (each thread's task)."
            )
    run.problems = problems
    if problems:
        print(
            "The run needs a look: "
            + "; ".join(problems)
            + '. "Clean up" saves the records, then stops the notebook with this message.'
        )


# --- Where the run differed from what the message asked: a measurement, not a gate ---------------------------


def diff_lines(sent, received):
    """The lines to remove from sent ("-" first) and to add ("+" first) to get received, in order,
    without the headers and context lines of a unified diff; [] when the two have the same lines."""
    diff = difflib.unified_diff(sent.splitlines(), received.splitlines(), lineterm="", n=0)
    return [line for line in list(diff)[2:] if line[:1] in "+-"]


def compare_text(sent, received):
    """How received compares with sent: "identical", "spacing" (equal once whitespace at the ends is
    dropped and each run of whitespace becomes one space) or "changed"."""
    if received == sent:
        return "identical"
    if received.strip() == sent.strip() or squash(received) == squash(sent):
        return "spacing"
    return "changed"


def most_at_once(spans):
    """The largest number of (start, end) spans open at the same moment; an end of None counts as still open."""
    events = sorted(
        [(s, 1) for s, _ in spans] + [(e, -1) for _, e in spans if e is not None],
        key=lambda x: (x[0], x[1]),
    )
    most = running = 0
    for _, change in events:
        running += change
        most = max(most, running)
    return most


def measurements(run):
    """Compare what the run did with what the message asked; returns a dict (retried: the lead's reason
    when read_results asked once for a new run, else None; the new run is then the one compared). workflow_printed says
    whether the agent printed the workflow it wrote when asked (workflow_asked: whether a reply to
    that request came back at all).
    When the message gives the agents' task texts (tasks_given), briefs counts, per agent name, the
    run threads whose first message matches the task text built for them, with the diffs of those
    that do not; when it gives none, tasks_written records the first task the lead agent wrote for
    each agent instead. name_asked, phases_asked, concurrency_limit and time_limit_minutes_asked come
    from the message (None or [] for what it does not state), name_run and phases_run from the
    platform's run events. differed is True when anything measured here differs from what the
    message asked."""
    out = {"workflow_printed": bool(run.workflow), "workflow_asked": bool(run.workflow_reply)}
    # The API does not guarantee the text of a run thread's first message (the Managed Agents
    # documentation on session threads says so), so a brief that differs is reported, never treated
    # as a failed run.
    asked = asked_in_request(run.request)
    expected_for = {}  # agent id: (name, function from the thread's text to (input, expected))
    analyzer, organizer = run.created.get("analyzer"), run.created.get("organizer")
    # When the message gives no task texts, the lead agent words each agent's task itself: the
    # texts it wrote are recorded (tasks_written), not compared with anything.
    compare_tasks = bool(asked["tasks_given"] and run.analyzer_task)
    out["tasks_given"] = asked["tasks_given"]
    out["tasks_written"] = {}
    if not compare_tasks:
        for t in run.threads:
            agent_id = getattr(t.agent, "id", None)
            received = run.prompts.get(t.id) or ""
            if not received.strip() or t.workflow_run_id is None:
                continue
            for agent in (analyzer, organizer):
                if agent is not None and agent_id == agent.id:
                    out["tasks_written"].setdefault(agent.name, received)
    if analyzer is not None and compare_tasks:

        def analyzer_brief(text):
            path = next((p for p in run.input_paths if has_path(text, p)), None)
            return path, (None if path is None else run.analyzer_task.replace("INPUT_PATH", path))

        expected_for[analyzer.id] = (analyzer.name, analyzer_brief)
    if organizer is not None and compare_tasks:
        expected_for[organizer.id] = (organizer.name, lambda text: ("", run.organizer_task))
    briefs = {
        name: {"threads": 0, "identical": 0, "spacing": 0, "changed": [], "no_input_named": 0}
        for name, _ in expected_for.values()
    }
    for t in run.threads:
        agent_id = getattr(t.agent, "id", None)
        received = run.prompts.get(t.id) or ""
        if t.workflow_run_id is None or not received.strip() or agent_id not in expected_for:
            continue
        name, brief_for = expected_for[agent_id]
        row = briefs[name]
        row["threads"] += 1
        path, expected = brief_for(squash(received))
        if expected is None:
            row["no_input_named"] += 1
            continue
        verdict = compare_text(expected, received)
        if verdict == "changed":
            diff = diff_lines(expected, received)
            row["changed"].append({"thread": t.id, "input": path or None, "diff": diff})
        else:
            row[verdict] += 1
    out["briefs"] = briefs
    out["name_asked"], out["phases_asked"] = asked["name"], asked["phases"]
    runs = list(run.followed.runs.values()) if run.followed else []
    out["runs"] = len(runs)
    # After a retry (read_results asked for one new run because the first read no transcript), the new
    # run is the one measured; "runs" still counts both, and two is then what was asked for.
    out["retried"] = run.retry_reason
    expected_runs = 2 if run.retry_reason else 1
    runs = runs[-1:] if run.retry_reason else runs
    out["name_run"] = [r.name for r in runs]
    out["phases_run"] = [list(r.phases.values()) for r in runs]
    by_agent, spans = {}, {}
    for r in runs:
        for info in r.threads.values():
            by_agent[info["agent"]] = by_agent.get(info["agent"], 0) + 1
            spans.setdefault(info["agent"], []).append((info["started"], info["ended"]))
    out["inputs"] = len(run.input_paths)
    analyzer_name = getattr(analyzer, "name", None)
    organizer_name = getattr(organizer, "name", None)
    out["agents"] = {"analyzer": analyzer_name, "organizer": organizer_name}
    out["threads_by_agent"] = by_agent
    out["most_at_once"] = {name: most_at_once(s) for name, s in spans.items()}
    out["concurrency_limit"] = asked["cap"]  # None when the message sets no cap
    analyzer_ends = [e for s, e in spans.get(analyzer_name, [])]
    organizer_starts = [s for s, e in spans.get(organizer_name, [])]
    if organizer_starts and analyzer_ends:
        # Times are seconds from when this notebook received each event; an organizer start equal
        # to the last analyzer end counts as in order.
        last_end = max((e for e in analyzer_ends if e is not None), default=None)
        late = None in analyzer_ends or (last_end is not None and min(organizer_starts) < last_end)
        out["organizer_before_analyzers_ended"] = bool(late)
    else:
        out["organizer_before_analyzers_ended"] = None
    report = run.report if isinstance(run.report, dict) else None
    out["report_given"] = report is not None
    # None unless the report has this key; the report shape in lead_system.md has none.
    out["time_limit_set"] = report.get("time_limit_set") if report else None
    processed = as_count(report.get("inputs_processed")) if report else None
    said = re.search(
        r"time limit\D{0,40}?(\d[\d,]*)\s*minutes?", after_code_block(run.workflow_reply), re.I
    )
    out["time_limit_minutes_said"] = int(said.group(1).replace(",", "")) if said else None
    out["time_limit_minutes_asked"] = asked["minutes"]  # None when the message sets no limit
    analyzers = by_agent.get(analyzer_name, 0)
    out["organizer_missing"] = bool(
        organizer_name and runs and by_agent.get(organizer_name, 0) == 0 and (processed or 0) > 0
    )
    out["differed"] = bool(
        any(row["changed"] or row["no_input_named"] for row in briefs.values())
        or (out["name_asked"] is not None and any(n != out["name_asked"] for n in out["name_run"]))
        or (out["phases_asked"] and any(p != out["phases_asked"] for p in out["phases_run"]))
        or out["runs"] != expected_runs
        or (analyzer_name is not None and runs and analyzers < out["inputs"])
        or out["organizer_missing"]
        or (
            out["concurrency_limit"] is not None
            and out["most_at_once"].get(analyzer_name, 0) > out["concurrency_limit"]
        )
        or out["organizer_before_analyzers_ended"] is True
        or (
            said is not None
            and asked["minutes"] is not None
            and out["time_limit_minutes_said"] != asked["minutes"]
        )
        or (asked["minutes"] is not None and out["time_limit_set"] is False)
    )
    return out


def after_code_block(text):
    """The part of a reply that follows its first fenced code block ("" when there is none)."""
    m = re.search(FENCE + r"[^\n]*\n.*?" + FENCE + r"(.*)", text or "", flags=re.DOTALL)
    return m.group(1) if m else ""


WORKFLOW_LINE = "The workflow the lead agent wrote, as it printed it when asked:"
DIFFERED_LINE = "Where the run differed from what the message asked:"
BRIEFS_LINE = (
    "Task texts the threads received that differ from the notebook's (the platform does not "
    "guarantee this text, so a difference may not be the lead agent's doing):"
)


def measurement_lines(m, limit=12):
    """measurements() as lines to print: after a retry, first one line saying so; then DIFFERED_LINE
    followed by "nowhere." or by one line per
    difference (each diff cut to limit lines) and, under BRIEFS_LINE, the task texts that differ;
    then a line when the lead agent gave no report, did not say whether it set the time limit, or did
    not print its workflow, and, when the message gave no task texts, the task texts the lead agent
    wrote (each cut to limit lines)."""

    def shown(diff):
        more = [
            f"    ... {len(diff) - limit} more lines, in measurements.json in the records folder"
        ]
        return ["    " + line for line in diff[:limit]] + (more if len(diff) > limit else [])

    lines = []
    expected_runs = 2 if m.get("retried") else 1
    if m["runs"] != expected_runs:
        wanted = "one, and the notebook asked for one more" if m.get("retried") else "one"
        lines.append(
            f"- the lead agent started {plural(m['runs'], 'workflow run')} (the message asks for {wanted})"
        )
    asked = ", ".join(m["phases_asked"]) or "no phases"
    for name, phases in zip(m["name_run"], m["phases_run"], strict=False):
        if m["name_asked"] is not None and name != m["name_asked"]:
            lines.append(f'- the run was named "{name}" (the message asks for "{m["name_asked"]}")')
        if m["phases_asked"] and phases != m["phases_asked"]:
            ran = ", ".join(phases) or "none"
            lines.append(f"- the run's phases were {ran} (the message asks for {asked})")
    analyzer, organizer = m["agents"]["analyzer"], m["agents"]["organizer"]
    if analyzer and m["runs"]:
        # The message asks for one analyzer thread per input file (the platform's retry of a failed
        # attempt adds one, so only fewer threads than files is a difference) and, when it states a
        # cap, at most that many of them at once.
        count = m["threads_by_agent"].get(analyzer, 0)
        most = m["most_at_once"].get(analyzer, 0)
        if count < m["inputs"]:
            lines.append(
                f"- {plural(count, analyzer + ' thread')} ran, for {plural(m['inputs'], 'input file')}"
            )
        if m["concurrency_limit"] is not None and most > m["concurrency_limit"]:
            lines.append(
                f"- up to {most} {analyzer} threads were at work at once, by this notebook's event "
                f"times (the message asks for at most {m['concurrency_limit']})"
            )
    if m["organizer_missing"]:
        lines.append(
            f"- the {organizer} never ran (the message asks for it once, after the analyzers)"
        )
    if m["organizer_before_analyzers_ended"]:
        lines.append("- the organizer's thread started before the last analyzer thread had ended")
    said, minutes = m["time_limit_minutes_said"], m["time_limit_minutes_asked"]
    if said is not None and minutes is not None and said != minutes:
        lines.append(
            f"- the lead agent says it gave the run a time limit of {said} minutes (the message "
            f"asks for {minutes})"
        )
    if minutes is not None and m["time_limit_set"] is False:
        lines.append(
            "- the lead agent's report says it started the run without the time limit the message "
            "asks for"
        )
    brief_lines = []
    for name, row in m["briefs"].items():
        if row["changed"]:
            first = row["changed"][0]
            which = f"; the diff is for {first['input']}" if first["input"] else ""
            brief_lines.append(
                f"- {len(row['changed'])} of {plural(row['threads'], name + ' thread')}{which} "
                "(- the notebook's, + received):"
            )
            brief_lines += shown(first["diff"])
        if row["no_input_named"]:
            brief_lines.append(
                f"- {plural(row['no_input_named'], name + ' thread')} received a task that names "
                "none of the input files"
            )
    if brief_lines:
        lines += [BRIEFS_LINE, *brief_lines]
    lines = [DIFFERED_LINE + " nowhere."] if not lines else [DIFFERED_LINE, *lines]
    if m.get("retried"):  # said first, before where the counted run differed
        then = "that run is the one counted here" if m["runs"] > 1 else "it started none"
        lines.insert(
            0,
            "The lead agent's report on the first run counted no transcript as processed, so the "
            f"notebook asked once for a new run; {then}.",
        )
    if not m["report_given"]:
        lines.append("The lead agent's reply held no JSON report.")
    elif minutes is not None and m["time_limit_set"] is None and said is None:
        lines.append(
            "The lead agent did not say whether it set the run's time limit (the run's events do "
            "not carry it)."
        )
    for name, text in (m.get("tasks_written") or {}).items():
        # The message gave no task texts, so these are the lead agent's own words, shown as a record.
        one = name == (m.get("agents") or {}).get("organizer")  # the organizer runs once
        which = f"the {name} thread" if one else f"the first {name} thread"
        lines.append(f"The task the lead agent wrote for {which}, in its own words:")
        lines += shown(text.strip().splitlines() or [""])
    if not m["workflow_printed"] and m["workflow_asked"]:
        lines.append(
            "Asked for the workflow it wrote, the lead agent gave no code block; its reply is in "
            "workflow_from_agent.md in the records folder."
        )
    elif not m["workflow_printed"]:
        lines.append(
            "The lead agent was not asked for the workflow it wrote (no run ended with the "
            "session idle)."
        )
    return lines


STUB = re.compile(r"MOVED TO \[\[([^\]\n]+)\]\]\.?")


def as_datetime(value):
    """A timezone-aware datetime from a datetime or an ISO 8601 string (a trailing Z allowed)."""
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def slugs_for(path):
    """The slugs a memory file answers to: its file name without .md, and its whole path with the folders joined
    by hyphens (tidewick/overview.md answers to "overview" and to "tidewick-overview")."""
    p = Path(path).with_suffix("")
    parts = [x for x in p.parts if x not in ("/", "")]
    return {p.name, "-".join(parts)}


def find_stubs(client, store_id, memories=None, only=None):
    """The placeholder files the organizer leaves behind when it merges or renames a file, since its tools can't
    delete: memories whose whole content is exactly one "MOVED TO [[slug]]" line. only, if given, limits the
    search to those memory ids (nothing else is read). Returns (memory, target slug, target exists) triples;
    the target exists when some other memory answers to that slug (slugs_for)."""
    memories = list_memories(client, store_id) if memories is None else memories
    answers = [(o.path, slugs_for(o.path)) for o in memories]
    stubs = []
    for m in memories:
        if m.content_size_bytes > 300 or (only is not None and m.id not in only):
            continue
        full = client.beta.memory_stores.memories.retrieve(
            m.id, memory_store_id=store_id, view="full"
        )
        match = STUB.fullmatch((full.content or "").strip())
        if not match:
            continue
        target = match.group(1).strip()
        exists = any(target in slugs and path != m.path for path, slugs in answers)
        stubs.append((full, target, exists))
    return stubs


def sweep_stubs(client, store_id, session_id, since):
    """Delete each placeholder file that THIS session wrote at or after since (pass the organizer
    thread's start; in a run shaped as the message asks, no analyzer writes after it), whose whole
    content is one "MOVED TO [[slug]]" line naming a memory
    that exists, and whose content is unchanged since it was read (the delete carries its hash). Returns
    (removed, left): removed as (path, target) pairs; left as (path, target, why) for placeholders whose
    target does not exist ("missing target") or whose delete failed (the error's text)."""
    start = as_datetime(since)
    versions = written_by_session(client, store_id, session_id)
    mine = {v.memory_id for v in versions if as_datetime(v.created_at) >= start}
    removed, left = [], []
    for memory, target, exists in find_stubs(client, store_id, only=mine):
        if not exists:
            left.append((memory.path, target, "missing target"))
            continue
        try:
            client.beta.memory_stores.memories.delete(
                memory.id, memory_store_id=store_id, expected_content_sha256=memory.content_sha256
            )
            removed.append((memory.path, target))
        except anthropic.APIError as exc:
            print(
                f"Could not delete the placeholder file {memory.path} ({exc}); it is still in the store."
            )
            left.append((memory.path, target, str(exc)))
    return removed, left


# --- Cleaning up ------------------------------------------------------------------------------------


def remove(what, call, *args, later=None, **kwargs):
    """Call one clean-up function; on an API error print what failed and, if given, the call that does it
    later, instead of raising, so the rest of the clean-up still runs. Returns whether the call succeeded."""
    try:
        call(*args, **kwargs)
        return True
    except anthropic.APIError as exc:
        print(f"Could not {what} ({exc})." + (f" To do it later, run: {later}" if later else ""))
        return False
