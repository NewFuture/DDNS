#!/usr/bin/env bash
RUN_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )";
echo "*/5 * * * *   root    ${RUN_DIR}/run.sh" > /etc/cron.d/ddns;
/etc/init.d/cron reload;
