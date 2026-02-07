#!/usr/bin/env bash
# installer.sh - installs systemd unit for FlowAgent
set -euo pipefail

SERVICE_NAME=flowagent.service
SERVICE_PATH=/etc/systemd/system/$SERVICE_NAME
FLOW_DIR=${FLOW_DIR:-/srv/flowagent}

if [ "$(id -u)" -ne 0 ]; then
  echo "Please run as root to install the service."
  exit 1
fi

echo "[STEP] Ensuring flow directory exists..."
for d in seed memory runtime persona reflex logs; do
  mkdir -p "$FLOW_DIR/$d"
  chown root:root "$FLOW_DIR/$d"
done

echo "[STEP] Copying service unit to $SERVICE_PATH"
cat > "$SERVICE_PATH" <<'UNIT'
[Unit]
Description=FlowAgent Wakeup Core Service
After=docker.service network.target
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
# Run as a non-root user with docker group membership; change 'flowagent' if needed.
User=root
# If you don't want root, create 'flowagent' user and set User=flowagent
Environment=FLOW_DIR=/srv/flowagent
# Keep restart behavior conservative to avoid crash loop
Restart=on-failure
RestartSec=5
TimeoutStartSec=120
ExecStart=/usr/bin/docker compose -f /srv/flowagent/docker-compose.yml up -d
ExecStop=/usr/bin/docker compose -f /srv/flowagent/docker-compose.yml down
# Optional: collect logs on stop
ExecStopPost=/bin/sh -c 'docker logs --tail 200 flowagent_core > /srv/flowagent/logs/flowagent_last_stop.log || true'

[Install]
WantedBy=multi-user.target

UNIT

echo "[STEP] Reloading systemd daemon and enabling service"
systemctl daemon-reload
systemctl enable --now $SERVICE_NAME

echo "[OK] Service $SERVICE_NAME installed and started (if docker compose is configured)."
echo "To view status: systemctl status $SERVICE_NAME"
