# AgentCore Runtime demo — Self-Hosted Sandboxes

Same `ant beta:worker run` entrypoint as the [`docker/`](../docker/) demo,
but the per-session container is replaced by an **Amazon Bedrock AgentCore
Runtime microVM** addressed by `runtimeSessionId == ANTHROPIC_SESSION_ID`.
Session affinity routes every turn for one Anthropic session to the same
microVM, giving the docker variant's per-session-container property without
running a host of your own.

The host runs `ant beta:worker poll` directly (no webhook); per claimed
work item its `--on-work` script (`on-work.sh` → `on-work.py`) calls
`bedrock-agentcore.invoke_agent_runtime` with the work metadata in the
payload. AgentCore routes to the microVM that owns that session, where
`server.py` (an `@app.entrypoint` HTTP handler) reads the payload, exports
the `ANTHROPIC_*` env vars, and execs `ant beta:worker run` to attach to
that one session — same CLI, same env contract, same `bash`/`read`/`write`/
`edit`/`glob`/`grep` toolset as the `docker/` variant. The CLI owns
heartbeat, backlog reconcile, SSE, and the work-item force-stop on exit.

Idle policy is the SDK default: each microVM exits 60s after
`session.status_idle` with `stop_reason: end_turn`; any other event —
including `requires_action` idle, where the agent is blocked on the
sandbox — resets the clock. AgentCore then idles the microVM; the next turn
for that session reuses session affinity and warms it up again, so the
agent's working tree under `/workspace` is still there.

No org API key reaches the runner. The host poller uses the environment key
to claim work, and that same key is forwarded inside the
`invoke_agent_runtime` payload and re-exported in the microVM as
`ANTHROPIC_ENVIRONMENT_KEY` (the per-session calls — event stream, lease
heartbeat, force-stop) **and** as `ANTHROPIC_AUTH_TOKEN` (the CLI's
skill-download client only resolves `ANTHROPIC_API_KEY` /
`ANTHROPIC_AUTH_TOKEN`, not `ANTHROPIC_ENVIRONMENT_KEY` — without it skills
silently fail to download). `ANTHROPIC_API_KEY` is only used by
`bootstrap.py` to create the environment + agent; no other component reads
it.

Unlike the webhook-driven demos (Modal/Daytona/Vercel/Cloudflare), there is
no webhook here — `ant beta:worker poll` long-polls Anthropic directly and
translates each work item into one `invoke_agent_runtime` call against the
host's AWS credentials. Nothing needs to be exposed to the internet.

## Files

In the microVM:

- `Dockerfile` — the per-microVM image: pinned `ant` CLI, `python3` +
  `bedrock-agentcore` SDK, `WORKDIR /workspace`. Entrypoint is
  `server.py`, not `ant`. The host poller never enters this image.
- `server.py` — AgentCore HTTP entrypoint
  (`BedrockAgentCoreApp` `@app.entrypoint`). Per `invoke_agent_runtime`
  call, reads `session_id` / `work_id` / `environment_id` /
  `environment_key` from the payload, exports them as the env vars
  `ant beta:worker run` reads, and execs the CLI with
  `--workdir /workspace --max-idle 60s`.
- `requirements.txt` — container deps (`bedrock-agentcore`).

On the host:

- `bootstrap.py` — one-time setup against `api.anthropic.com` (uses
  `ANTHROPIC_API_KEY`): creates the self-hosted environment, creates an
  agent with `agent_toolset_20260401`, and prompts you to paste the
  Console-generated environment key. Writes `bootstrap.config`.
  Idempotent.
- `setup.sh` — provisions the AWS infrastructure for the runtime: ECR
  repository (idempotent), arm64 image build, ECR push. Writes
  `envvars.config`.
- `deploy.py` — creates the IAM execution role and the AgentCore Runtime
  in `PUBLIC` network mode (no VPC, no NAT, no S3 Files for this minimal
  demo). Waits until the runtime status is `READY` and writes
  `runtime_config.json`.
