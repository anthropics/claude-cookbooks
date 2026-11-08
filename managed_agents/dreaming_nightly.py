"""Run CMA_dreaming_with_a_dynamic_workflow.ipynb every night ("Dream every night"): export the agent's sessions
since the last run and distill them into the memory store the agent reads. Set two things in the cron job's environment,
on the crontab line as the notebook's "Dream every night" section shows:

  COOKBOOK_AGENT_ID   the agent whose finished sessions feed the store
  COOKBOOK_STORE_ID   the memory store to update in place (printed after "Memory store:" on the first run)

Credentials are found as the notebook finds them (ANTHROPIC_API_KEY or .env next to the notebook, otherwise your
ant auth login profile); the sessions the notebook starts never see them. This script skips the notebook's
"%pip install" cell, so a night installs nothing: install the packages yourself in the Python that runs this
script (anthropic 2.x and python-dotenv for the notebook; nbformat, nbclient and ipykernel for this script;
running the notebook once by hand does the first two).
COOKBOOK_SINCE (an ISO timestamp), if you set it, is where one run's window starts, in place of the last
run's start (on the first night, 24 hours ago); the notebook reads all three.
Exit status 0 when the notebook ran to the end (or had no transcripts to distill), 1 when it stopped (an earlier cell
stopped it, e.g. a session that could not be exported, or the clean-up cell raises when a transcript was not analyzed, a run did not complete, the organizer did not finish,
or the agent reported a failure); a failed night keeps its window, so the next night takes it again.
"""

import json
import os
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import nbformat
from nbclient import NotebookClient

HERE = Path(__file__).resolve().parent
CACHE = Path.home() / ".cache" / "memory_distill"
STATE = CACHE / "nightly.json"  # holds where the next run's window starts
INSTALL_CELL = ("%pip install", "%%capture\n%pip install")  # how the notebook's install cell begins


def main():
    agent_id, store_id = os.environ.get("COOKBOOK_AGENT_ID"), os.environ.get("COOKBOOK_STORE_ID")
    # An empty one would make the notebook distill its examples, or create a new store each night.
    if not agent_id or not store_id:
        sys.exit(
            "Set COOKBOOK_AGENT_ID and COOKBOOK_STORE_ID on the crontab line (see the top of dreaming_nightly.py)."
        )
    started = datetime.now(UTC)
    state = json.loads(STATE.read_text()) if STATE.exists() else {}
    # Sessions created since the last run started; on the first night, the last 24 hours.
    given = os.environ.get("COOKBOOK_SINCE")  # your own window start, if you set one
    since = given or state.get("last_run") or (started - timedelta(days=1)).isoformat()
    out = CACHE / "nightly" / f"{started:%Y-%m-%dT%H%M%S}Z.ipynb"  # the night's log
    out.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    nb = nbformat.read(HERE / "CMA_dreaming_with_a_dynamic_workflow.ipynb", as_version=4)
    # No unattended package installs: the notebook's one install cell is left out (the packages must
    # already be installed); anything other than exactly one such cell means the notebook changed shape.
    install = [
        c for c in nb.cells if c.cell_type == "code" and c.source.lstrip().startswith(INSTALL_CELL)
    ]
    if len(install) != 1:
        sys.exit(
            f"Expected one %pip install cell in the notebook, found {len(install)}; not running it."
        )
    nb.cells = [c for c in nb.cells if c is not install[0]]
    nothing = False  # set when the night had no transcripts to distill
    os.environ["COOKBOOK_SINCE"] = since  # the notebook's kernel reads it, with the two ids
    try:
        NotebookClient(nb, timeout=6 * 3600, resources={"metadata": {"path": str(HERE)}}).execute()
        done = True
    except Exception as exc:
        # A cell raised or timed out, or the kernel died; NothingToDistill means no transcripts to distill.
        name = getattr(exc, "ename", type(exc).__name__)
        done = nothing = name == "NothingToDistill"
        if not nothing:
            print(f"The notebook stopped: {name}: {getattr(exc, 'evalue', exc)}")
    finally:
        if given is None:
            del os.environ["COOKBOOK_SINCE"]  # leave the environment as it was
        else:
            os.environ["COOKBOOK_SINCE"] = given
        nbformat.write(nb, out)
        out.chmod(0o600)  # it holds memory text and transcript excerpts
    state["last_run"] = started.isoformat() if done else since  # a night not done keeps its window
    STATE.write_text(json.dumps(state, indent=1))
    STATE.chmod(0o600)
    if nothing:
        print(f"Nothing to distill: no finished session since {since} was exported. Log: {out}")
    elif done:
        print(f"The notebook ran to the end. Log: {out}")
    else:
        print(f"Stopped; the next run will take the same sessions again. Log: {out}")
    sys.exit(0 if done else 1)


if __name__ == "__main__":
    main()
