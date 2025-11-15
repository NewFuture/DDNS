# -*- coding:utf-8 -*-
"""
Configuration loader for DDNS command-line interface.
@author: NewFuture
"""

import platform
import sys
from argparse import SUPPRESS, Action, ArgumentParser, RawTextHelpFormatter
from logging import DEBUG, basicConfig, getLevelName
from os import path as os_path

from ..scheduler import get_scheduler
from .file import save_config

__all__ = ["load_config", "str_bool"]


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
    """兼容 Python <3.8 的 extend action"""

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
            config_path = getattr(namespace, "config", None) or "config.json"  # type: str
            config_path = config_path[0] if isinstance(config_path, list) else config_path
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


def _add_ddns_args(arg):  # type: (ArgumentParser) -> None
    """Add common DDNS arguments to a parser"""
    log_levels = [
        "CRITICAL",  # 50
        "ERROR",  # 40
        "WARNING",  # 30
        "INFO",  # 20
        "DEBUG",  # 10
        "NOTSET",  # 0
    ]
    arg.add_argument(
        "-c",
        "--config",
        nargs="*",
        action=ExtendAction,
        metavar="FILE",
        help="load config file [配置文件路径, 可多次指定]",
    )
    arg.add_argument("--debug", action="store_true", help="debug mode [开启调试模式]")

    # DDNS Configuration group
    ddns = arg.add_argument_group("DDNS Configuration [DDNS配置参数]")
    ddns.add_argument(
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
            "edgeone_dns",
            "he",
            "huaweidns",
            "namesilo",
            "noip",
            "tencentcloud",
        ],
    )
    ddns.add_argument("--id", help="API ID or email [对应账号ID或邮箱]")
    ddns.add_argument("--token", help="API token or key [授权凭证或密钥]")
    ddns.add_argument("--endpoint", help="API endpoint URL [API端点URL]")
    ddns.add_argument(
        "--index4", nargs="*", action=ExtendAction, metavar="RULE", help="IPv4 rules [获取IPv4方式, 多次可配置多规则]"
    )
    ddns.add_argument(
        "--index6", nargs="*", action=ExtendAction, metavar="RULE", help="IPv6 rules [获取IPv6方式, 多次配置多规则]"
    )
    ddns.add_argument(
        "--ipv4", nargs="*", action=ExtendAction, metavar="DOMAIN", help="IPv4 domains [IPv4域名列表, 可配多个域名]"
    )
    ddns.add_argument(
        "--ipv6", nargs="*", action=ExtendAction, metavar="DOMAIN", help="IPv6 domains [IPv6域名列表, 可配多个域名]"
    )
    ddns.add_argument("--ttl", type=int, help="DNS TTL(s) [设置域名解析过期时间]")
    ddns.add_argument("--line", help="DNS line/route [DNS线路设置]")

    # Advanced Options group
    advanced = arg.add_argument_group("Advanced Options [高级参数]")
    advanced.add_argument("--proxy", nargs="*", action=ExtendAction, help="HTTP proxy [设置http代理，可配多个代理连接]")
    advanced.add_argument(
        "--cache", type=str_bool, nargs="?", const=True, help="set cache [启用缓存开关，或传入保存路径]"
    )
    advanced.add_argument(
        "--no-cache", dest="cache", action="store_const", const=False, help="disable cache [关闭缓存等效 --cache=false]"
    )
    advanced.add_argument(
        "--ssl",
        type=str_bool,
        nargs="?",
        const=True,
        help="SSL certificate verification [SSL证书验证方式]: "
        "true(强制验证), false(禁用验证), auto(自动降级), /path/to/cert.pem(自定义证书)",
    )
    advanced.add_argument(
        "--no-ssl",
        dest="ssl",
        action="store_const",
        const=False,
        help="disable SSL verify [禁用验证, 等效 --ssl=false]",
    )
    advanced.add_argument("--log_file", metavar="FILE", help="log file [日志文件，默认标准输出]")
    advanced.add_argument("--log.file", "--log-file", dest="log_file", help=SUPPRESS)  # 隐藏参数
    advanced.add_argument("--log_level", type=log_level, metavar="|".join(log_levels), help=None)
    advanced.add_argument("--log.level", "--log-level", dest="log_level", type=log_level, help=SUPPRESS)  # 隐藏参数
    advanced.add_argument("--log_format", metavar="FORMAT", help="set log format [日志格式]")
    advanced.add_argument("--log.format", "--log-format", dest="log_format", help=SUPPRESS)  # 隐藏参数
    advanced.add_argument("--log_datefmt", metavar="FORMAT", help="set log date format [日志时间格式]")
    advanced.add_argument("--log.datefmt", "--log-datefmt", dest="log_datefmt", help=SUPPRESS)  # 隐藏参数


