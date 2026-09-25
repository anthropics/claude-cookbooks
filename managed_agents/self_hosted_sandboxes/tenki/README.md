# Tenki Sandbox demo - Self-Hosted Sandboxes

This is a reference implementation of the [usage guide](../docs/usage-guide.md) on [Tenki Sandbox](https://pypi.org/project/tenki/).
`tenki_sandbox_webhook.py` is a FastAPI app that handles the `session.status_run_started` webhook and verifies it with `client.beta.webhooks.unwrap()`.
It drains the environment work queue with `client.beta.environments.work.poller(drain=True, auto_stop=False)`, then creates or reuses a Tenki Sandbox for each item.
Each sandbox receives the same provider-agnostic `sandbox_runner.py` that the Modal demo uses.

No org API key reaches the runner.
The webhook polls with the environment key, and each sandbox runner authenticates with that same environment key.

## Files

- `tenki_sandbox_webhook.py` verifies the webhook, drains the queue, creates or resumes a tagged Tenki Sandbox, uploads the Python runner, and launches it for the claimed work item.

## Prerequisites

- A Tenki API token in `TENKI_AUTH_TOKEN` or `TENKI_API_KEY`.
- A registered Anthropic self-hosted environment and its environment key.
- Python 3.11 or newer.

The Tenki API token determines the workspace automatically, so no workspace or project ID is required.

## Configure

```sh
pip install fastapi uvicorn standardwebhooks anthropic tenki

export TENKI_AUTH_TOKEN=...
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
export TENKI_SANDBOX_RESUME_TIMEOUT_SECONDS=180
export TENKI_SANDBOX_STICKY=false
```

## Run

```sh
uvicorn tenki_sandbox_webhook:app --host 0.0.0.0 --port 8080
```

Deploy the FastAPI app anywhere that can serve HTTP and reach the Tenki API, then register its URL as the webhook endpoint for `session.status_run_started`.

## Test

Create a session pointing at your environment ID and send it a message:

```py
session = client.beta.sessions.create(agent=agent_id, environment_id=ENVIRONMENT_ID)
client.beta.sessions.events.send(session.id, events=[{"type": "user.message", "content": "ls -la"}])
```

You should see these events in order:

```sh
# FastAPI host logs
[webhook] work=work_... session=sesn_... sandbox=... (created)

# Inside the Tenki Sandbox, from its default workdir
cat workspace/anthropic-runner.log
# [runner] INFO ...
```

## Notes

- The webhook uses the native async Tenki client so sandbox operations do not block the FastAPI event loop.
- The webhook tags each Tenki Sandbox as `anthropic-session:<session_id>` and reuses or resumes it on later deliveries for the same Anthropic session.
- If the sandbox is still running but the previous runner idled out, the webhook starts a fresh runner in the same filesystem.
- Tenki resolves relative filesystem and process paths under the image workdir, so this demo uses `workspace/` relative to that directory.
- The default Tenki image resolves the runner workdir to `/home/tenki/workspace`.
- `_start_runner()` installs `anthropic` inside a sandbox if it is missing, which adds cold-start time.
- For production, publish a Tenki image with `anthropic` preinstalled and set `TENKI_SANDBOX_IMAGE`.
- Tune `max_duration`, `idle_timeout_minutes`, `pause_retention`, and `sticky` to match your session length and cost posture.
