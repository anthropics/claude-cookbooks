# Deployment Guide for Particle Chat v42

This guide walks you through deploying the Particle Chat v42 application to Cloudflare Workers.

## Prerequisites

- A Cloudflare account (free tier works)
- An Anthropic API key from [console.anthropic.com](https://console.anthropic.com)
- Node.js 18+ installed
- Terminal/command line access

## Step-by-Step Deployment

### Step 1: Extract the Application

If you received this as a zip file, extract it:

```bash
unzip particle-chat-v42-deploy.zip
cd particle-chat-v42
```

If you're working from the repository:

```bash
cd particle-chat-v42
```

### Step 2: Install Dependencies

```bash
npm install
```

This will install:
- `@anthropic-ai/sdk` - Anthropic's official SDK
- `@cloudflare/workers-types` - TypeScript types for Workers
- `typescript` - TypeScript compiler
- `wrangler` - Cloudflare's deployment CLI

### Step 3: Login to Cloudflare

Authenticate with your Cloudflare account:

```bash
wrangler login
```

This will:
1. Open your browser
2. Ask you to log in to Cloudflare
3. Authorize the Wrangler CLI
4. Save credentials for future use

### Step 4: Set Your Anthropic API Key

**CRITICAL SECURITY STEP**: Set your API key as a Cloudflare secret (not in code):

```bash
wrangler secret put ANTHROPIC_API_KEY
```

When prompted, paste your Anthropic API key. It should look like:
```
sk-ant-api03-...
```

**Important**: 
- The key is encrypted and stored securely by Cloudflare
- It will NOT appear in your code or configuration files
- It's only accessible to your Worker at runtime

### Step 5: Deploy to Cloudflare Workers

Deploy your application:

```bash
wrangler deploy
```

Or use the npm script:

```bash
npm run deploy
```

### Step 6: Access Your Application

After deployment completes, you'll see output like:

```
✨ Built successfully, built project size is 234 KiB.
✨ Successfully published your script to
   https://particle-chat-v42.your-subdomain.workers.dev
```

Visit that URL in your browser to start chatting with Claude!

## Deployment Environments

### Development Environment

For testing with a development environment:

```bash
wrangler deploy --env development
```

This uses the configuration from `[env.development]` in `wrangler.toml`.

### Production Environment

For production deployment:

```bash
wrangler deploy --env production
```

This uses the configuration from `[env.production]` in `wrangler.toml`.

## Quick Commands Reference

```bash
# Login to Cloudflare
wrangler login

# Set API key secret
wrangler secret put ANTHROPIC_API_KEY

# Deploy to default environment
wrangler deploy

# Deploy to specific environment
wrangler deploy --env production

# Start local development server
wrangler dev

# View deployment logs
wrangler tail

# List all secrets
wrangler secret list

# Delete a secret
wrangler secret delete ANTHROPIC_API_KEY
```

## Verification

After deployment, test your application:

### 1. Health Check

```bash
curl https://your-worker-url.workers.dev/health
```

Expected response:
```json
{
  "status": "ok",
  "version": "v42",
  "timestamp": "2026-02-01T..."
}
```

### 2. Chat API Test

```bash
curl -X POST https://your-worker-url.workers.dev/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Hello!"}
    ]
  }'
```

Expected response:
```json
{
  "response": "Hello! How can I help you today?",
  "usage": {
    "input_tokens": 10,
    "output_tokens": 20
  }
}
```

### 3. Web UI Test

Open your worker URL in a browser and try sending a message through the chat interface.

## Troubleshooting

### Error: "Missing entry-point to Worker script"

**Solution**: Ensure your `wrangler.toml` has:
```toml
main = "src/index.ts"
```

### Error: "API Key not set"

**Solution**: Run the secret command:
```bash
wrangler secret put ANTHROPIC_API_KEY
```

### Error: "Not authenticated"

**Solution**: Login again:
```bash
wrangler login
```

### Error: "Module not found"

**Solution**: Install dependencies:
```bash
npm install
```

### Deployment takes too long or fails

**Solution**: Check your internet connection and try again. Cloudflare's network is generally very fast.

## Updating Your Deployment

To update your application after making changes:

1. Edit your code in `src/index.ts`
2. Run `wrangler deploy` again
3. Your changes will be live within seconds!

## Rolling Back

If something goes wrong, you can rollback to a previous version:

```bash
wrangler rollback
```

This will show you a list of recent deployments and let you choose which to restore.

## Custom Domain (Optional)

To use your own domain instead of `*.workers.dev`:

1. Add your domain to Cloudflare
2. Add a route in `wrangler.toml`:

```toml
routes = [
  { pattern = "chat.yourdomain.com/*", zone_name = "yourdomain.com" }
]
```

3. Deploy again:

```bash
wrangler deploy
```

## Monitoring and Logs

View live logs from your Worker:

```bash
wrangler tail
```

This shows real-time request logs and console output.

## Cost Management

**Free Tier Limits**:
- 100,000 requests per day
- 10ms CPU time per request

**Paid Tier** ($5/month):
- 10 million requests
- 50ms CPU time per request

To monitor usage:
1. Go to [dash.cloudflare.com](https://dash.cloudflare.com)
2. Navigate to Workers & Pages
3. Click on your worker
4. View the Analytics tab

## Security Checklist

- [x] API key stored as secret (not in code)
- [x] `.env` files added to `.gitignore`
- [x] CORS headers configured
- [ ] Consider adding rate limiting for production
- [ ] Consider adding request validation
- [ ] Monitor usage to prevent abuse

## Next Steps

1. **Customize the UI**: Edit the HTML/CSS in `getHTML()` function
2. **Add features**: Implement conversation history, user accounts, etc.
3. **Optimize performance**: Use Cloudflare KV for caching
4. **Add analytics**: Track usage patterns
5. **Set up monitoring**: Use Cloudflare's analytics dashboard

## Support Resources

- **Wrangler Docs**: https://developers.cloudflare.com/workers/wrangler/
- **Workers Docs**: https://developers.cloudflare.com/workers/
- **Anthropic Docs**: https://docs.anthropic.com/
- **Anthropic Support**: support@anthropic.com

---

**Happy deploying! 🚀**
