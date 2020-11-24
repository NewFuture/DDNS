# /bin/bash
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

config='{
    "$schema": "https://ddns.newfuture.cc/schema/v2.8.json",
    "id": "YOUR ID or EAMIL for DNS Provider",
    "token": "YOUR TOKEN or KEY for DNS Provider",
    "dns": "dnspod",
    "ipv4": [
        "newfuture.cc",
        "ddns.newfuture.cc"
    ],
    "ipv6": [
        "newfuture.cc",
        "ipv6.ddns.newfuture.cc"
    ],
    "index4": "default",
    "index6": "default",
    "ttl": None,
    "proxy": None,
    "debug": False,
}'

if [[ "install" == $1 ]]; then
    echo "$service" > /usr/lib/systemd/system/ddns.service
    echo "$timer" > /usr/lib/systemd/system/ddns.timer
    cp -r `pwd` /usr/share/
    mkdir -p /etc/DDNS
    if [ ! -f "/etc/DDNS/config.json" ];then
        echo "$config" > /etc/DDNS/config.json
        echo "create new config file on /etc/DDNS/config.json"
    fi
    systemctl enable ddns.timer
    systemctl start ddns.timer
    echo "installed"
    echo "use systemctl status ddns to view service status"
    echo "use journalctl -u ddns.timer to view logs"
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
    echo "use install to install"
    echo "use uninstall to uninstall"
fi