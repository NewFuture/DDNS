#!/bin/sh

stop_startup() {
  # tini -g already signaled this process group. Stay alive until those
  # processes finish handling SIGTERM, or container teardown will SIGKILL them.
  while :; do
    wait 2>/dev/null || true
    pending=0
    for stat_file in /proc/[0-9]*/stat; do
      [ -f "$stat_file" ] || continue
      pid=${stat_file#/proc/}
      pid=${pid%/stat}
      [ "$pid" = "$$" ] && continue
      pgrp=$(sed -n 's/.*) [^ ]* [^ ]* \([^ ]*\).*/\1/p' "$stat_file" 2>/dev/null || true)
      if [ "$pgrp" = "$$" ]; then
        pending=1
        break
      fi
    done
    [ "$pending" -eq 0 ] && break
    sleep 0.1
  done
  exit 143
}

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
  # Use DDNS_CRON environment variable for cron schedule, default to every 5 minutes
  CRON_SCHEDULE="${DDNS_CRON:-*/5 * * * *}"
  echo "${CRON_SCHEDULE}  cd /ddns && /bin/ddns" > /etc/crontabs/root
  trap stop_startup TERM INT
  /bin/ddns
  status=$?
  trap - TERM INT
  if [ "$status" -eq 0 ]; then
    echo "Cron daemon will run with schedule: ${CRON_SCHEDULE}"
    exec crond -f
  fi
  exit "$status"
else
  first=`echo $1 | cut -c1`
  if [ "$first" = "-" ]; then
    exec /bin/ddns $@
  else
    exec $@
  fi
fi
