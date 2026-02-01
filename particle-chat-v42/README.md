# Particle Chat v42

A modern, lightweight chat application powered by Claude AI, deployed on Cloudflare Workers for global edge performance.

## Features

- 🚀 **Edge-native**: Runs on Cloudflare's global edge network for low latency
- 🤖 **Claude AI**: Powered by Anthropic's Claude for intelligent conversations
- 🎨 **Modern UI**: Clean, responsive chat interface
- 🔒 **Secure**: API keys stored as Cloudflare secrets, never in code
- ⚡ **Fast**: Serverless architecture with instant cold starts

## Prerequisites

Before deploying, ensure you have:

1. **Cloudflare Account**: Sign up at [cloudflare.com](https://cloudflare.com)
2. **Anthropic API Key**: Get yours at [console.anthropic.com](https://console.anthropic.com)
3. **Node.js**: Version 18 or higher
4. **Wrangler CLI**: Cloudflare's deployment tool

## Quick Start

### 1. Install Dependencies

```bash
# Install packages
npm install
```

### 2. Configure Wrangler

Login to your Cloudflare account:

```bash
wrangler login
```

This will open a browser window to authenticate.

### 3. Set API Key Secret

**IMPORTANT**: Never commit API keys to version control. Use Wrangler secrets:

```bash
wrangler secret put ANTHROPIC_API_KEY
```

When prompted, paste your Anthropic API key (starts with `sk-ant-api03-...`).

### 4. Deploy

Deploy to Cloudflare Workers:

```bash
wrangler deploy
```

Or use npm script:

```bash
npm run deploy
```

Your application will be deployed and you'll receive a URL like:
```
https://particle-chat-v42.<your-subdomain>.workers.dev
```

## Local Development

To run the application locally:

```bash
# Start development server
npm run dev
```

Or:

```bash
wrangler dev
```

The app will be available at `http://localhost:8787`

**Note**: For local development, you'll need to set the API key secret:
```bash
wrangler secret put ANTHROPIC_API_KEY --env development
```

## API Endpoints

### GET `/`
Returns the chat UI (HTML page)

### POST `/api/chat`
Send messages to Claude

**Request body**:
```json
{
  "messages": [
    { "role": "user", "content": "Hello!" }
  ],
  "model": "claude-sonnet-4-20250514",  // optional
  "max_tokens": 1024  // optional
}
```

**Response**:
```json
{
  "response": "Hello! How can I help you today?",
  "usage": {
    "input_tokens": 10,
    "output_tokens": 20
  }
}
```

### GET `/health`
Health check endpoint

**Response**:
```json
{
  "status": "ok",
  "version": "v42",
  "timestamp": "2026-02-01T00:00:00.000Z"
}
```

## Environment Configuration

The application supports multiple environments configured in `wrangler.toml`:

- **development**: For local testing
- **production**: For production deployment

## Project Structure

```
particle-chat-v42/
├── src/
│   └── index.ts          # Main worker code
├── package.json          # Dependencies
├── tsconfig.json         # TypeScript configuration
├── wrangler.toml         # Cloudflare Workers configuration
└── README.md            # This file
```

## Security Best Practices

1. **Never commit secrets**: Always use `wrangler secret put` for sensitive data
2. **Use environment variables**: Store configuration in `wrangler.toml` [vars] section
3. **CORS configuration**: Adjust CORS headers in production as needed
4. **Rate limiting**: Consider adding rate limiting for production use

## Customization

### Change Claude Model

Edit the model in `src/index.ts`:

```typescript
const response = await anthropic.messages.create({
  model: 'claude-opus-4-20250514', // or claude-haiku-4-20250514
  // ...
});
```

Available models:
- `claude-sonnet-4-20250514` (default, balanced)
- `claude-opus-4-20250514` (most capable)
- `claude-haiku-4-20250514` (fastest, most affordable)

### Adjust Token Limits

Modify `max_tokens` in the API call or request:

```typescript
max_tokens: chatRequest.max_tokens || 2048, // Increase for longer responses
```

### Customize UI

The HTML/CSS/JavaScript is embedded in the `getHTML()` function in `src/index.ts`. Modify it to match your branding.

## Troubleshooting

### "Missing entry-point" Error

Ensure `wrangler.toml` has:
```toml
main = "src/index.ts"
```

### "API Key not found" Error

Set the secret:
```bash
wrangler secret put ANTHROPIC_API_KEY
```

### TypeScript Errors

Install dependencies:
```bash
npm install
```

### Deployment Fails

Check Wrangler version:
```bash
wrangler --version
```

Update if needed:
```bash
npm install -g wrangler@latest
```

## Cost Estimation

**Cloudflare Workers**:
- Free tier: 100,000 requests/day
- Paid tier: $5/month for 10 million requests

**Anthropic Claude API**:
- Pricing varies by model and tokens used
- See [anthropic.com/pricing](https://www.anthropic.com/pricing)

## Support

- **Anthropic Documentation**: [docs.anthropic.com](https://docs.anthropic.com)
- **Cloudflare Workers Docs**: [developers.cloudflare.com/workers](https://developers.cloudflare.com/workers)
- **Wrangler CLI Docs**: [developers.cloudflare.com/workers/wrangler](https://developers.cloudflare.com/workers/wrangler)

## License

MIT License - feel free to modify and distribute as needed.

## Contributing

Contributions welcome! This is part of the Anthropic Cookbooks collection.

---

**Built with ❤️ using Claude AI and Cloudflare Workers**
