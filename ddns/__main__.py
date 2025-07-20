# -*- coding:utf-8 -*-
"""
DDNS
@author: NewFuture, rufengsuixing
"""

from io import TextIOWrapper
from subprocess import check_output
from logging import getLogger
import sys

from .__init__ import __version__, __description__, build_date
from .config import load_configs, Config  # noqa: F401
from .provider import get_provider_class, SimpleProvider
from . import ip
from .cache import Cache
from .task import TaskManager, print_task_status

logger = getLogger()
# Set user agent for All Providers
SimpleProvider.user_agent = SimpleProvider.user_agent.format(version=__version__)


def get_ip(ip_type, rules):
    """
    get IP address
    """
    if rules is False:  # disabled
        return False
    for i in rules:
        try:
            logger.debug("get_ip:(%s, %s)", ip_type, i)
            if str(i).isdigit():  # 数字 local eth
                return getattr(ip, "local_v" + ip_type)(i)
            elif i.startswith("cmd:"):  # cmd
                return str(check_output(i[4:]).strip().decode("utf-8"))
            elif i.startswith("shell:"):  # shell
                return str(check_output(i[6:], shell=True).strip().decode("utf-8"))
            elif i.startswith("url:"):  # 自定义 url
                return getattr(ip, "public_v" + ip_type)(i[4:])
            elif i.startswith("regex:"):  # 正则 regex
                return getattr(ip, "regex_v" + ip_type)(i[6:])
            else:
                return getattr(ip, i + "_v" + ip_type)()
        except Exception as e:
            logger.error("Failed to get %s address: %s", ip_type, e)
    return None


def update_ip(dns, cache, index_rule, domains, record_type, config):
    # type: (SimpleProvider, Cache | None, list[str]|bool, list[str], str, Config) -> bool | None
    """
    更新IP并变更DNS记录
    """
    if not domains:
        return None

    ip_type = "4" if record_type == "A" else "6"
    address = get_ip(ip_type, index_rule)
    if not address:
        logger.error("Fail to get %s address!", ip_type)
        return False

    update_success = False

    for domain in domains:
        domain = domain.lower()
        cache_key = "{}:{}".format(domain, record_type)
        if cache and cache.get(cache_key) == address:
            logger.info("%s[%s] address not changed, using cache: %s", domain, record_type, address)
            update_success = True
        else:
            try:
                result = dns.set_record(domain, address, record_type=record_type, ttl=config.ttl, line=config.line)
                if result:
                    logger.warning("set %s[IPv%s]: %s successfully.", domain, ip_type, address)
                    update_success = True
                    if isinstance(cache, dict):
                        cache[cache_key] = address
                else:
                    logger.error("Failed to update %s record for %s", record_type, domain)
            except Exception as e:
                logger.exception("Failed to update %s record for %s: %s", record_type, domain, e)
    return update_success


def run(config):
    # type: (Config) -> bool
    """
    Run the DDNS update process
    """
    # 设置IP模块的SSL验证配置
    ip.ssl_verify = config.ssl

    # dns provider class
    provider_class = get_provider_class(config.dns)
    dns = provider_class(
        config.id, config.token, endpoint=config.endpoint, logger=logger, proxy=config.proxy, ssl=config.ssl
    )
    cache = Cache.new(config.cache, config.md5(), logger)
    return (
        update_ip(dns, cache, config.index4, config.ipv4, "A", config) is not False
        and update_ip(dns, cache, config.index6, config.ipv6, "AAAA", config) is not False
    )


