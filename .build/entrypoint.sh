#!/bin/sh

if [ $# -eq 0 ]; then
  printenv > /etc/environment
  echo "*/5 * * * *   /ddns -c /config.json" > /etc/crontabs/root
  exec crond -f
else
  first=`echo $1 | cut -c1`
  if [ "$first" = "-" ]; then
    exec /ddns $@
  else
    exec $@
  fi
fi
