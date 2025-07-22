# -*- coding:utf-8 -*-
"""
Configuration loader for DDNS command-line interface.
@author: NewFuture
"""

from argparse import Action, ArgumentParser, RawTextHelpFormatter, SUPPRESS
from logging import getLevelName
from os import path as os_path
import platform
import sys

from .file import save_config

__all__ = ["load_config", "str_bool", "handle_task_command"]


def str_bool(v):
    # type: (str | bool | None | int | float | list) -> bool | str
    """
    parse string to boolean
    """
    if isinstance(v, bool):
        return v
    if v is None:
        return False
    if not isinstance(v, str) and not type(v).__name__ == "unicode":
        return bool(v)  # For non-string types, convert to string first
    if v.lower() in ("yes", "true", "t", "y", "1"):  # type: ignore[attribute-defined]
        return True
    elif v.lower() in ("no", "false", "f", "n", "0"):  # type: ignore[attribute-defined]
        return False
    else:
        return v  # type: ignore[return-value]


def log_level(value):
    """
    parse string to log level
    or getattr(logging, value.upper())
    """
    return getLevelName(value if isinstance(value, int) else value.upper())


def _get_system_info_str():
    system = platform.system()
    release = platform.release()
    machine = platform.machine()
    arch = platform.architecture()
    return "{}-{} {} {}".format(system, release, machine, arch)


def _get_python_info_str():
    version = platform.python_version()
    branch, py_build_date = platform.python_build()
    return "Python-{} {} ({})".format(version, branch, py_build_date)


class ExtendAction(Action):
    """
    兼容 Python <3.8 的 extend action
    """

    def __call__(self, parser, namespace, values, option_string=None):
        items = getattr(namespace, self.dest, None)
        if items is None:
            items = []
        # values 可能是单个值或列表
        if isinstance(values, list):
            items.extend(values)
        else:
            items.append(values)
        setattr(namespace, self.dest, items)


class NewConfigAction(Action):
    """生成配置文件并退出程序"""

    def __call__(self, parser, namespace, values, option_string=None):

        # 获取配置文件路径
        if values and values != "true":
            config_path = str(values)  # type: str
        else:
            config_path = getattr(namespace, "config", "config.json")  # type: str
            if os_path.exists(config_path):
                sys.stderr.write("The default %s already exists!\n" % config_path)
                sys.stdout.write("Please use `--new-config=%s` to specify a new config file.\n" % config_path)
                sys.exit(1)
        # 获取当前已解析的参数
        current_config = {k: v for k, v in vars(namespace).items() if v is not None}
        # 保存配置文件
        save_config(config_path, current_config)
        sys.stdout.write("%s is generated.\n" % config_path)
        sys.exit(0)


