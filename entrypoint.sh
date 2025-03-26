#!/usr/bin/env sh

# CN: 该脚本用于在容器启动时执行 ddns 命令, 并创建定时任务
# EN: This script is used to execute the ddns command when the container starts and create a scheduled task

# CN: 如果没有传入参数
# EN: If no parameters are passed in
if [ $# -eq 0 ]; then
    printenv > /etc/environment

    ### CONF FILE OR ENV ###
    # CN: 不存在 /config 文件夹，则执行
    # EN: If the /config folder does not exist, execute
    if [ ! -d /config ]; then
        # CN: 不存在 /config.json 文件,则执行 /ddns
        # EN: If the /config.json file does not exist, execute /ddns
        if [ ! -f /config.json ]; then
            exec /ddns
        fi
        exec /ddns -c /config.json
        echo "*/5 * * * *   /ddns -c /config.json" > /etc/crontabs/root
        exec crond -f
    fi
    ### CONF FILE OR ENV ###

    ### CONF PATH        ###
    # CN: 存在 /config 文件夹,则遍历 /config 文件夹下的json文件,依次执行 /ddns -c /config/xxx.json
    # EN: If the /config folder exists, traverse the json file under the /config folder, and execute /ddns -c /config/xxx.json
    if [ -d /config ]; then
      cat >/tmp/run.sh << 'END_OF_SCRIPT'
#!/usr/bin/env sh
# CN: 遍历 /config 文件夹下的json文件,依次执行 /ddns -c /config/xxx.json
# EN: Traverse the json file under the /config folder, and execute /ddns -c /config/xxx.json
for file in /config/*.json
do
    /ddns -c $file
done
END_OF_SCRIPT
        chmod +x /tmp/run.sh
        # CN: 执行 /tmp/run.sh
        # EN: Execute /tmp/run.sh
        /tmp/run.sh
        echo "*/5 * * * *   /tmp/run.sh" > /etc/crontabs/root
        exec crond -f
    fi
    ### CONF PATH        ###

else

    first=`echo $1 | cut -c1`
    if [ "$first" = "-" ]; then
        exec /ddns $@
        # CN: 创建定时任务
        # EN: Create a scheduled task
        echo "*/5 * * * *   /ddns $@" > /etc/crontabs/root
        # CN: 执行定时任务
        # EN: Execute the scheduled task
        exec crond -f
    else
        exec $@
    fi
fi
