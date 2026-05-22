#!/bin/bash
set -euo pipefail
kind delete cluster --name claude-agent
rm -rf "$(dirname "$0")/certs"
