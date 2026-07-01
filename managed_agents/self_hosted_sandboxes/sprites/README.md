# Sprites demo — Self-Hosted Sandboxes

Reference implementation of the [usage guide](../docs/usage-guide.md) on [Sprites](https://sprites.dev) (Fly.io's stateful sandboxes). Per claimed session it creates a Sprite, uploads its own copy of the **provider-agnostic `sandbox_runner.py`** (same code as the Modal and Daytona demos; the header documents the Sprites specifics), and starts it. A Sprite is a full Linux environment, so `beta_agent_toolset_20260401` (bash/read/write/edit/glob/grep) works as-is.

Two ways to drive it, both calling the shared `sprite_sandbox.spawn()`:

- **`sprites_webhook.py`** — a FastAPI app that handles the `session.status_run_started` webhook (verified with `client.beta.webhooks.unwrap()`) and **drains the work queue** with `client.beta.environments.work.poller(drain=True, auto_stop=False)`, so any single delivery recovers earlier missed ones. No idle poller, but needs a public HTTPS endpoint.
- **`sprites_poller.py`** — an [always-on](https://platform.claude.com/docs/en/managed-agents/self-hosted-sandboxes#always-on-sdk) process that polls the queue continuously (`drain` omitted) and spawns a Sprite per session. No public endpoint, only outbound HTTPS.

Sprites has no published SDK, so the demo talks its REST API directly: `POST /v1/sprites` (create), `PUT /v1/sprites/{name}/fs/write` (upload the runner and an env file), `POST /v1/sprites/{name}/exec` (install the SDK), and `PUT /v1/sprites/{name}/services/...` to start the runner. The runner runs as a **service** rather than a detached `nohup` — Sprites reaps an exec's process tree when the request closes, so a service (supervised, outlives the request) is the right primitive; it self-stops on exit so the one-shot worker isn't restarted. The `ANTHROPIC_*` env vars (the same contract `ant beta:worker poll --on-work` sets) are written to a file the service sources (not passed as service args), so the environment key never appears in process listings; the service deletes the file right after sourcing it so the key isn't left on the Sprite's disk.

A service is supervised but does not hold the Sprite in an active state: once a session is underway the runner only makes outbound calls, so the Sprite would pause after its short idle window and stall the session mid-turn. To keep it active, the service registers a [Task](https://docs.sprites.dev/keeping-sprites-running/) before launching the runner, refreshes it on a heartbeat shorter than its expiry, and deletes it when the runner exits. Task expiry is the crash-safety net: if the runner dies without cleaning up, the task lapses on its own and the Sprite is free to pause. (Because the self-stop terminates the service's own shell, the final service state reads `failed (exit 143)` — that's the expected terminal state; the service is not restarted.)

No org API key reaches the runner: the orchestrator polls with the environment key, and each Sprite authenticates with that same environment key — the single credential for both the control plane and the per-session calls.

```sh
# A Sprites API token (org-slug/org-id/token-id/token-value). SPRITES_API_URL
# is optional and defaults to https://api.sprites.dev.
export SPRITE_TOKEN=...
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

> **Cold-start note:** `spawn()` runs `python3 -m pip install anthropic` inside each fresh Sprite, which adds ~10–15s before the runner starts. A [checkpoint](https://docs.sprites.dev/concepts/checkpoints/) restores only into the same Sprite, so it can't pre-bake a brand-new Sprite; to drop the install cost in production, reuse a pool of prepared Sprites (restoring each Sprite's own checkpoint, SDK included, between sessions) instead of creating one per session.
