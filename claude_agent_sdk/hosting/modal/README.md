# Tier 2 — Modal

Runs the **same** `hosting/Dockerfile` image on [Modal](https://modal.com) via
`modal.Sandbox`. You get a public HTTPS URL, scale-to-zero, and no
infrastructure to manage.

## Prerequisites

```bash
pip install modal
modal setup            # opens a browser to authenticate
modal secret create anthropic ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY"
```

## Deploy

```bash
cd claude_agent_sdk/
python hosting/modal/modal_app.py
```

This builds the Dockerfile remotely on Modal (build context = `claude_agent_sdk/`,
same as local), starts a sandbox running `serve`, and prints a tunnel URL.

## Talk to it

The deploy script prints a `url:` and a `token:` line. The tunnel URL is public,
so the server requires the bearer token on the messages endpoint (only
`/health` is open):

```bash
curl -N -X POST "$MODAL_URL/sessions/demo-1/messages" \
  -H "Authorization: Bearer $MODAL_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"What are the latest AI agent trends?"}'
```

## Persistence

By default `modal_app.py` mounts a `modal.Volume` at `/data` — the same
`CLAUDE_CONFIG_DIR` trick as tier 1. Session transcripts survive sandbox
restarts.

> **Note:** `modal.Volume` has explicit commit semantics. If your workload has
> many sandboxes writing many sessions concurrently and you see lost writes,
> switch to a [`SessionStore`](https://code.claude.com/docs/en/agent-sdk/session-storage)
> backed by Modal `Dict` or an external store — that's also what tier 3 uses.

## Liveness

Modal keeps the sandbox running until the `timeout=` passed to `Sandbox.create`
expires; it does not probe `GET /health`. If the server inside dies, the sandbox
stays up and requests fail until the timeout reaps it. For anything longer-lived
than a demo, point your own monitoring at `/health` and recreate the sandbox
when it stops answering.

## Teardown

```bash
python hosting/modal/teardown.py
```

Stops sandboxes and removes the volume so you're not billed for idle resources.
