#!/bin/bash
service='[Unit]
Description=NewFuture ddns
After=network.target
 
[Service]
Type=simple
WorkingDirectory=/usr/share/DDNS
ExecStart=/usr/bin/env python /usr/share/DDNS/run.py -c /etc/DDNS/config.json
 
[Install]
WantedBy=multi-user.target'

timer='[Unit]
Description=NewFuture ddns timer
 
[Timer]
OnUnitActiveSec=5m
Unit=ddns.service

[Install]
WantedBy=multi-user.target'

if [[ "install" == $1 ]]; then
    echo "$service" > /usr/lib/systemd/system/ddns.service
    echo "$timer" > /usr/lib/systemd/system/ddns.timer
    cp -r `pwd` /usr/share/
    mkdir -p /etc/DDNS
    if [ ! -f "/etc/DDNS/config.json" ];then
        if [ -f "config.json" ];then
            cp config.json /etc/DDNS/config.json
        fi
    fi
    systemctl enable ddns.timer
    systemctl start ddns.timer
    echo "installed"
    echo "useful commands:"
    echo "  systemctl status ddns       view service status."
    echo "  journalctl -u ddns.timer    view the logs."
    echo "config file: /etc/DDNS/config.json"
                
elif [[ "uninstall" == $1 ]]; then
    systemctl disable ddns.timer
    rm /usr/lib/systemd/system/ddns.service
    rm /usr/lib/systemd/system/ddns.timer
    rm -rf /etc/DDNS
    rm -rf /usr/share/DDNS
    systemctl daemon-reload
    echo "uninstalled"
else
    echo "Tips:"
    echo "  $0 install      install the ddns systemd service."
    echo "  $0 uninstall    uninstall the ddns service."
fi
