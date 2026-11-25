#!/bin/bash
# =============================================================================
# kind-quickstart.sh — Run the full Tier 3 topology on a local kind cluster
# =============================================================================
#
# kind ("Kubernetes in Docker") spins up a real Kubernetes API server inside a
# Docker container on your laptop.  No cloud account needed.  The manifests
# applied here are the same ones you'd apply to a production cluster — only
# the image registry differs.
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOSTING_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"      # → claude_agent_sdk/hosting/ (Dockerfile, server.py)
SDK_ROOT="$(cd "$HOSTING_ROOT/.." && pwd)"        # → claude_agent_sdk/ (build context — image needs research_agent/, utils/)
cd "$SCRIPT_DIR"

CLUSTER=claude-agent
REG=local                                     # tag prefix for kind-loaded images

info() { printf '\033[0;32m[INFO]\033[0m %s\n' "$1"; }
error() { printf '\033[0;31m[ERROR]\033[0m %s\n' "$1"; exit 1; }

for cmd in kind kubectl docker openssl jq; do
    command -v "$cmd" >/dev/null || error "$cmd is required but not installed"
done
: "${ANTHROPIC_API_KEY:?Must set ANTHROPIC_API_KEY (get one at https://console.anthropic.com/settings/keys)}"
# Preflight: verify the key actually works before we build a cluster around it.
# A stale or revoked key in env produces a confusing "Invalid API key" error
# only after the full stack is up and the first curl is sent.
info "Verifying ANTHROPIC_API_KEY against api.anthropic.com..."
_preflight=$(curl -sS https://api.anthropic.com/v1/models \
    -H "x-api-key: $ANTHROPIC_API_KEY" \
    -H "anthropic-version: 2023-06-01") || error "Could not reach api.anthropic.com"
if echo "$_preflight" | jq -e 'has("error")' >/dev/null; then
    error "ANTHROPIC_API_KEY rejected by API: $_preflight
       Mint a fresh key at https://console.anthropic.com/settings/keys and re-export."
fi

# 1. Cluster ────────────────────────────────────────────────────────────────
# kind's default CNI (kindnet) does NOT enforce NetworkPolicy.  We disable it
# and install Calico so the egress-lockdown demo below actually blocks traffic
# the way it would on a real cluster.
if ! kind get clusters | grep -qx "$CLUSTER"; then
    info "Creating kind cluster '$CLUSTER' (default CNI disabled, Calico will provide NetworkPolicy)..."
    cat <<EOF | kind create cluster --name "$CLUSTER" --config=-
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
networking:
  disableDefaultCNI: true
  podSubnet: "192.168.0.0/16"
EOF
    info "Installing Calico CNI..."
    kubectl apply -f https://raw.githubusercontent.com/projectcalico/calico/v3.28.5/manifests/calico.yaml
    info "Waiting for Calico to be ready..."
    # Wait on the workload objects (they exist immediately after apply); waiting
    # on pods by label can race — the DaemonSet may not have scheduled them yet.
    kubectl -n kube-system rollout status daemonset/calico-node --timeout=180s
    kubectl -n kube-system rollout status deployment/calico-kube-controllers --timeout=180s
    # Now the node has a CNI; wait for it to flip to Ready before building images.
    kubectl wait --for=condition=ready node --all --timeout=120s
else
    info "kind cluster '$CLUSTER' already exists — reusing"
    REUSING_CLUSTER=1
fi

# 2. Images ─────────────────────────────────────────────────────────────────
# The agent image is the same one Tier 1 (docker/) builds — one Dockerfile,
# different machinery around it.
info "Building agent image..."
docker build -t "${REG}/agent:latest" -f "$HOSTING_ROOT/Dockerfile" "$SDK_ROOT"

info "Building gateway image..."
docker build -t "${REG}/gateway:latest" "$SCRIPT_DIR/gateway"

info "Building egress-proxy image..."
docker build -t "${REG}/egress-proxy:latest" "$SCRIPT_DIR/egress-proxy"

info "Loading images into kind..."
kind load docker-image "${REG}/agent:latest" "${REG}/gateway:latest" \
    "${REG}/egress-proxy:latest" --name "$CLUSTER"

