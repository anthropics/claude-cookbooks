"""Trigger a manual deployment run, stream it, and download the report.

Starts a session immediately, exactly as the schedule would, and records a
deployment run with `trigger_context.type: "manual"`. Use it to smoke-test
the deployment without waiting for the next cron tick.
"""

import time
from pathlib import Path

from cma import BETAS, client, require_env, stream_until_end_turn

CLAUDE_DEPLOYMENT_ID = require_env("CLAUDE_DEPLOYMENT_ID")

manual_run = client.beta.deployments.run(CLAUDE_DEPLOYMENT_ID)
print(f"run: {manual_run.id}")
print(f"session: {manual_run.session_id}")

# The run created a real session. Stream it like any other.
stream_until_end_turn(manual_run.session_id)

# The agent wrote to /mnt/session/outputs/, which the Files API captures
# automatically. Indexing can lag 1-3 seconds after the session goes idle,
# so retry an empty list a few times. scope_id is a Managed Agents beta
# parameter, so list via client.beta.files; download uses the GA client.files.
report_files = []
for _ in range(5):
    report_files = client.beta.files.list(
        scope_id=manual_run.session_id,
        betas=BETAS,
    ).data
    if report_files:
        break
    time.sleep(1)

if not report_files:
    print("\nno files found; check the transcript above for whether the agent wrote the report")

# The agent picked these filenames, and the agent reads attacker-controlled
# input (issue titles, stack traces). Strip any path components before
# writing to the local disk.
for f in report_files:
    local_name = Path(f.filename).name
    print(f"\n{f.filename}  ({f.size_bytes} bytes)")
    content = client.files.download(f.id)
    content.write_to_file(local_name)
    print(f"downloaded to ./{local_name}")
