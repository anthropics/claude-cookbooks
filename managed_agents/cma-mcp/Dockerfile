FROM oven/bun:1-slim

# Non-root user — limits blast radius if the process is compromised.
RUN adduser --system --no-create-home app

WORKDIR /app
COPY package.json bun.lockb ./
RUN bun install --frozen-lockfile --production
COPY src ./src

USER app
ENV PORT=3000
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=3s CMD curl -f http://localhost:3000/health || exit 1
CMD ["bun", "run", "src/server-http.ts"]