# 3. Certificates ───────────────────────────────────────────────────────────
info "Generating TLS certificates for the egress proxy..."
bash generate-certs.sh

# 4. Namespace, secrets, config ─────────────────────────────────────────────
info "Applying namespace..."
kubectl apply -f manifests/namespace.yaml

info "Creating secrets..."
kubectl -n claude-agent create secret generic anthropic-api-key \
    --from-literal=ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" \
    --dry-run=client -o yaml | kubectl apply -f -

# Two demo tenants so you can watch the gateway enforce session ownership:
# alice can read/continue/delete her sessions, bob gets a 403 on them.
# The gateway reads this secret at pod start, so on a re-run we restart the
# deployment below once the manifests are applied.
ALICE_TOKEN=$(openssl rand -hex 16)
BOB_TOKEN=$(openssl rand -hex 16)
kubectl -n claude-agent create secret generic gateway-tenants \
    --from-literal=GATEWAY_TENANTS="${ALICE_TOKEN}:alice,${BOB_TOKEN}:bob" \
    --dry-run=client -o yaml | kubectl apply -f -

kubectl -n claude-agent create secret generic egress-proxy-tls \
    --from-file=ca.crt=certs/ca.crt \
    --from-file=proxy.crt=certs/proxy.crt \
    --from-file=proxy.key=certs/proxy.key \
    --dry-run=client -o yaml | kubectl apply -f -

info "Creating agent-config ConfigMap..."
kubectl -n claude-agent create configmap agent-config \
    --from-literal=AGENT_IMAGE="${REG}/agent:latest" \
    --from-literal=STANDBY_POOL_SIZE=2 \
    --dry-run=client -o yaml | kubectl apply -f -

# 5. Manifests ──────────────────────────────────────────────────────────────
info "Applying manifests..."
for f in manifests/*.yaml; do
    sed "s|REGISTRY_URL|${REG}|g" "$f" | kubectl apply -f -
done

# On a re-run the gateway pod predates the freshly regenerated GATEWAY_TENANTS
# secret — restart it so the new tokens take effect.
if [[ -n "${REUSING_CLUSTER:-}" ]]; then
    info "Restarting gateway to pick up regenerated tenant tokens..."
    kubectl -n claude-agent rollout restart deploy/gateway
    kubectl -n claude-agent rollout status deploy/gateway --timeout=300s
fi

# 6. Wait ───────────────────────────────────────────────────────────────────
info "Waiting for gateway to be ready (this can take a minute on first run)..."
kubectl -n claude-agent wait --for=condition=available deploy/redis --timeout=180s
kubectl -n claude-agent wait --for=condition=available deploy/egress-proxy --timeout=180s
kubectl -n claude-agent wait --for=condition=available deploy/gateway --timeout=300s

# 7. Done ───────────────────────────────────────────────────────────────────
info "Ready. Port-forwarding gateway to http://localhost:8080 ..."
kubectl -n claude-agent port-forward svc/gateway 8080:8080 &
PF_PID=$!
# Make sure the port-forward dies with the script (Ctrl-C or any error exit) —
# otherwise it lingers and the next run fails with "address already in use".
trap 'kill "$PF_PID" 2>/dev/null || true' EXIT INT TERM
sleep 2

cat <<EOF

  Two demo tenants are configured. Sessions belong to whichever tenant
  creates them:

    alice  $ALICE_TOKEN
    bob    $BOB_TOKEN

  Try it as alice:

    curl -N -X POST http://localhost:8080/sessions/demo/messages \\
      -H 'Authorization: Bearer $ALICE_TOKEN' \\
      -H 'Content-Type: application/json' \\
      -d '{"prompt": "Hello from Tier 3"}'

  Now hit alice's session with bob's token — the gateway returns 403:

    curl -X POST http://localhost:8080/sessions/demo/messages \\
      -H 'Authorization: Bearer $BOB_TOKEN' \\
      -H 'Content-Type: application/json' \\
      -d '{"prompt": "let me in"}'

  Watch pods come and go:

    kubectl -n claude-agent get pods -w

  Stop the port-forward with Ctrl-C, or run ./teardown.sh to delete the cluster.

EOF

wait $PF_PID
