# Pipelock <> Claude Cookbooks

[Pipelock](https://github.com/luckyPipewrench/pipelock) is an open-source firewall for AI agents. It runs as a network proxy that scans HTTP, WebSocket, and MCP traffic for prompt injection, secret exfiltration, SSRF, and tool poisoning. When configured with a flight recorder and signing key, every scanned exchange is recorded in a hash-chained, signed receipt that a third party can verify with the public key alone.

Here we provide a cookbook for using Pipelock with Claude to harden Model Context Protocol (MCP) integrations.

1. `securing-mcp-with-pipelock.ipynb` — Wrap an MCP server with `pipelock mcp proxy`, watch Pipelock block a prompt-injection payload returned in a tool response, and verify the signed action receipts.

[Documentation](https://pipelab.org)
[Repository](https://github.com/luckyPipewrench/pipelock)
[Apache 2.0 License](https://github.com/luckyPipewrench/pipelock/blob/main/LICENSE)
