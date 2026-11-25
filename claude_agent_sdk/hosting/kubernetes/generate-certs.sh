#!/bin/bash
# =============================================================================
# generate-certs.sh — Create a self-signed CA and proxy certificate
# =============================================================================
#
# WHAT IS A SELF-SIGNED CA?
#   A Certificate Authority (CA) is an entity that signs TLS certificates.
#   Normally, browsers and apps trust well-known CAs (like Let's Encrypt).
#   A "self-signed" CA is one you create yourself — it's not trusted by
#   default, but you can configure your applications to trust it explicitly.
#
# WHY WE NEED THIS:
#   The egress proxy sits between agent pods and api.anthropic.com. Agent
#   pods connect to the proxy over HTTPS, so the proxy needs a TLS
#   certificate. Since the proxy is an internal service (not a public
#   website), we can't get a certificate from a public CA — we create our
#   own CA and sign the proxy's certificate with it.
#
#   Agent pods are then configured to trust our CA certificate via the
#   NODE_EXTRA_CA_CERTS environment variable. This tells Node.js (and
#   tools like Claude Code that run on Node.js) to accept TLS certificates
#   signed by our CA.
#
# WHAT THIS SCRIPT CREATES:
#   certs/ca.key     — CA private key (keep secret)
#   certs/ca.crt     — CA certificate (shared with agent pods so they
#                       trust the proxy)
#   certs/proxy.key  — Proxy private key (mounted into the proxy pod)
#   certs/proxy.crt  — Proxy certificate signed by our CA (mounted into
#                       the proxy pod)
# =============================================================================

set -euo pipefail

CERTS_DIR="$(dirname "$0")/certs"
mkdir -p "$CERTS_DIR"
cd "$CERTS_DIR"

echo "Generating CA certificate..."
openssl genrsa -out ca.key 2048
openssl req -x509 -new -nodes -key ca.key -sha256 -days 365 -out ca.crt \
    -subj "/CN=Demo CA/O=Agent SDK Demo"

echo "Generating proxy certificate..."
openssl genrsa -out proxy.key 2048

# Create CSR with SAN for egress-proxy hostname
cat > proxy.cnf << EOF
[req]
default_bits = 2048
prompt = no
default_md = sha256
distinguished_name = dn
req_extensions = req_ext

[dn]
CN = egress-proxy

[req_ext]
subjectAltName = @alt_names

[alt_names]
DNS.1 = egress-proxy
DNS.2 = egress-proxy.claude-agent.svc.cluster.local
DNS.3 = localhost
EOF

openssl req -new -key proxy.key -out proxy.csr -config proxy.cnf

# Sign with CA
openssl x509 -req -in proxy.csr -CA ca.crt -CAkey ca.key -CAcreateserial \
    -out proxy.crt -days 365 -sha256 -extensions req_ext -extfile proxy.cnf

# Cleanup CSR and config
rm -f proxy.csr proxy.cnf ca.srl

echo ""
echo "Certificates generated:"
ls -la .
echo ""
echo "CA certificate:    ca.crt"
echo "Proxy certificate: proxy.crt"
echo "Proxy key:         proxy.key"
