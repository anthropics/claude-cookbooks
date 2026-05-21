# BoxLite demo — Self-Hosted Sandboxes

Reference implementation of the [usage guide](../docs/usage-guide.md) on a self-hosted [BoxLite](https://github.com/boxlite-ai/boxlite) server. `boxlite_sandbox_webhook.py` is a FastAPI app that handles the `session.status_run_started` webhook (verified with `client.beta.webhooks.unwrap()`), **drains the environment work queue** with `client.beta.environments.work.poller(drain=True, auto_stop=False)` so any single delivery recovers earlier missed ones, and per item creates a BoxLite microVM, uploads the **same provider-agnostic `sandbox_runner.py`** the Modal demo uses, and starts it. BoxLite microVMs are full Linux environments running on Firecracker-style virtualization, so `beta_agent_toolset_20260401` (bash/read/write/edit/glob/grep) works as-is.

No org API key reaches the runner: the webhook polls with the environment key, and each microVM authenticates with that same environment key — the single credential for both the control plane and the per-session calls.

BoxLite is self-hosted: you run `boxlite serve` on infrastructure you control (your laptop for development, or a VM/host you own for production). The webhook handler talks to that server over REST. No managed BoxLite endpoint is required.

```sh
# standardwebhooks backs `client.beta.webhooks.unwrap()` — only the orchestrator
# host needs it; the inner BoxLite microVM never sees raw webhook deliveries.
pip install fastapi uvicorn boxlite standardwebhooks anthropic

# Start boxlite serve in another terminal (or on a separate host that the
# orchestrator can reach):
#   boxlite serve --port 8100
# The reference configuration accepts `local-dev-key` as the bearer.

export BOXLITE_REST_URL=http://localhost:8100  # default; override for remote
export BOXLITE_API_KEY=local-dev-key            # default; override if changed

export ANTHROPIC_WEBHOOK_SECRET=whsec_... \
       ANTHROPIC_ENVIRONMENT_ID=env_... \
       ANTHROPIC_ENVIRONMENT_KEY=sk-ant-oat...

uvicorn boxlite_sandbox_webhook:app --host 0.0.0.0 --port 8080
```

Deploy the FastAPI app anywhere that can serve HTTP and reach the BoxLite server (Fly, Render, a VM, or the same host as `boxlite serve`), then register its URL as the webhook endpoint.

> **Cold-start note:** `_spawn()` runs `pip install anthropic` inside each fresh microVM, which adds ~5–10 s before the runner starts. For production, pre-bake the SDK into a custom image (`boxlite build` or your own Dockerfile pushed to the BoxLite image cache) and drop the `pip install` line.

> **Workspace persistence:** unlike Modal's `Volume`, this variant does not mount a per-session persistent workspace. Skills are downloaded fresh each time a microVM is created. If a session reuses a live microVM (idempotent re-delivery while the previous runner is still alive), state persists. Production deployments that need cross-microVM session persistence should attach a host-side directory via `BoxOptions(volumes=[(host_dir, "/workspace", "rw")])`.

## How idempotency works

If a webhook delivery covers a session whose previous microVM is **still running** (`state.status == "running"` for a box named `anthropic-session-<session_id>`), `_spawn()` is skipped — the live runner picks up the new session events via the SSE stream. If the previous microVM has exited (the runner self-terminates 60 s after `session.status_idle`), a fresh one is created. This matches the Daytona variant's `_find_live` pattern.
