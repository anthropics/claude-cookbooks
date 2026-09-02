#!/usr/bin/env bash
# Provision the minimal AWS resources for the AgentCore variant of the CMA
# self-hosted sandbox demo:
#   - ECR repository
#   - arm64 Docker image build + push
# Writes envvars.config consumed by deploy.py.
#
# This is intentionally smaller than the agentcore-samples cookbook scripts:
# no VPC, no NAT, no S3 Files. Each session's /workspace is ephemeral inside
# its microVM, mirroring the docker/ variant. Add S3 Files later if you want
# persistence across sessions (see 01-claude-code-with-s3-files for pattern).
set -euo pipefail
cd "$(dirname "$0")"

REGION="${1:-us-west-2}"
ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
AGENT_NAME="cma_self_hosted_$(date +%s | tail -c 6)"
ECR_REPO="cma-self-hosted-sandbox"
IMAGE_TAG="${AGENT_NAME}"
ECR_URI="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${ECR_REPO}:${IMAGE_TAG}"

echo "Region:   ${REGION}"
echo "Account:  ${ACCOUNT_ID}"
echo "Agent:    ${AGENT_NAME}"
echo "Image:    ${ECR_URI}"

# ── Create ECR repo (idempotent) ─────────────────────────────────────────────

if aws ecr describe-repositories --repository-names "${ECR_REPO}" --region "${REGION}" >/dev/null 2>&1; then
  echo "ECR repo exists: ${ECR_REPO}"
else
  echo "Creating ECR repo: ${ECR_REPO}"
  aws ecr create-repository --repository-name "${ECR_REPO}" --region "${REGION}" >/dev/null
fi

# ── Build + push arm64 image ─────────────────────────────────────────────────

echo "Logging into ECR..."
aws ecr get-login-password --region "${REGION}" \
  | docker login --username AWS --password-stdin "${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"

echo "Building arm64 image (AgentCore Runtime is Graviton-only)..."
# Use buildx if available; otherwise plain docker/finch build (which still
# accepts --platform for cross-arch builds on darwin).
if docker buildx version >/dev/null 2>&1; then
  docker buildx build --platform linux/arm64 -t "${ECR_URI}" -f Dockerfile --push .
else
  docker build --platform linux/arm64 -t "${ECR_URI}" -f Dockerfile .
  docker push "${ECR_URI}"
fi

echo "Image pushed: ${ECR_URI}"

# ── Save config ──────────────────────────────────────────────────────────────

cat > envvars.config <<CFG
AGENTCORE_REGION=${REGION}
AGENTCORE_AGENT_NAME=${AGENT_NAME}
AGENTCORE_ECR_REPO=${ECR_REPO}
AGENTCORE_ECR_URI=${ECR_URI}
CFG

echo
echo "Wrote envvars.config:"
cat envvars.config
echo
echo "Next: python3 deploy.py"