- `cleanup.py` — tears down the runtime, IAM execution role, and ECR
  images (`--delete-repo` to drop the repo too). Anthropic-side
  resources are intentionally untouched; archive them separately with
  `ant beta:agents archive` / `ant beta:environments archive`.
- `on-work.py` — host-side `--on-work` bridge. Reads the
  `ANTHROPIC_{WORK_ID,ENVIRONMENT_ID,SESSION_ID,ENVIRONMENT_KEY}` the
  poller sets, drains the work JSON on stdin, and calls
  `boto3.invoke_agent_runtime` with `runtimeSessionId =
  ANTHROPIC_SESSION_ID`.
- `on-work.sh` — thin wrapper (the poller's `--on-work` takes a single
  executable; this one execs `python3 on-work.py`).
- `start.sh` — host launcher: `ant beta:worker poll --on-work on-work.sh`.
- `tui_exec.py` — operator TUI, one-shot. Calls
  `InvokeAgentRuntimeCommand` against the same microVM as a running
  Anthropic session (matched by `runtimeSessionId`) and streams stdout /
  stderr / exit deltas back over HTTP. Useful for `ls /workspace` or
  `cat <path>` while the agent is mid-turn.
- `tui_shell.py` — operator TUI, interactive PTY over WebSocket
  (`InvokeAgentRuntimeCommandShell`, via the `bedrock-agentcore` SDK's
  `AgentCoreRuntimeClient.open_shell()`). Local terminal attaches to a
  real bash PTY in the microVM with line editing, Ctrl+C, and `SIGWINCH`
  resize. Pass `--shell-id` with the same `--runtime-session-id` to
  reconnect to the same PTY (the service replays up to 256 KB of buffered
  output); up to 10 concurrent shells per runtime.
- `requirements-host.txt` — host deps (`anthropic`, `boto3`,
  `bedrock-agentcore`).

## Prerequisites

- An AWS account with [AgentCore Runtime](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime.html)
  available in your region, AWS credentials with permissions to create
  IAM roles, ECR repositories, and AgentCore runtimes (and
  `bedrock-agentcore:InvokeAgentRuntime` on the deployed runtime ARN; the
  TUI clients additionally need `InvokeAgentRuntimeCommand` for one-shot
  exec and `InvokeAgentRuntimeCommandShell` for the interactive PTY).
- `python3` + `pip install -r requirements-host.txt`.
- `docker` (or a buildx-equivalent like `finch`) capable of `linux/arm64`
  cross-builds — AgentCore Runtime is Graviton-only.
- An Anthropic API key for `bootstrap.py` (used once to create the
  environment + agent and **never reaches the runtime**).
- `ant` on the host's PATH, the **same build** pinned in `Dockerfile`
  (`ARG ANT_VERSION`). Install:

  ```sh
  VERSION=1.9.1
  OS=$(uname -s | tr '[:upper:]' '[:lower:]')
  ARCH=$(uname -m | sed -e 's/x86_64/amd64/' -e 's/aarch64/arm64/')

  # linux: tarball
  curl -fsSL "https://github.com/anthropics/anthropic-cli/releases/download/v${VERSION}/ant_${VERSION}_${OS}_${ARCH}.tar.gz" \
    | sudo tar -xz -C /usr/local/bin ant

  # macOS: zip — `ant_${VERSION}_macos_${ARCH}.zip`
  # curl -fsSL "https://github.com/anthropics/anthropic-cli/releases/download/v${VERSION}/ant_${VERSION}_macos_${ARCH}.zip" \
  #   -o /tmp/ant.zip && unzip -p /tmp/ant.zip ant | sudo tee /usr/local/bin/ant >/dev/null && sudo chmod +x /usr/local/bin/ant

  ant --version
  ```

## Bootstrap (one time)

Create the Anthropic-side resources. The script uses your API key once,
prints the Console URL where the environment key is generated, and waits
for you to paste it back:

