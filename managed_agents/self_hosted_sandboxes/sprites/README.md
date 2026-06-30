# Sprites demo — Self-Hosted Sandboxes

Reference implementation of the [usage guide](../docs/usage-guide.md) on [Sprites](https://sprites.dev) (Fly.io's stateful sandboxes). Per claimed session it creates a Sprite, uploads the **same provider-agnostic `sandbox_runner.py`** the Modal and Daytona demos use, and starts it. A Sprite is a full Linux environment, so `beta_agent_toolset_20260401` (bash/read/write/edit/glob/grep) works as-is.

Two ways to drive it, both calling the shared `sprite_sandbox.spawn()`:

- **`sprites_webhook.py`** — a FastAPI app that handles the `session.status_run_started` webhook (verified with `client.beta.webhooks.unwrap()`) and **drains the work queue** with `client.beta.environments.work.poller(drain=True, auto_stop=False)`, so any single delivery recovers earlier missed ones. No idle poller, but needs a public HTTPS endpoint.
- **`sprites_poller.py`** — an [always-on](https://platform.claude.com/docs/en/managed-agents/self-hosted-sandboxes#always-on-sdk) process that polls the queue continuously (`drain` omitted) and spawns a Sprite per session. No public endpoint, only outbound HTTPS.

Sprites has no published SDK, so the demo talks its REST API directly: `POST /v1/sprites` (create), `PUT /v1/sprites/{name}/fs/write` (upload the runner and an env file), `POST /v1/sprites/{name}/exec` (install the SDK), and `PUT /v1/sprites/{name}/services/...` to start the runner. The runner runs as a **service** rather than a detached `nohup` — Sprites reaps an exec's process tree when the request closes, so a service (supervised, outlives the request) is the right primitive; it self-stops on exit so the one-shot worker isn't restarted. The `ANTHROPIC_*` env vars (the same contract `ant beta:worker poll --on-work` sets) are written to a file the service sources, so the environment key never appears in process listings.

No org API key reaches the runner: the orchestrator polls with the environment key, and each Sprite authenticates with that same environment key — the single credential for both the control plane and the per-session calls.

```sh
# A Sprites API token (org/projectNumber/tokenId/secret). SPRITES_API_URL is
# optional and defaults to https://api.sprites.dev.
export SPRITES_API_KEY=...
export ANTHROPIC_ENVIRONMENT_ID=env_... ANTHROPIC_ENVIRONMENT_KEY=sk-ant-oat...

# Always-on poller (no public endpoint):
pip install httpx anthropic
python sprites_poller.py

# OR webhook (needs a public HTTPS endpoint). standardwebhooks backs
# `client.beta.webhooks.unwrap()` — only the orchestrator host needs it; the
# inner Sprite never sees raw webhook deliveries.
pip install fastapi uvicorn httpx standardwebhooks anthropic
export ANTHROPIC_WEBHOOK_SECRET=...
uvicorn sprites_webhook:app --host 0.0.0.0 --port 8080
```

Deploy either anywhere that can reach the Sprites API (Fly, Render, a VM behind a tunnel, etc.); for the webhook, register its URL as the webhook endpoint.

> **Cold-start note:** `spawn()` runs `python3 -m pip install anthropic` inside each fresh Sprite, which adds ~10–15s before the runner starts. For production, bake the SDK into a Sprite [checkpoint](https://docs.sprites.dev/concepts/checkpoints/) and drop the `pip install` line.