def handle_task_command_from_args():
    # type: () -> None
    """
    Handle task subcommand by parsing arguments separately
    """
    from argparse import ArgumentParser, RawTextHelpFormatter
    
    parser = ArgumentParser(
        prog='ddns task',
        description='Manage DDNS scheduled tasks',
        formatter_class=RawTextHelpFormatter
    )
    
    task_group = parser.add_mutually_exclusive_group()
    task_group.add_argument('--status', action='store_true', 
                           help='query task status [查询定时任务状态]')
    task_group.add_argument('-i', '--install', action='store_true',
                           help='install scheduled task [安装定时任务]')
    task_group.add_argument('--delete', action='store_true',
                           help='delete scheduled task [删除定时任务]')
    
    parser.add_argument('--interval', type=int, default=5, metavar='MINUTES',
                        help='task execution interval in minutes (default: 5) [执行间隔分钟数，默认5分钟]')
    parser.add_argument('--scheduler', choices=['systemd', 'cron', 'launchd', 'schtasks'],
                        help='preferred task scheduler [指定任务调度器]')
    parser.add_argument('--force', action='store_true',
                        help='force reinstall if task already exists [强制重新安装]')
    parser.add_argument('-c', '--config', metavar='FILE',
                        help='config file for scheduled task [定时任务使用的配置文件]')
    
    # Parse arguments starting from index 2 (skip 'ddns' and 'task')
    args = parser.parse_args(sys.argv[2:])
    
    logger = getLogger("ddns.task")
    task_manager = TaskManager(logger)
    
    # Determine action
    if args.status:
        action = 'status'
    elif args.install:
        action = 'install'
    elif args.delete:
        action = 'delete'
    else:
        action = 'auto'  # Default action: show status and install if needed
    
    if action == 'status':
        # Show task status
        status = task_manager.get_task_status()
        print_task_status(status)
        
    elif action == 'install':
        # Install task
        success = task_manager.install_task(
            scheduler=args.scheduler,
            interval=args.interval,
            config_file=args.config,
            force=args.force
        )
        
        if not success:
            sys.exit(1)
            
    elif action == 'delete':
        # Uninstall task
        success = task_manager.uninstall_task(scheduler=args.scheduler)
        
        if not success:
            sys.exit(1)
            
    elif action == 'auto':
        # Auto mode: show status, install if not installed
        status = task_manager.get_task_status()
        
        if status['installed']:
            print_task_status(status)
        else:
            print_task_status(status)
            print("")
            print("Task not installed. Installing with default settings...")
            
            success = task_manager.install_task(
                interval=args.interval,
                config_file=args.config
            )
            
            if not success:
                sys.exit(1)
            else:
                print("Task installed successfully!")


def handle_task_command(task_config):
    # type: (dict) -> None
    """
    Handle task subcommand
    """
    logger = getLogger("ddns.task")
    task_manager = TaskManager(logger)
    
    action = task_config.get('task_action', 'auto')
    
    if action == 'status':
        # Show task status
        status = task_manager.get_task_status()
        print_task_status(status)
        
    elif action == 'install':
        # Install task
        interval = task_config.get('interval', 5)
        scheduler = task_config.get('scheduler')
        config_file = task_config.get('config')
        force = task_config.get('force', False)
        
        success = task_manager.install_task(
            scheduler=scheduler,
            interval=interval,
            config_file=config_file,
            force=force
        )
        
        if not success:
            sys.exit(1)
            
    elif action == 'delete':
        # Uninstall task
        scheduler = task_config.get('scheduler')
        success = task_manager.uninstall_task(scheduler=scheduler)
        
        if not success:
            sys.exit(1)
            
    elif action == 'auto':
        # Auto mode: show status, install if not installed
        status = task_manager.get_task_status()
        
        if status['installed']:
            print_task_status(status)
        else:
            print_task_status(status)
            print("")
            print("Task not installed. Installing with default settings...")
            
            interval = task_config.get('interval', 5)
            config_file = task_config.get('config')
            
            success = task_manager.install_task(
                interval=interval,
                config_file=config_file
            )
            
            if not success:
                sys.exit(1)
            else:
                print("Task installed successfully!")


def main():
    encode = sys.stdout.encoding
    if encode is not None and encode.lower() != "utf-8" and hasattr(sys.stdout, "buffer"):
        # 兼容windows 和部分ASCII编码的老旧系统
        sys.stdout = TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        sys.stderr = TextIOWrapper(sys.stderr.buffer, encoding="utf-8")
    logger.name = "ddns"

    # Check if this is a task command by examining sys.argv
    if len(sys.argv) > 1 and sys.argv[1] == 'task':
        # Handle task command with a separate parser
        handle_task_command_from_args()
        return

    # 使用多配置加载器，它会自动处理单个和多个配置
    configs = load_configs(__description__, __version__, build_date)

    if len(configs) == 1:
        # 单个配置，使用原有逻辑（向后兼容）
        config = configs[0]
        success = run(config)
        if not success:
            sys.exit(1)
    else:
        # 多个配置，使用新的批处理逻辑
        overall_success = True
        for i, config in enumerate(configs):
            # 如果log_level有值则设置setLevel
            if hasattr(config, "log_level") and config.log_level:
                logger.setLevel(config.log_level)
            logger.info("Running configuration %d/%d", i + 1, len(configs))
            # 记录当前provider
            logger.info("Using DNS provider: %s", config.dns)
            success = run(config)
            if not success:
                overall_success = False
                logger.error("Configuration %d failed", i + 1)
            else:
                logger.info("Configuration %d completed successfully", i + 1)

        if not overall_success:
            logger.error("Some configurations failed")
            sys.exit(1)
        else:
            logger.info("All configurations completed successfully")


if __name__ == "__main__":
    main()
