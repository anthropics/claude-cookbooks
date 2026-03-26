# SceneView MCP Cookbook

This cookbook demonstrates how to use the [SceneView MCP server](https://www.npmjs.com/package/sceneview-mcp) to give Claude expert knowledge of the SceneView 3D/AR SDK.

## Notebook

- **[sceneview_3d_mcp.ipynb](./sceneview_3d_mcp.ipynb)** — Building 3D & AR experiences with the SceneView MCP server

## What you'll learn

- Defining MCP tool schemas and using them with the Anthropic Messages API
- The **"linter in the loop"** pattern: Claude validates its own generated code via tools before presenting it
- Building an agentic tool-use loop (fetch reference -> generate -> validate -> fix)
- How to package any SDK's expertise into MCP tools for Claude

## Quick start (no Python needed)

To use the MCP server directly with Claude Desktop:

```json
{
  "mcpServers": {
    "sceneview": {
      "command": "npx",
      "args": ["-y", "sceneview-mcp"]
    }
  }
}
```

Or with Claude Code:

```bash
claude mcp add sceneview -- npx -y sceneview-mcp
```

## Requirements

- Python 3.11+ (for the notebook)
- `anthropic` Python SDK
- Node.js >= 18 (optional, for the MCP server)
