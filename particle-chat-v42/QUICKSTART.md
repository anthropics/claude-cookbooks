# Quick Start - Matching Original Instructions

This document maps the original deployment commands to the new application structure.

## Original Commands (from problem statement)

```bash
unzip particle-chat-v42-deploy.zip
cd particle-chat-v42
wrangler login
wrangler secret put ANTHROPIC_API_KEY
# Paste your API key when prompted
wrangler deploy
```

## How This Works With Our Implementation

### Step 1: Get the Application

**If you have a zip file:**
```bash
unzip particle-chat-v42-deploy.zip
cd particle-chat-v42
```

**If you're using the repository:**
```bash
cd particle-chat-v42
```

### Step 2: Install Dependencies (one-time setup)

```bash
npm install
```

This installs:
- Anthropic SDK
- Wrangler CLI
- TypeScript compiler
- Cloudflare Workers types

### Step 3: Login to Cloudflare

```bash
wrangler login
```

Opens your browser to authenticate with Cloudflare.

### Step 4: Set Your API Key Securely

```bash
wrangler secret put ANTHROPIC_API_KEY
```

When prompted, paste your Anthropic API key (starts with `sk-ant-api03-...`).

**IMPORTANT**: The key is encrypted and stored securely by Cloudflare. It will NEVER appear in:
- Your code
- Configuration files
- Git commits
- Public URLs

### Step 5: Deploy

```bash
wrangler deploy
```

Or use the npm script:

```bash
npm run deploy
```

Your chat app will be live at:
```
https://particle-chat-v42.<your-subdomain>.workers.dev
```

## Creating a Deployment Zip

To create a `particle-chat-v42-deploy.zip` for easy distribution:

```bash
cd /path/to/claude-cookbooks
zip -r particle-chat-v42-deploy.zip particle-chat-v42/ \
  -x "particle-chat-v42/node_modules/*" \
  -x "particle-chat-v42/.wrangler/*" \
  -x "particle-chat-v42/dist/*"
```

This creates a zip file containing:
- ✅ Source code (`src/index.ts`)
- ✅ Configuration (`wrangler.toml`, `package.json`, `tsconfig.json`)
- ✅ Documentation (`README.md`, `DEPLOYMENT.md`)
- ✅ Examples (`.env.example`)
- ✅ Git ignore rules (`.gitignore`)
- ❌ No dependencies (user runs `npm install`)
- ❌ No build artifacts
- ❌ No API keys

## What Happens During Deployment

1. **Build**: Wrangler compiles TypeScript to JavaScript
2. **Bundle**: Creates a single worker script
3. **Upload**: Deploys to Cloudflare's edge network
4. **Activate**: Makes it live at your Workers URL
5. **Done**: Usually takes 5-10 seconds total

## Verifying Deployment

After deployment, test your endpoints:

```bash
# Health check
curl https://your-worker-url.workers.dev/health

# Chat API (replace YOUR_URL)
curl -X POST https://your-worker-url.workers.dev/api/chat \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Hello!"}]}'

# Web UI
open https://your-worker-url.workers.dev
```

## Troubleshooting

### "Missing entry-point" error
✅ **Fixed**: Our `wrangler.toml` includes `main = "src/index.ts"`

### "API key not set" error
Run: `wrangler secret put ANTHROPIC_API_KEY`

### "Module not found" error
Run: `npm install`

### Dependencies won't install
Check Node.js version: `node --version` (need 18+)

## Security Notes

This implementation follows security best practices:

1. ✅ API keys stored as encrypted Cloudflare secrets
2. ✅ `.gitignore` prevents committing sensitive files
3. ✅ `.env.example` shows format without real keys
4. ✅ Documentation emphasizes security
5. ✅ CORS configured (can be restricted in production)

## Next Steps

After successful deployment:

1. **Customize**: Edit `src/index.ts` to modify the chat UI or behavior
2. **Add features**: Implement conversation history, user sessions, etc.
3. **Monitor**: Use Cloudflare dashboard to track usage
4. **Scale**: Cloudflare Workers automatically scales globally
5. **Optimize**: Add caching, rate limiting, or analytics

## Support

- See `README.md` for detailed documentation
- See `DEPLOYMENT.md` for comprehensive deployment guide
- Visit [docs.anthropic.com](https://docs.anthropic.com) for Claude API docs
- Visit [developers.cloudflare.com/workers](https://developers.cloudflare.com/workers) for Workers docs
