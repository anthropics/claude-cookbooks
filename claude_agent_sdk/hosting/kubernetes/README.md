# Tier 3 — Kubernetes (pod-per-session)

> Part of the [Agent SDK hosting cookbook](../../07_Hosting_the_agent.ipynb).
> If you haven't picked a hosting tier yet, start there — it covers when a
> managed option is the better fit and when you actually need this.

Run the agent on a Kubernetes cluster where every session gets its own
isolated pod, with network-level controls ensuring agent pods can only reach
the Anthropic API.

```
                     ┌──────────────────────────────────────────────────┐
                     │                  Kubernetes                      │
                     │                                                  │
  curl / SDK ──────► Gateway (FastAPI)                                  │
                     │  ├─ creates/deletes agent pods via K8s API       │
                     │  ├─ routes /sessions/{id}/messages to right pod  │
                     │  └─ session → pod mapping stored in Redis        │
                     │                                                  │
              ┌──────┴──────┐                                           │
              │             │                                           │
          Agent Pod    Agent Pod ──► Egress Proxy ──► api.anthropic.com │
          (session A)  (session B)      ▲                               │
              │             │            │                               │
              │     NetworkPolicy: pods can ONLY reach egress-proxy     │
              │                                                         │
            Redis (session → pod-IP mapping)                            │
                     │                                                  │
                     └──────────────────────────────────────────────────┘
```

The agent image is the **same one** Tier 1 builds from
[`hosting/Dockerfile`](../Dockerfile). Same image, different machinery: instead
of a single container or a Modal sandbox, the gateway gives each session its
own pod and the cluster enforces what that pod can reach.

> **Before you self-host:** if you just want a hosted agent without running
> infrastructure, use Anthropic's managed option — see the
> [Hosting overview](../README.md). This guide is for teams that need the
> agent on their own Kubernetes cluster (regulated environments, existing
> platform, custom networking).


## Why each piece exists

**Gateway** — Each user session gets its own agent pod. Something has to create
those pods on demand, route traffic to the right one, and clean them up when
sessions go idle. That's the gateway. It talks to the Kubernetes API to manage
pod lifecycles and uses Redis to remember which session maps to which pod IP.

**Egress proxy + NetworkPolicy** — Agents run arbitrary code. This pair ensures
agent pods can reach `api.anthropic.com` and *nothing else*. The NetworkPolicy
blocks all outbound traffic except to the egress proxy (port 443) and DNS
(port 53). The egress proxy terminates TLS from the agent, then re-encrypts the
request to Anthropic's API. Any attempt to reach the internet, other services,
or other namespaces is dropped at the network level.

**Redis** — The gateway needs to remember which pod is handling which session.
When a request arrives, it looks up the session ID in Redis to find the pod IP
and routes traffic there. Redis persists to disk so mappings survive gateway
restarts.

**Standby pool** — Pods take 10–30 seconds to start (image pull + container
boot). The gateway pre-warms a configurable number of standby pods so new
sessions can claim one instantly instead of waiting. After a pod is claimed,
the pool replenishes in the background.

## Prerequisites

