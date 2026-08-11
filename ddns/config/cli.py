# -*- coding:utf-8 -*-
"""
Configuration loader for DDNS command-line interface.
@author: NewFuture
"""

import platform
import sys
from argparse import SUPPRESS, Action, ArgumentParser, ArgumentTypeError, RawTextHelpFormatter
from logging import DEBUG, basicConfig, getLevelName, getLogger
from os import path as os_path

from ..scheduler import get_scheduler
from .env import load_config as load_env_config
from .file import DEFAULT_CONFIG_PATHS, load_config as load_file_config, save_config

__all__ = ["load_config", "str_bool"]

try:
    integer_types = (int, long)  # type: ignore[name-defined]
except NameError:
    integer_types = (int,)


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


def non_negative_int(value):
    # type: (str) -> int
    """Parse a non-negative integer CLI option."""
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        raise ArgumentTypeError("must be a non-negative integer")
    if parsed < 0:
        raise ArgumentTypeError("must be a non-negative integer")
    return parsed


def port_number(value):
    # type: (str) -> int
    """Parse a valid TCP port number."""
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        raise ArgumentTypeError("must be a valid TCP port")
    if parsed < 1 or parsed > 65535:
        raise ArgumentTypeError("must be between 1 and 65535")
    return parsed


def interval_minutes(value):
    # type: (object) -> int
    """Parse a web scheduler interval."""
    if isinstance(value, (bool, float)):
        raise ArgumentTypeError("must be an integer between 1 and 1440")
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        raise ArgumentTypeError("must be an integer between 1 and 1440")
    if parsed < 1 or parsed > 1440:
        raise ArgumentTypeError("must be an integer between 1 and 1440")
    return parsed


def config_interval_minutes(value):
    # type: (object) -> int
    """Parse a JSON interval without coercing non-integer types."""
    if isinstance(value, bool) or not isinstance(value, integer_types):
        raise ArgumentTypeError("must be an integer between 1 and 1440")
    return interval_minutes(value)


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
            "cloudns",
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
            "west",
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
        "--cache-max-age",
        "--cache_max_age",
        dest="cache_max_age",
        type=non_negative_int,
        help="cache file max age in seconds [缓存文件最大有效期，单位秒]",
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


def _add_task_subcommand(subparsers):
    # type: (object) -> None
    """Add scheduled-task command arguments."""
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


def _add_web_subcommand(subparsers):
    # type: (object) -> None
    """Add embedded dashboard command arguments."""
    web = subparsers.add_parser("web", help="Run local management dashboard [运行本机管理控制台]")
    web.set_defaults(func=_handle_web_command)
    web.add_argument("-c", "--config", metavar="FILE", help="local config file [本机配置文件]")
    web.add_argument(
        "--host", choices=["127.0.0.1", "localhost", "::1"], default="127.0.0.1", help="loopback address [本机监听地址]"
    )
    web.add_argument("--port", type=port_number, default=9876, help="dashboard port [控制台端口]")
    web.add_argument(
        "--interval",
        type=interval_minutes,
        metavar="MINs",
        help="built-in sync interval; overrides config [内置同步间隔，优先于配置]",
    )
    web.add_argument("--open", action="store_true", help="open dashboard in browser [在浏览器中打开]")
    web.add_argument("--debug", action="store_true", help="enable debug logging [启用调试日志]")
    web.add_argument(
        "--log-level", dest="log_level", type=log_level, default="INFO", help="set dashboard log level [控制台日志级别]"
    )


def _add_task_subcommand_if_needed(parser):  # type: (ArgumentParser) -> None
    """
    Conditionally add subcommands to avoid Python 2 'too few arguments' error.

    Python 2's argparse requires subcommand when subparsers are defined, but Python 3 doesn't.
    We only add subparsers when the first argument is likely a subcommand (doesn't start with '-').
    """
    # Python2 Only add subparsers when first argument is a subcommand (not an option)
    if len(sys.argv) <= 1 or (sys.argv[1].startswith("-") and sys.argv[1] != "--help"):
        return

    subparsers = parser.add_subparsers(dest="command", help="subcommands [子命令]")
    _add_task_subcommand(subparsers)
    _add_web_subcommand(subparsers)


def _expand_web_interval_shorthand():
    # type: () -> None
    """Treat a top-level --interval option as an implicit web command."""
    if len(sys.argv) <= 1 or sys.argv[1] in ("task", "web"):
        return
    if any(argument == "--interval" or argument.startswith("--interval=") for argument in sys.argv[1:]):
        config_paths = _cli_config_paths(sys.argv[1:])
        if config_paths is not None and len(config_paths) != 1:
            _reject_multiple_web_configs()
        sys.argv.insert(1, "web")


def _cli_config_paths(arguments):
    # type: (list[str]) -> list[str] | None
    result = None
    index = 0
    while index < len(arguments):
        argument = arguments[index]
        if argument in ("-c", "--config"):
            if result is None:
                result = []
            index += 1
            while index < len(arguments) and not arguments[index].startswith("-"):
                result.append(arguments[index])
                index += 1
            continue
        if argument.startswith("--config="):
            if result is None:
                result = []
            result.append(argument.split("=", 1)[1])
        index += 1
    return result