```sh
pip install -r requirements-host.txt
export ANTHROPIC_API_KEY=sk-ant-api03-...
python3 bootstrap.py
```

Outputs `bootstrap.config` with `ANTHROPIC_ENVIRONMENT_ID`,
`ANTHROPIC_ENVIRONMENT_KEY`, and `ANTHROPIC_AGENT_ID`. The API key is no
longer used after this; `start.sh`, the runtime, and every subsequent step
authenticate with the environment key alone.

The default model is `claude-haiku-4-5`; override with
`ANTHROPIC_AGENT_MODEL=claude-sonnet-4-6` (or any other supported model)
before running.

## Deploy the runtime

Build and push the image, then create the runtime:

```sh
./setup.sh us-west-2     # ECR repo + arm64 image build/push -> envvars.config
python3 deploy.py        # IAM role + AgentCore Runtime    -> runtime_config.json
```

Capture the runtime ARN for the next step:

```sh
export AGENTCORE_RUNTIME_ARN=$(python3 -c 'import json; print(json.load(open("runtime_config.json"))["runtime_arn"])')
export AGENTCORE_REGION=us-west-2
```

## Run

Source the bootstrap config and start the host poller:

```sh
source bootstrap.config
./start.sh
```

Then create a session pointing at that `ANTHROPIC_ENVIRONMENT_ID` and send
it a message. You should see, in order:

```
[start]    polling env=env_... runtime=arn:aws:bedrock-agentcore:...
{"msg":"claimed work","work_id":"sesn_...","work_type":"session"}
{"msg":"spawning on-work script","script":".../on-work.sh","work_id":"sesn_..."}
[on-work]  session=sesn_... -> invoke_agent_runtime
```

Inside the microVM (CloudWatch
`/aws/bedrock-agentcore/runtimes/<runtime-id>-DEFAULT`):

```
[server]   runtimeSessionId=sesn_...-000 anthropicSessionId=sesn_... workId=sesn_...
{"msg":"executing tool","session_id":"sesn_...","tool":"bash"}
{"msg":"dispatched tool","session_id":"sesn_...","tool":"bash","is_error":false,"posted":true}
```

After end_turn idle:

```
[on-work]  session=sesn_... done in N.Ns status=200
```

## Inspect a running session (TUI)

While the agent is working, you can attach an operator shell to the *same*
microVM by reusing the Anthropic session id as `runtimeSessionId` —
session affinity routes both the agent's `invoke_agent_runtime` and your
`invoke_agent_runtime_command` to the same VM. This is the part the other
self-hosted-sandbox compute variants here cannot offer; their per-session
container has no operator surface.

One-shot HTTP streaming:

```sh
python3 tui_exec.py --runtime-session-id "$SESSION_ID" -- "ls -la /workspace"
python3 tui_exec.py --runtime-session-id "$SESSION_ID" -- "cat /workspace/<file>"
```

`InvokeAgentRuntimeCommand` runs each call as a single argv (no shell
expansion). Wrap pipelines or redirects in `bash -c`:

```sh
python3 tui_exec.py --runtime-session-id "$SESSION_ID" -- bash -c 'ls /workspace && cat /workspace/result.json'
```

Interactive PTY via `InvokeAgentRuntimeCommandShell` — full bash session
with line editing, Ctrl+C, and resize:

```sh
python3 tui_shell.py --runtime-session-id "$SESSION_ID"
```

`tui_shell.py` prints the `shellId` it opened. To reconnect to the *same*
PTY after a disconnect (the service replays up to 256 KB of recent
output), pass it back alongside the same session id:

```sh
python3 tui_shell.py --runtime-session-id "$SESSION_ID" --shell-id <shellId>
```

`AGENTCORE_RUNTIME_ARN` and `AGENTCORE_REGION` are picked up from the
environment, same as `start.sh`. The TUI clients use the standard AWS SDK
/ SigV4 — no Anthropic credentials reach them, they run purely in the AWS
data plane.

