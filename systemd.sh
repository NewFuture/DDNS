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

if [[ "install" == $1 ]]; then
    echo "$service" > /usr/lib/systemd/system/ddns.service
    echo "$timer" > /usr/lib/systemd/system/ddns.timer
    cp -r `pwd` /usr/share/
    mkdir -p /etc/DDNS
    if [ ! -f "/etc/DDNS/config.json" ];then
        if [ ! -f "config.json" ];then
            echo "create new template configure file on /etc/DDNS/config.json"
        else
            cp config.json /etc/DDNS/config.json
            echo "config file is /etc/DDNS/config.json"
        fi
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