| Tool | What it's for |
|------|---------------|
| [kind](https://kind.sigs.k8s.io/) | Local Kubernetes cluster in Docker |
| [kubectl](https://kubernetes.io/docs/tasks/tools/) | Applying manifests, inspecting the cluster |
| [docker](https://docs.docker.com/get-docker/) | Building container images |
| `openssl` | Generating the egress proxy's TLS certificate |
| `ANTHROPIC_API_KEY` | Set as env var |

## Quickstart (local, with kind)

```bash
cd hosting/kubernetes
export ANTHROPIC_API_KEY=sk-ant-...
./kind-quickstart.sh
```

This builds the three images, loads them into a local `kind` cluster, applies
every manifest, and port-forwards the gateway to `localhost:8080`. It also
generates bearer tokens for two demo tenants (`alice` and `bob`) and prints
them at the end — export the one you want to use:

```bash
export ALICE_TOKEN=...   # printed by kind-quickstart.sh
export BOB_TOKEN=...
```

## Talk to it

Same path and shape as Tier 1/2 — the base URL changes, and the gateway now
requires a bearer token that identifies the calling tenant:

```bash
curl -N -X POST http://localhost:8080/sessions/demo/messages \
  -H "Authorization: Bearer $ALICE_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"prompt": "What tools do you have?"}'
```

The first request on a new `session_id` claims a standby pod (or spawns one if
the pool is empty). Subsequent requests with the same `session_id` route to the
same pod, so the agent sees a continuous conversation.

The session now belongs to `alice` — the gateway records the creating tenant in
Redis and checks it on every subsequent request. The same call with
`$BOB_TOKEN` returns `403 {"detail":"session belongs to another tenant"}`, and
no token at all returns `401`. The tenant map is a static
`token:tenant,token:tenant` string in the `gateway-tenants` secret; swap the
`authenticate()` stub in [`gateway/main.py`](./gateway/main.py) for your IdP to
derive the tenant from a real credential instead.

Watch the machinery work:

```bash
kubectl -n claude-agent get pods -w
# you'll see agent-standby-* pods appear, then one flip to active when you curl
```

To end a session, go through the gateway so the Redis mapping is cleaned up
(owner-only, like every other session operation):

```bash
curl -X DELETE http://localhost:8080/sessions/demo \
  -H "Authorization: Bearer $ALICE_TOKEN"
```

(`kubectl delete pod` works too, but leaves a stale `session → pod-IP` entry
in Redis until the next request on that session 502s.)

## Verify the egress lockdown

The agent runs code the model decides to run. The egress proxy + NetworkPolicy
mean a prompt-injected agent still can't reach arbitrary hosts. Prove it:

> `kind-quickstart.sh` installs Calico because kind's default CNI (kindnet)
> doesn't enforce NetworkPolicy. On GKE/EKS/AKS or any Calico/Cilium cluster,
> enforcement is on by default and this section works unchanged.

```bash
AGENT_POD=$(kubectl -n claude-agent get pods -l role=agent \
  -o jsonpath='{.items[0].metadata.name}')

# This should FAIL — Calico drops the route to anything except egress-proxy.
# (The agent image is slim and has no curl, so we use Python's socket.)
kubectl -n claude-agent exec "$AGENT_POD" -- python3 -c \
  "import socket; socket.setdefaulttimeout(5); socket.create_connection(('example.com',443)); print('REACHED — policy NOT enforcing')"
```

Expected: `OSError: [Errno 101] Network is unreachable` (or a timeout) and a
non-zero exit. The positive control — that the egress-proxy path *is* open —
was already proven by the curl above returning model output.

## Standby pool

`STANDBY_POOL_SIZE` (in the `agent-config` ConfigMap) controls how many warm
pods the gateway keeps ready. Check current state (any valid tenant token):

```bash
curl http://localhost:8080/api/pool -H "Authorization: Bearer $ALICE_TOKEN"
```

## Persistence

`server.py` persists transcripts (and its caller-ID → SDK-ID map) to
`CLAUDE_CONFIG_DIR=/data`. In this tier that's the pod's ephemeral filesystem,
so:

- **While the pod is alive** (within the idle-timeout window), follow-up
  messages resume the conversation exactly as in Tiers 1 and 2.
- **After the pod is reaped**, `/data` is gone. The next message on that
  `session_id` gets a fresh pod with no history.

For a cookbook demo this is fine — sessions outlive the curl, not the cluster.
For production you need durable storage that survives pod recycle. Two options:

1. **Mount a PersistentVolumeClaim** at `/data` instead of the pod's local
   disk, and have the gateway reattach the same PVC when a session returns.
   Works with `server.py` as-is, but couples each session to a volume in one
   zone.
2. **Mirror `/data` to external storage** with the SDK's
   [`SessionStore`](https://code.claude.com/docs/en/agent-sdk/session-storage):
   the local-disk write still happens first; the store is a mirror, and
   `mirror_error` is non-fatal. This is the approach the notebook's
   *Making it production-ready* section describes — it needs a small hook in
   `server.py` that the cookbook hasn't grown yet.

## Deploying to your own cluster

`kind` proves the topology; the manifests are cloud-agnostic. To run on EKS,
AKS, GKE, OpenShift, or bare metal, swap the image registry and the front door:

```bash
REG=your.registry.example.com/claude-agent     # ECR, ACR, GHCR, Artifact Registry, ...

# 1. Build and push the three images
docker build -t $REG/agent:latest -f ../Dockerfile ..
docker build -t $REG/gateway:latest ./gateway
docker build -t $REG/egress-proxy:latest ./egress-proxy
docker push $REG/agent:latest $REG/gateway:latest $REG/egress-proxy:latest

# 2. TLS certs for the egress proxy
./generate-certs.sh

# 3. Namespace + secrets + config
kubectl apply -f manifests/namespace.yaml
kubectl -n claude-agent create secret generic anthropic-api-key \
    --from-literal=ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY"
kubectl -n claude-agent create secret generic gateway-tenants \
    --from-literal=GATEWAY_TENANTS="$(openssl rand -hex 16):tenant-a,$(openssl rand -hex 16):tenant-b"
kubectl -n claude-agent create secret generic egress-proxy-tls \
    --from-file=ca.crt=certs/ca.crt \
    --from-file=proxy.crt=certs/proxy.crt \
    --from-file=proxy.key=certs/proxy.key
kubectl -n claude-agent create configmap agent-config \
    --from-literal=AGENT_IMAGE=$REG/agent:latest \
    --from-literal=STANDBY_POOL_SIZE=2

# 4. Apply manifests with your registry substituted
for f in manifests/*.yaml; do
  sed "s|REGISTRY_URL|$REG|g" "$f" | kubectl apply -f -
done
```

> If you later change `$REG`, recreate the `agent-config` ConfigMap as well —
> the gateway reads `AGENT_IMAGE` from it when spawning agent pods, so re-running
> the `sed` over the manifests alone won't repoint them.

Then expose the `gateway` Service through whatever your cluster uses for
ingress — a cloud LoadBalancer, an Ingress controller, or a service mesh
gateway. Three things vary by environment:

- **Registry auth** — your nodes need pull credentials for `$REG`
  (`imagePullSecrets`, IRSA/Workload Identity, or a public registry).
- **NetworkPolicy enforcement** — the egress lockdown only works if your CNI
  enforces `NetworkPolicy` (Cilium, Calico, GKE Dataplane V2, EKS with the
  VPC CNI policy add-on). On a CNI that ignores it, agent pods can reach the
  internet.
- **TLS + auth in front of the gateway** — the static `GATEWAY_TENANTS` token
  map is a stand-in for real credentials. Put your IdP / API gateway in front
  before exposing this publicly.

## What this doesn't give you

- A real identity provider. The gateway *does* enforce per-tenant session
  ownership — each bearer token in `GATEWAY_TENANTS` maps to a tenant, the
  creating tenant owns the session, and other tenants get a 403 — but the
  tokens themselves are a static map with no issuance, rotation, revocation,
  or per-tenant RBAC. Swap `authenticate()` for your IdP; the ownership
  checks don't change.
- Durable session storage (see [Persistence](#persistence))
- Gateway autoscaling or multi-region routing
- DNS-level egress control — port 53 stays open to any resolver so node-local
  DNS caches keep working, which leaves DNS tunneling as a residual
  exfiltration channel. The note in
  [`manifests/network-policy.yaml`](./manifests/network-policy.yaml) shows how
  to tighten it if your cluster talks to kube-dns/CoreDNS directly.
- Hardened supporting services — the gateway, Redis, and nginx run as their
  stock images' default (root) users. The hardening budget went to the agent
  pods, which are the ones running model-driven code; lock down the rest to
  your org's baseline before production.
- Observability beyond what
  [`OTEL_EXPORTER_OTLP_ENDPOINT`](https://code.claude.com/docs/en/agent-sdk/observability)
  gives you for free

## Teardown

```bash
./teardown.sh        # kind delete cluster + remove certs/
```

## Layout

```
kubernetes/
├── README.md
├── kind-quickstart.sh         # local end-to-end on kind
├── teardown.sh
├── generate-certs.sh          # self-signed CA + proxy cert for egress-proxy
├── gateway/
│   ├── main.py                # FastAPI: route + reap
│   ├── k8s.py                 # pod lifecycle + standby pool
│   ├── proxy.py               # SSE relay
│   ├── requirements.txt
│   └── Dockerfile
├── egress-proxy/
│   ├── nginx.conf
│   └── Dockerfile
└── manifests/
    ├── namespace.yaml
    ├── redis.yaml
    ├── egress-proxy.yaml
    ├── gateway.yaml           # SA + RBAC + Deployment + Service
    └── network-policy.yaml
```