def _reject_multiple_web_configs():
    # type: () -> None
    sys.stderr.write("ddns web: exactly one local configuration file is supported.\n")
    sys.exit(2)


def _default_local_config_path():
    # type: () -> str | None
    for candidate in DEFAULT_CONFIG_PATHS:
        candidate = os_path.expanduser(candidate)
        if os_path.isfile(candidate):
            return candidate
    return None


def _document_interval(config_path):
    # type: (str) -> tuple[bool, object | None]
    if not config_path or "://" in config_path or not os_path.isfile(config_path):
        return False, None
    document = load_file_config(config_path, raw=True)
    return (True, document.get("interval")) if isinstance(document, dict) and "interval" in document else (False, None)


def _configured_web_interval():
    # type: () -> tuple[str, object] | None
    cli_paths = _cli_config_paths(sys.argv[1:])
    config_path = None
    if cli_paths is not None:
        if len(cli_paths) != 1:
            if any(_document_interval(path)[0] for path in cli_paths):
                _reject_multiple_web_configs()
            return None
        config_path = cli_paths[0]
    else:
        config_path = load_env_config().get("config")
        if config_path:
            from .config import split_array_string

            config_paths = split_array_string(config_path, preserve_special=False)
            if len(config_paths) != 1:
                if any(_document_interval(path)[0] for path in config_paths):
                    _reject_multiple_web_configs()
                return None
            config_path = config_paths[0]
    if not config_path:
        config_path = _default_local_config_path()
    has_interval, interval = _document_interval(config_path)
    if not has_interval:
        return None
    return config_path, interval


def _validate_explicit_web_configs():
    # type: () -> None
    if len(sys.argv) <= 1 or sys.argv[1] != "web":
        return
    config_paths = _cli_config_paths(sys.argv[2:])
    if config_paths is not None and len(config_paths) != 1:
        _reject_multiple_web_configs()


def _validate_web_mode_arguments():
    # type: () -> None
    if len(sys.argv) <= 1 or sys.argv[1] != "web":
        return
    value_options = ("-c", "--config", "--host", "--port", "--interval", "--log-level")
    flag_options = ("--open", "--debug", "-h", "--help")
    long_value_prefixes = tuple(option + "=" for option in value_options if option.startswith("--"))
    arguments = sys.argv[2:]
    index = 0
    while index < len(arguments):
        argument = arguments[index]
        if argument in value_options:
            index += 2
            continue
        if argument in flag_options or argument.startswith(long_value_prefixes):
            index += 1
            continue
        sys.stderr.write(
            "ddns web: unsupported option {}; edit the local configuration file instead.\n".format(argument)
        )
        sys.exit(2)


def _expand_web_config_shorthand():
    # type: () -> None
    arguments = sys.argv[1:]
    if (
        (arguments and arguments[0] in ("task", "web"))
        or any(argument in ("-h", "--help", "-v", "--version", "--new-config") for argument in arguments)
        or any(argument.startswith("--new-config=") for argument in arguments)
    ):
        return
    configured = _configured_web_interval()
    if configured is None:
        return
    config_path, interval = configured
    try:
        interval = config_interval_minutes(interval)
    except ArgumentTypeError as error:
        sys.stderr.write("ddns web: interval {}\n".format(error))
        sys.exit(2)
    original_arguments = arguments
    prefix = ["web"] if _cli_config_paths(original_arguments) is not None else ["web", "--config", config_path]
    sys.argv[1:] = prefix + original_arguments + ["--interval", str(interval)]


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
    _expand_web_interval_shorthand()
    _expand_web_config_shorthand()
    _validate_explicit_web_configs()
    _validate_web_mode_arguments()
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
    parser.add_argument(
        "--interval",
        type=interval_minutes,
        metavar="MINs",
        help="run the local dashboard with built-in sync interval [按内置同步间隔运行本机控制台]",
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


def _handle_web_command(args):
    # type: (dict) -> None
    """Run the local-only embedded management dashboard."""
    basicConfig(level=args.get("debug") and DEBUG or args.get("log_level", "INFO"))
    config_path = args.get("config")
    if not config_path:
        config_path = load_env_config().get("config")
    if not config_path:
        config_path = _default_local_config_path()
    if config_path:
        from .config import split_array_string

        config_paths = split_array_string(config_path, preserve_special=False)
        if len(config_paths) != 1:
            sys.stderr.write("ddns web: exactly one local configuration file is supported.\n")
            sys.exit(2)
        config_path = config_paths[0]
        if "://" in config_path:
            sys.stderr.write("ddns web: remote configuration files are not supported.\n")
            sys.exit(2)

    interval = args.get("interval")
    interval_from_config = False
    if interval is None and config_path and os_path.isfile(config_path):
        document = load_file_config(config_path, raw=True)
        if isinstance(document, dict):
            interval = document.get("interval")
            interval_from_config = interval is not None
    if interval is None:
        interval = 5
    try:
        interval = config_interval_minutes(interval) if interval_from_config else interval_minutes(interval)
    except ArgumentTypeError as error:
        sys.stderr.write("ddns web: interval {}\n".format(error))
        sys.exit(2)

    from ..web import serve

    serve(
        config_path=config_path,
        host=args.get("host", "127.0.0.1"),
        port=args.get("port", 9876),
        open_browser=args.get("open", False),
        logger=getLogger(),
        interval=interval,
    )
