#!/usr/bin/env bash
RUN_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )";

CMD="$RUN_DIR/ddns -c $RUN_DIR/config.json";

# Add newfuture_ddns.timer to /etc/systemd/system
echo "[Unit]
Description=NewFuture DDNS Timer
Wants=network-online.target
After=network-online.target

[Timer]
OnStartupSec=60
OnUnitActiveSec=300

[Install]
WantedBy=timers.target" > /etc/systemd/system/newfuture_ddns.timer;

# Add newfuture_ddns.service to /etc/systemd/system
echo "[Unit]
Description=NewFuture DDNS Service
Wants=network-online.target
After=network-online.target

[Service]
User=root
Type=oneshot
ExecStart=$CMD
TimeoutSec=180

[Install]
WantedBy=multi-user.target" > /etc/systemd/system/newfuture_ddns.service;

# Enable and start newfuture_ddns.timer
systemctl enable newfuture_ddns.timer;
systemctl start newfuture_ddns.timer;

echo "Use \"systemctl status newfuture_ddns.service\" to view run logs,
Use \"systemctl status newfuture_ddns.timer\" to view timer logs."
