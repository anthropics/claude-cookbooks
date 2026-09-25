FROM debian:12-slim

ARG ANT_VERSION=1.9.0
ARG TARGETOS=linux
ARG TARGETARCH=arm64

RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates curl python3 python3-pip git \
 && rm -rf /var/lib/apt/lists/*

ADD https://github.com/anthropics/anthropic-cli/releases/download/v${ANT_VERSION}/ant_${ANT_VERSION}_${TARGETOS}_${TARGETARCH}.tar.gz /tmp/ant.tgz
RUN tar -xzf /tmp/ant.tgz -C /usr/local/bin ant \
 && chmod +x /usr/local/bin/ant && rm /tmp/ant.tgz

RUN useradd -m -d /home/agent -u 1000 agent
WORKDIR /workspace
RUN chown -R agent:agent /workspace

COPY --chown=agent:agent requirements.txt /app/requirements.txt
RUN pip3 install --break-system-packages -r /app/requirements.txt

COPY --chown=agent:agent server.py /app/server.py

USER agent
ENV HOME=/home/agent
EXPOSE 8080
CMD ["python3", "/app/server.py"]
