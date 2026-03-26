# SceneView MCP Cookbook

This cookbook demonstrates how to use the [SceneView MCP server](https://www.npmjs.com/package/sceneview-mcp) to give Claude expert knowledge of the SceneView 3D/AR SDK.

## Notebook

- **[sceneview_3d_mcp.ipynb](./sceneview_3d_mcp.ipynb)** — Building 3D & AR experiences with the SceneView MCP server

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

## Requirements

- Python 3.11+ (for the notebook)
- `anthropic` Python SDK
- Node.js >= 18 (for the MCP server)
