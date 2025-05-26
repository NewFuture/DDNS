#!/bin/sh

if [ $# -eq 0 ]; then
  printenv > /etc/environment
  echo "*/5 * * * *  cd /ddns && /bin/ddns >> run.log 2>&1 " > /etc/crontabs/root
  exec /bin/ddns
  exec crond -f
else
  first=`echo $1 | cut -c1`
  if [ "$first" = "-" ]; then
    exec /bin/ddns $@
  else
    exec $@
  fi
fi
