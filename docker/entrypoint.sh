#!/bin/sh

if [ $# -eq 0 ]; then
  printenv > /etc/environment
  if [ -f /config.json ]; then
    echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
    if [ ! -f /ddns/config.json ]; then
      ln -s /config.json /ddns/config.json
      echo "WARNING: /ddns/config.json not found. Created symlink to /config.json."
    fi
     echo "WARNING: From v4.0.0, the working dir is /ddns/"
     echo "WARNING: Please map your host folder to /ddns/"
     echo "[old] -v /host/folder/config.json:/config.json"
     echo "[new] -v /host/folder/:/ddns/"
     echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
  fi
  echo "*/5 * * * *  cd /ddns && /bin/ddns" > /etc/crontabs/root
  /bin/ddns &&  echo "Cron daemon will run every 5 minutes..." && exec crond -f
else
  first=`echo $1 | cut -c1`
  if [ "$first" = "-" ]; then
    exec /bin/ddns $@
  else
    exec $@
  fi
fi