> **Interactive shells require a runtime created or updated on/after
> 2026-06-05.** The `InvokeAgentRuntimeCommandShell` API (and the
> `open_shell()` SDK call `tui_shell.py` uses) only works on runtimes at
> the post-launch platform version; older runtimes return an error on
> connect. If you deployed before then, re-run `python3 deploy.py` (or
> `aws bedrock-agentcore-control update-agent-runtime …` against the same
> image) to roll the runtime to a new version. The one-shot
> `tui_exec.py` path (`InvokeAgentRuntimeCommand`) is unaffected. The
> caller also needs `bedrock-agentcore:InvokeAgentRuntimeCommandShell`
> (interactive) and `bedrock-agentcore:InvokeAgentRuntimeCommand`
> (one-shot) on the runtime ARN.

Window: `/workspace` lives inside the microVM and is evicted when the
microVM is reclaimed (60s after `session.status_idle` with
`stop_reason: end_turn`, sooner if the runtime needs the slot). Operator
inspection has to happen while the agent is mid-turn or within that idle
window.

## Cleanup

```sh
python3 cleanup.py                  # runtime + IAM role + ECR images (repo kept)
python3 cleanup.py --delete-repo    # also drop the ECR repo
```

```sh
ant beta:agents archive --agent-id "$ANTHROPIC_AGENT_ID"
ant beta:environments archive --environment-id "$ANTHROPIC_ENVIRONMENT_ID"
```

## Notes

- **microVM cold start** is ~5–15s the first time AgentCore has to launch
  one for a session — image pull + container start + `server.py` boot +
  `ant beta:worker run` initial SSE connect. Subsequent turns for the
  same session reuse session affinity and skip most of that.
  `invoke_agent_runtime` blocks until the in-microVM
  `ant beta:worker run` exits (idle timeout after `end_turn`), so the
  host poller waits for the duration of the turn before claiming the
  next work item; this matches `docker/`, where `docker run` is also
  blocking from the poller's point of view.
- **Persistent `/workspace`** — `/workspace` lives inside the microVM and
  persists for the lifetime of the session (every turn for one session
  lands on the same microVM via
  `runtimeSessionId == ANTHROPIC_SESSION_ID`). When the session ends or
  AgentCore evicts the microVM, the working tree is gone. For persistent
  `/workspace` shared *across* sessions, attach an EFS or S3 Files mount
  to the runtime — the contract here is unchanged, `ant` always writes
  to `/workspace`. The
  `aws-samples/agentcore-samples` siblings
  [`01-claude-code-with-s3-files`](https://github.com/awslabs/agentcore-samples/tree/main/01-features/02-host-your-agent/01-runtime/04-coding-agents/01-claude-code-with-s3-files)
  and
  [`02-claude-code-with-efs`](https://github.com/awslabs/agentcore-samples/tree/main/01-features/02-host-your-agent/01-runtime/04-coding-agents/02-claude-code-with-efs)
  show the mount setup; the same `filesystemConfigurations[]` block
  drops in unchanged on top of this image.
- **Container build, not direct code deploy.** AgentCore Runtime supports
  both, but the `ant` CLI is a native Go binary and skill download
  invokes arbitrary host tools (`git`, `curl`, `bash`). Container is
  the only mode that supports this without re-architecting upstream.
- **Single in-flight session per poller process.** `ant beta:worker
  poll` claims one work item at a time and waits for `--on-work` to
  return, so concurrent sessions need either multiple poller processes
  on the host or `--on-work` returning immediately. AgentCore's
  session-affinity routing handles independent sessions in parallel as
  long as the poller hands off fast enough; for high concurrency, fan
  out the poll loop across processes (one per CPU is plenty for this
  shape) — each process's `ANTHROPIC_WORKER_ID` is automatically the
  hostname suffixed by PID, and the work queue is shared across them.
