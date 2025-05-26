#!/bin/sh

if [ $# -eq 0 ]; then
  printenv > /etc/environment
  echo "*/5 * * * *   /bin/ddns -c /config.json >> /ddns/ddns.log" > /etc/crontabs/root
  exec crond -f
else
  first=`echo $1 | cut -c1`
  if [ "$first" = "-" ]; then
    exec /bin/ddns $@
  else
    exec $@
  fi
fi
