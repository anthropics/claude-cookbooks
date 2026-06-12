# Tenki Sandbox demo — Self-Hosted Sandboxes

Reference implementation of the [usage guide](../docs/usage-guide.md) on
[Tenki Sandbox](https://pypi.org/project/tenki-sandbox/). `tenki_sandbox_webhook.py`
is a FastAPI app that handles the `session.status_run_started` webhook
(verified with `client.beta.webhooks.unwrap()`), **drains the environment work
queue** with `client.beta.environments.work.poller(drain=True, auto_stop=False)`,
and per item creates or reuses a Tenki Sandbox, uploads the **same
provider-agnostic `sandbox_runner.py`** the Modal demo uses, and starts it
detached.

No org API key reaches the runner: the webhook polls with the environment key,
and each sandbox runner authenticates with that same environment key — the
single credential for both the control plane and the per-session calls.

## Files

- `tenki_sandbox_webhook.py` — FastAPI app: verify signature, drain the queue,
  create or resume a tagged Tenki Sandbox, upload the Python runner, and launch
  it for the claimed work item.

## Prerequisites

- A Tenki Sandbox API token (`TENKI_AUTH_TOKEN` or `TENKI_API_KEY`)
- A registered Anthropic self-hosted environment and its environment key
- Python 3.11+

## Configure

```sh
pip install fastapi uvicorn standardwebhooks anthropic tenki-sandbox

export TENKI_AUTH_TOKEN=...
export TENKI_PROJECT_ID=proj_...        # recommended so sandboxes appear under a project
export ANTHROPIC_WEBHOOK_SECRET=whsec_...
export ANTHROPIC_ENVIRONMENT_ID=env_...
export ANTHROPIC_ENVIRONMENT_KEY=sk-ant-oat...
```

Optional Tenki settings:

```sh
export TENKI_API_ENDPOINT=https://api.tenki.cloud
export TENKI_SANDBOX_IMAGE=workspace-slug/anthropic-runner:latest
export TENKI_SANDBOX_CPU_CORES=2
export TENKI_SANDBOX_MEMORY_MB=4096
export TENKI_SANDBOX_DISK_SIZE_GB=20
export TENKI_SANDBOX_IDLE_TIMEOUT_MINUTES=30
export TENKI_SANDBOX_MAX_DURATION_SECONDS=3600
export TENKI_SANDBOX_PAUSE_RETENTION_SECONDS=86400
```

## Run

```sh
uvicorn tenki_sandbox_webhook:app --host 0.0.0.0 --port 8080
```

Deploy the FastAPI app anywhere that can serve HTTP and reach the Tenki API
(Fly, Render, a VM behind a tunnel, etc.), then register its URL as the webhook
endpoint for `session.status_run_started`.

## Test

Create a session pointing at your environment id and send it a message:

```py
session = client.beta.sessions.create(agent=agent_id, environment_id=ENVIRONMENT_ID)
client.beta.sessions.events.send(session.id, events=[{"type": "user.message", "content": "ls -la"}])
```

You should see, in order:

```sh
# FastAPI host logs
[webhook] work=work_... session=sesn_... sandbox=... (created)

# Inside the Tenki Sandbox
cat /workspace/anthropic-runner.log
# [runner] INFO ...
```

## Notes

- The webhook tags each Tenki Sandbox as `anthropic-session:<session_id>` and
  reuses or resumes it on later deliveries for the same Anthropic session.
  If the sandbox is still running but the previous runner idled out, the
  webhook starts a fresh runner in the same filesystem.
- The runner workdir is `/workspace`, matching the other self-hosted sandbox
  demos. Skills download under `/workspace/skills/<name>/`.
- `_start_runner()` installs the `anthropic` package inside each fresh sandbox
  if it is missing, which adds cold-start time. For production, publish a Tenki
  Sandbox image with the package already installed and set `TENKI_SANDBOX_IMAGE`.
- `max_duration`, `idle_timeout_minutes`, and `pause_retention` are Tenki
  lifecycle settings. Tune them to match your session length and cost posture.