def _add_task_subcommand_if_needed(parser):  # type: (ArgumentParser) -> None
    """
    Conditionally add task subcommand to avoid Python 2 'too few arguments' error.

    Python 2's argparse requires subcommand when subparsers are defined, but Python 3 doesn't.
    We only add subparsers when the first argument is likely a subcommand (doesn't start with '-').
    """
    # Python2 Only add subparsers when first argument is a subcommand (not an option)
    if len(sys.argv) <= 1 or (sys.argv[1].startswith("-") and sys.argv[1] != "--help"):
        return

    # Add subparsers for subcommands
    subparsers = parser.add_subparsers(dest="command", help="subcommands [子命令]")

    # Create task subcommand parser
    task = subparsers.add_parser("task", help="Manage scheduled tasks [管理定时任务]")
    task.set_defaults(func=_handle_task_command)
    _add_ddns_args(task)

    # Add task-specific arguments
    task.add_argument(
        "-i",
        "--install",
        nargs="?",
        type=int,
        const=5,
        metavar="MINs",
        help="Install task with <mins> [安装定时任务，默认5分钟]",
    )
    task.add_argument("--uninstall", action="store_true", help="Uninstall scheduled task [卸载定时任务]")
    task.add_argument("--status", action="store_true", help="Show task status [显示定时任务状态]")
    task.add_argument("--enable", action="store_true", help="Enable scheduled task [启用定时任务]")
    task.add_argument("--disable", action="store_true", help="Disable scheduled task [禁用定时任务]")
    task.add_argument(
        "--scheduler",
        choices=["auto", "systemd", "cron", "launchd", "schtasks"],
        default="auto",
        help="Specify scheduler type [指定定时任务方式]",
    )


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
    compiled = getattr(sys.modules["__main__"], "__compiled__", "")
    version_str = "v{} ({})\n{}\n{}\n{}".format(version, date, pyinfo, sysinfo, compiled)

    _add_ddns_args(parser)  # Add common DDNS arguments to main parser
    # Default behavior (no subcommand) - add all the regular DDNS options
    parser.add_argument("-v", "--version", action="version", version=version_str)
    parser.add_argument(
        "--new-config", metavar="FILE", action=NewConfigAction, nargs="?", help="generate new config [生成配置文件]"
    )

    # Python 2/3 compatibility: conditionally add subparsers to avoid 'too few arguments' error
    # Subparsers are only needed when user provides a subcommand (non-option argument)
    _add_task_subcommand_if_needed(parser)

    args, unknown = parser.parse_known_args()

    # Parse unknown arguments that follow --extra.xxx format
    extra_args = {}  # type: dict
    i = 0
    while i < len(unknown):
        arg = unknown[i]
        if arg.startswith("--extra."):
            key = "extra_" + arg[8:]  # Remove "--extra." and add "extra_" prefix
            # Check if there's a value for this argument
            if i + 1 < len(unknown) and not unknown[i + 1].startswith("--"):
                extra_args[key] = unknown[i + 1]
                i += 2
            else:
                # No value provided, set to True (flag)
                extra_args[key] = True  # type: ignore[assignment]
                i += 1
        else:
            # Unknown argument that doesn't match our pattern
            sys.stderr.write("Warning: Unknown argument: {}\n".format(arg))
            i += 1

    # Merge extra_args into args namespace
    for k, v in extra_args.items():
        setattr(args, k, v)

    # Handle task subcommand and exit early if present
    if hasattr(args, "func"):
        args.func(vars(args))
        sys.exit(0)

    is_debug = getattr(args, "debug", False)
    if is_debug:
        # 如果启用调试模式，则强制设置日志级别为 DEBUG
        args.log_level = log_level("DEBUG")
        if args.cache is None:
            args.cache = False  # 禁用缓存

    # 将 Namespace 对象转换为字典并直接返回
    config = vars(args)
    return {k: v for k, v in config.items() if v is not None}  # 过滤掉 None 值的配置项


def _handle_task_command(args):  # type: (dict) -> None
    """Handle task subcommand"""
    basicConfig(level=args["debug"] and DEBUG or args.get("log_level", "INFO"))

    # Use specified scheduler or auto-detect
    scheduler_type = args.get("scheduler", "auto")
    scheduler = get_scheduler(scheduler_type)

    interval = args.get("install", 5) or 5
    excluded_keys = ("status", "install", "uninstall", "enable", "disable", "command", "scheduler", "func")
    ddns_args = {k: v for k, v in args.items() if k not in excluded_keys and v is not None}

    # Execute operations
    for op in ["install", "uninstall", "enable", "disable"]:
        if not args.get(op):
            continue

        # Check if task is installed for enable/disable
        if op in ["enable", "disable"] and not scheduler.is_installed():
            print("DDNS task is not installed" + (" Please install it first." if op == "enable" else "."))
            sys.exit(1)

        # Execute operation
        print("{} DDNS scheduled task...".format(op.title()))
        func = getattr(scheduler, op)
        result = func(interval, ddns_args) if op == "install" else func()

        if result:
            past_tense = {
                "install": "installed",
                "uninstall": "uninstalled",
                "enable": "enabled",
                "disable": "disabled",
            }[op]
            suffix = " with {} minute interval".format(interval) if op == "install" else ""
            print("DDNS task {} successfully{}".format(past_tense, suffix))
        else:
            print("Failed to {} DDNS task".format(op))
            sys.exit(1)
        return

    # Show status or auto-install
    status = scheduler.get_status()

    if args.get("status") or status["installed"]:
        print("DDNS Task Status:")
        print("  Installed: {}".format("Yes" if status["installed"] else "No"))
        print("  Scheduler: {}".format(status["scheduler"]))
        if status["installed"]:
            print("  Enabled: {}".format(status.get("enabled", "unknown")))
            print("  Interval: {} minutes".format(status.get("interval", "unknown")))
            print("  Command: {}".format(status.get("command", "unknown")))
            print("  Description: {}".format(status.get("description", "")))
    else:
        print("DDNS task is not installed. Installing with default settings...")
        if scheduler.install(interval, ddns_args):
            print("DDNS task installed successfully with {} minute interval".format(interval))
        else:
            print("Failed to install DDNS task")
            sys.exit(1)
