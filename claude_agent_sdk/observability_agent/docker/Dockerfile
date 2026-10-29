FROM python:3.11

WORKDIR /app

# Install system dependencies including Docker CLI
RUN apt-get update && apt-get install -y \
    curl \
    git \
    ca-certificates \
    gnupg \
    && install -m 0755 -d /etc/apt/keyrings \
    && curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg \
    && echo "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
    "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" > /etc/apt/sources.list.d/docker.list \
    && apt-get update \
    && apt-get install -y docker-ce-cli \
    && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# The claude-agent-sdk wheel bundles its own CLI binary and prefers it; this
# global install (Node 22+) is a fallback and provides `claude --version` below.
RUN npm install -g @anthropic-ai/claude-code

COPY observability_agent ./observability_agent

RUN pip install --no-cache-dir \
    "claude-agent-sdk>=0.2.168" \
    fastapi \
    python-dotenv \
    uvicorn[standard] \
    mcp-server-git

RUN claude --version

EXPOSE 8000

CMD ["python", "-m", "observability_agent.web.app"]