def load_config(description, doc, version, date):
    # type: (str, str, str, str) -> dict
    """
    解析命令行参数并返回配置字典。

    Args:
        description (str): 程序描述
        doc (str): 程序文档
        version (str): 程序版本
        date (str): 构建日期

    Returns:
        dict: 配置字典
    """
    parser = ArgumentParser(description=description, epilog=doc, formatter_class=RawTextHelpFormatter)
    sysinfo = _get_system_info_str()
    pyinfo = _get_python_info_str()
    version_str = "v{} ({})\n{}\n{}".format(version, date, pyinfo, sysinfo)
    log_levels = [
        "CRITICAL",  # 50
        "ERROR",  # 40
        "WARNING",  # 30
        "INFO",  # 20
        "DEBUG",  # 10
        "NOTSET",  # 0
    ]
    
    # Add subparsers for subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands [可用的子命令]")
    
    # Default behavior (no subcommand) - add all the regular DDNS options
    parser.add_argument("-v", "--version", action="version", version=version_str)
    parser.add_argument(
        "-c",
        "--config",
        nargs="*",
        action=ExtendAction,
        metavar="FILE",
        help="load config file [配置文件路径, 可多次指定]",
    )
    parser.add_argument("--debug", action="store_true", help="debug mode [开启调试模式]")
    parser.add_argument(
        "--new-config", metavar="FILE", action=NewConfigAction, nargs="?", help="generate new config [生成配置文件]"
    )
    
    # Task subcommand
    task_parser = subparsers.add_parser("task", help="Manage scheduled tasks [管理定时任务]")
    task_parser.add_argument(
        "--status", action="store_true",
        help="Show task installation status [显示定时任务安装状态]"
    )
    task_parser.add_argument(
        "--install", "-i", nargs="?", type=int, const=5, metavar="MINUTES",
        help="Install scheduled task with interval in minutes (default: 5) [安装定时任务，指定间隔分钟数，默认5分钟]"
    )
    task_parser.add_argument(
        "--delete", action="store_true",
        help="Delete installed scheduled task [删除已安装的定时任务]"
    )
    task_parser.add_argument(
        "-c", "--config", default="config.json",
        help="Config file path for scheduled task [定时任务使用的配置文件路径]"
    )
    task_parser.add_argument(
        "--log-file", default="ddns.log",
        help="Log file path for scheduled task [定时任务使用的日志文件路径]"
    )

    # Regular DDNS parameters (only when no subcommand is used)
    parser.add_argument(
        "--dns",
        help="DNS provider [DNS服务提供商]",
        choices=[
            "51dns",
            "alidns",
            "aliesa",
            "callback",
            "cloudflare",
            "debug",
            "dnscom",
            "dnspod_com",
            "dnspod",
            "edgeone",
            "he",
            "huaweidns",
            "namesilo",
            "noip",
            "tencentcloud",
        ],
    )
    parser.add_argument("--id", help="API ID or email [对应账号ID或邮箱]")
    parser.add_argument("--token", help="API token or key [授权凭证或密钥]")
    parser.add_argument("--endpoint", help="API endpoint URL [API端点URL]")
    parser.add_argument(
        "--index4",
        nargs="*",
        action=ExtendAction,
        metavar="RULE",
        help="IPv4 rules [获取IPv4方式, 多次可配置多规则]",
    )
    parser.add_argument(
        "--index6",
        nargs="*",
        action=ExtendAction,
        metavar="RULE",
        help="IPv6 rules [获取IPv6方式, 多次可配置多规则]",
    )
    parser.add_argument(
        "--ipv4",
        nargs="*",
        action=ExtendAction,
        metavar="DOMAIN",
        help="IPv4 domains [IPv4域名列表, 可配置多个域名]",
    )
    parser.add_argument(
        "--ipv6",
        nargs="*",
        action=ExtendAction,
        metavar="DOMAIN",
        help="IPv6 domains [IPv6域名列表, 可配置多个域名]",
    )
    parser.add_argument("--ttl", type=int, help="DNS TTL(s) [设置域名解析过期时间]")
    parser.add_argument("--line", help="DNS line/route [DNS线路设置，如电信、联通、移动等]")
    parser.add_argument(
        "--proxy",
        nargs="*",
        action=ExtendAction,
        help="HTTP proxy [设置http代理，可配多个代理连接]",
    )
    parser.add_argument(
        "--cache",
        type=str_bool,
        nargs="?",
        const=True,
        help="set cache [启用缓存开关，或传入保存路径]",
    )
    parser.add_argument(
        "--no-cache",
        dest="cache",
        action="store_const",
        const=False,
        help="disable cache [关闭缓存等效 --cache=false]",
    )
    parser.add_argument(
        "--ssl",
        type=str_bool,
        nargs="?",
        const=True,
        help="SSL certificate verification [SSL证书验证方式]: "
        "true(强制验证), false(禁用验证), auto(自动降级), /path/to/cert.pem(自定义证书)",
    )
    parser.add_argument(
        "--no-ssl",
        dest="ssl",
        action="store_const",
        const=False,
        help="disable SSL verify [禁用验证, 等效 --ssl=false]",
    )
    parser.add_argument("--log_file", metavar="FILE", help="log file [日志文件，默认标准输出]")
    parser.add_argument("--log.file", "--log-file", dest="log_file", help=SUPPRESS)  # 隐藏参数
    parser.add_argument("--log_level", type=log_level, metavar="|".join(log_levels), help=None)
    parser.add_argument("--log.level", "--log-level", dest="log_level", type=log_level, help=SUPPRESS)  # 隐藏参数
    parser.add_argument("--log_format", metavar="FORMAT", help="set log format [日志格式]")
    parser.add_argument("--log.format", "--log-format", dest="log_format", help=SUPPRESS)  # 隐藏参数
    parser.add_argument("--log_datefmt", metavar="FORMAT", help="set log date format [日志时间格式]")
    parser.add_argument("--log.datefmt", "--log-datefmt", dest="log_datefmt", help=SUPPRESS)  # 隐藏参数

    args = parser.parse_args()
    is_debug = getattr(args, "debug", False)
    if is_debug:
        # 如果启用调试模式，则强制设置日志级别为 DEBUG
        args.log_level = log_level("DEBUG")
        if args.cache is None:
            args.cache = False  # 禁用缓存

    # 将 Namespace 对象转换为字典并直接返回
    config = vars(args)
    return {k: v for k, v in config.items() if v is not None}  # 过滤掉 None 值的配置项


