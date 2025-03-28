#!/usr/bin/env sh
set -x

# CN: 该脚本用于在容器启动时执行 ddns 命令, 并创建定时任务
# EN: This script is used to execute the ddns command when the container starts and create a scheduled task

# CN: 运行 `ddns` 命令, 在容器启动时执行 `ddns` 命令, 并创建定时任务
# EN: Run the `ddns` command, execute the `ddns` command when the container starts, and create a cron job
function  fun_run_and_crond()
{
    printenv > /etc/environment
    # CN: 如果传入参数包含 `-h` 或 `--help`, 则执行 `ddns -h` 命令
    # EN: If the parameter contains `-h` or `--help`, execute the `ddns -h` command
    if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
        exec /ddns -h
        return
    fi
    ### CONF FILE OR ENV ###
    # CN: 不存在 /config 文件夹，则执行命令
    # EN: If the /config folder does not exist, execute the command
    if [ ! -d /config ]; then
        exec /ddns $@
        echo "*/5 * * * *  /ddns $@" > /etc/crontabs/root
        exec crond -f
    fi
    ### CONF FILE OR ENV ###
    
    ### CONF PATH        ###
    # CN: 存在 /config 文件夹, 且文件夹下有json文件, 则创建shell脚本
    # EN: If the /config folder exists, and there are json files under the folder, create a shell script
    if [ -d /config ]; then
        if [ ! "$(ls -A /config/*.json 2>/dev/null)" ]; then
            ecec /ddns  -c /config/config.json $@
        fi
    cat >/tmp/run.sh << 'EOF'
#!/usr/bin/env sh
set -x
# CN: 遍历 /config 文件夹下的json文件,依次执行 /ddns -c /config/xxx.json
# EN: Traverse the json file under the /config folder, and execute /ddns -c /config/xxx.json
for file in /config/*.json
do
    /ddns -c $file $@
done
EOF
        chmod +x /tmp/run.sh
        /tmp/run.sh
        echo "*/5 * * * *   /tmp/run.sh" > /etc/crontabs/root
        exec crond -f
    fi
    ### CONF PATH        ###
    
}


if [ $# -eq 0 ]; then
    fun_run_and_crond
else
    first=`echo $1 | cut -c1`
    if [ "$first" = "-" ]; then
        fun_run_and_crond $@
    else
        exec $@
    fi
fi
