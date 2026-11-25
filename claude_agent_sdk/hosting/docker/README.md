# Tier 1 — Local Docker

Runs the shared image locally. Two paths:

## Ephemeral (no server)

One prompt, one process, then exit. Good for job-shaped work (batch processing,
one-off analysis) where there's no conversation to resume.

```bash
cd claude_agent_sdk/
docker build -f hosting/Dockerfile -t research-agent .
docker run --rm \
  -e ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" \
  -e PROMPT="What is the Claude Agent SDK?" \
  research-agent
```

## Hybrid (with a server)

Starts the FastAPI server and mounts `./sessions` at `/data` so conversations
survive container restarts.

```bash
cd claude_agent_sdk/hosting/docker/
docker compose up --build
```

Then, from another shell:

```bash
curl -N -X POST http://localhost:8000/sessions/demo-1/messages \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"What are the latest AI agent trends?"}'

# Follow-up — the agent remembers the first turn:
curl -N -X POST http://localhost:8000/sessions/demo-1/messages \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"Tell me more about the second one."}'

curl http://localhost:8000/health
```

Stop the container, `docker compose up` again, send another follow-up — the
agent still has context because `./sessions` persisted `/data`.