def handle_task_command(args):
    # type: (dict) -> None
    """
    Handle task subcommand
    
    Args:
        args (dict): Parsed command line arguments
    """
    # Import here to avoid circular imports
    import sys
    from logging import getLogger
    from ..util.task import TaskManager
    
    logger = getLogger()
    
    config_path = args.get("config", "config.json")
    log_file = args.get("log_file", "ddns.log")
    
    # Default interval is 5 minutes
    interval = 5
    if args.get("install") is not None:
        interval = args["install"]
    
    task_manager = TaskManager(config_path=config_path, log_path=log_file, interval=interval)
    
    # Handle different task operations
    if args.get("install") is not None:
        # Install task
        logger.info("Installing DDNS scheduled task...")
        if task_manager.install(force=True):
            logger.info("DDNS task installed successfully with %d minute interval", interval)
        else:
            logger.error("Failed to install DDNS task")
            sys.exit(1)
    elif args.get("delete"):
        # Delete task
        logger.info("Uninstalling DDNS scheduled task...")
        if task_manager.uninstall():
            logger.info("DDNS task uninstalled successfully")
        else:
            logger.error("Failed to uninstall DDNS task")
            sys.exit(1)
    elif args.get("status"):
        # Show status only
        status = task_manager.get_status()
        print("DDNS Task Status:")
        print("  Installed: {}".format("Yes" if status["installed"] else "No"))
        print("  Scheduler: {}".format(status["scheduler"]))
        print("  System: {}".format(status["system"]))
        if status["installed"]:
            print("  Running Status: {}".format(status.get("running_status", "unknown")))
            print("  Interval: {} minutes".format(status["interval"]))
            print("  Config Path: {}".format(status["config_path"]))
            print("  Log Path: {}".format(status["log_path"]))
    else:
        # Default behavior: show status and install if not installed
        status = task_manager.get_status()
        if status["installed"]:
            print("DDNS Task Status:")
            print("  Installed: Yes")
            print("  Scheduler: {}".format(status["scheduler"]))
            print("  Running Status: {}".format(status.get("running_status", "unknown")))
            print("  Interval: {} minutes".format(status["interval"]))
            print("  Config Path: {}".format(status["config_path"]))
            print("  Log Path: {}".format(status["log_path"]))
        else:
            print("DDNS task is not installed. Installing with default settings...")
            if task_manager.install():
                print("DDNS task installed successfully with {} minute interval".format(interval))
            else:
                print("Failed to install DDNS task")
                sys.exit(1)
