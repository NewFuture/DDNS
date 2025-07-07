# -*- coding:utf-8 -*-
"""
DDNS
@author: NewFuture, rufengsuixing
"""

from os import path, name as os_name
from io import TextIOWrapper
from subprocess import check_output
from tempfile import gettempdir
from logging import basicConfig, getLogger, info, error, debug, warning, INFO
from time import time
import sys

from .__init__ import __version__, __description__, build_date
from .config import load_config, Config  # noqa: F401
from .provider import get_provider_class, SimpleProvider
from .util import ip
from .util.cache import Cache

logger = getLogger()
logger.name = "ddns"
# Set user agent for All Providers
SimpleProvider.user_agent = SimpleProvider.user_agent.format(version=__version__)


def is_false(value):
    """
    判断值是否为 False
    字符串 'false', 或者 False, 或者 'none';
    0 不是 False
    """
    if hasattr(value, "strip"):  # 字符串
        return value.strip().lower() in ["false", "none"]
    return value is False


def get_ip(ip_type, index="default"):
    """
    get IP address
    """
    # CN: 捕获异常
    # EN: Catch exceptions
    value = None
    try:
        debug("get_ip(%s, %s)", ip_type, index)
        if is_false(index):  # disabled
            return False
        elif isinstance(index, list):  # 如果获取到的规则是列表，则依次判断列表中每一个规则，直到获取到IP
            for i in index:
                value = get_ip(ip_type, i)
                if value:
                    break
        elif str(index).isdigit():  # 数字 local eth
            value = getattr(ip, "local_v" + ip_type)(index)
        elif index.startswith("cmd:"):  # cmd
            value = str(check_output(index[4:]).strip().decode("utf-8"))
        elif index.startswith("shell:"):  # shell
            value = str(check_output(index[6:], shell=True).strip().decode("utf-8"))
        elif index.startswith("url:"):  # 自定义 url
            value = getattr(ip, "public_v" + ip_type)(index[4:])
        elif index.startswith("regex:"):  # 正则 regex
            value = getattr(ip, "regex_v" + ip_type)(index[6:])
        else:
            value = getattr(ip, index + "_v" + ip_type)()
    except Exception as e:
        error("Failed to get %s address: %s", ip_type, e)
    return value


def change_dns_record(dns, **kw):
    # type: (SimpleProvider,  **(Any)) -> bool
    record_type, domain = kw["record_type"], kw["domain"]
    try:
        return dns.set_record(domain, kw["ip"], record_type=record_type, ttl=kw["ttl"], line=kw.get("line"))
    except Exception as e:
        logger.exception("Failed to update %s record for %s: %s", record_type, domain, e)
    return False


def update_ip(ip_type, dns, config, cache):
    # type: (str, SimpleProvider, Config, Cache | None) -> bool | None
    """
    更新IP
    """
    ipname = "ipv" + ip_type
    domains = getattr(config, ipname, None)  # type: list[str] | str | None
    if not domains:
        return None
    if not isinstance(domains, list):
        domains = domains.strip("; ").replace(",", ";").replace(" ", ";").split(";")

    index_rule = getattr(config, "index" + ip_type, "default")  # type: str # type: ignore
    address = get_ip(ip_type, index_rule)
    if not address:
        error("Fail to get %s address!", ipname)
        return False

    record_type = "A" if ip_type == "4" else "AAAA"
    update_success = False

    # Check cache and update each domain individually
    for domain in domains:
        domain = domain.lower()
        cache_key = "{}:{}".format(domain, record_type)
        if cache and cache.get(cache_key) == address:
            info("%s[%s] address not changed, using cache: %s", domain, record_type, address)
            update_success = True  # At least one domain is successfully cached
        else:
            # Update domain that is not cached or has different IP
            if change_dns_record(
                dns, domain=domain, ip=address, record_type=record_type, ttl=config.ttl, line=config.line
            ):
                warning("set %s[IPv%s]: %s successfully.", domain, ip_type, address)
                update_success = True
                # Cache successful update immediately
                if isinstance(cache, dict):
                    cache[cache_key] = address

    return update_success


def main():
    encode = sys.stdout.encoding
    if encode is not None and encode.lower() != "utf-8" and hasattr(sys.stdout, "buffer"):
        # 兼容windows 和部分ASCII编码的老旧系统
        sys.stdout = TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        sys.stderr = TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

    config = load_config(__description__, __version__, build_date)
    log_format = config.log_format  # type: str  # type: ignore
    if log_format:
        # A custom log format is already set; no further action is required.
        pass
    elif config.log_level < INFO:
        # Override log format in debug mode to include filename and line number for detailed debugging
        log_format = "%(asctime)s %(levelname)s [%(name)s.%(funcName)s](%(filename)s:%(lineno)d): %(message)s"
    elif config.log_level > INFO:
        log_format = "%(asctime)s %(levelname)s: %(message)s"
    else:
        log_format = "%(asctime)s %(levelname)s [%(name)s]: %(message)s"
    basicConfig(level=config.log_level, format=log_format, datefmt=config.log_datefmt, filename=config.log_file)

    debug("DDNS[ %s ] run: %s %s", __version__, os_name, sys.platform)

    # dns provider class
    provider_class = get_provider_class(config.dns)
    dns = provider_class(
        config.id, config.token, version=__version__, logger=logger, proxy=config.proxy, verify_ssl=config.ssl
    )

    if config.cache is False:
        cache = None
    elif config.cache is True:
        cache_path = path.join(gettempdir(), "ddns.{}.cache".format(hash(config)))
        cache = Cache(cache_path, logger)
    else:
        cache = Cache(config.cache, logger)

    if cache is None:
        info("Cache is disabled!")
    elif cache.time > time():  # type: ignore
        info("Cache file is outdated.")
        cache.clear()
    elif len(cache) == 0:
        debug("Cache is empty.")
    else:
        debug("Cache loaded with %d entries.", len(cache))

    update_ip("4", dns, config, cache)
    update_ip("6", dns, config, cache)


if __name__ == "__main__":
    main()
