# -*- coding:utf-8 -*-
"""
DDNS
@author: NewFuture, rufengsuixing
"""

from os import path, environ, name as os_name
from io import TextIOWrapper
from subprocess import check_output
from tempfile import gettempdir
from logging import basicConfig, getLogger, info, error, debug, warning, INFO

import sys

from .__init__ import __version__, __description__, __doc__, build_date
from .util import ip
from .util.cache import Cache
from .util.config import init_config, get_config
from .provider import get_provider_class, SimpleProvider  # noqa: F401

environ["DDNS_VERSION"] = __version__


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


def change_dns_record(dns, proxy_list, **kw):
    # type: (SimpleProvider, list, **(str)) -> bool
    for proxy in proxy_list:
        if not proxy or (proxy.upper() in ["DIRECT", "NONE"]):
            dns.set_proxy(None)
        else:
            dns.set_proxy(proxy)
        record_type, domain = kw["record_type"], kw["domain"]
        try:
            return dns.set_record(domain, kw["ip"], record_type=record_type, ttl=kw["ttl"], line=kw.get("line"))
        except Exception as e:
            error("Failed to update %s record for %s: %s", record_type, domain, e)
    return False


def update_ip(ip_type, cache, dns, ttl, line, proxy_list):
    # type: (str, Cache | None, SimpleProvider, str, str | None, list[str]) -> bool | None
    """
    更新IP
    """
    ipname = "ipv" + ip_type
    domains = get_config(ipname)
    if not domains:
        return None
    if not isinstance(domains, list):
        domains = domains.strip("; ").replace(",", ";").replace(" ", ";").split(";")

    index_rule = get_config("index" + ip_type, "default")  # type: str # type: ignore
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
            if change_dns_record(dns, proxy_list, domain=domain, ip=address, record_type=record_type, ttl=ttl, line=line):
                warning("set %s[IPv%s]: %s successfully.", domain, ip_type, address)
                update_success = True
                # Cache successful update immediately
                if isinstance(cache, dict):
                    cache[cache_key] = address

    return update_success


def main():
    """
    更新
    """
    encode = sys.stdout.encoding
    if encode is not None and encode.lower() != "utf-8" and hasattr(sys.stdout, "buffer"):
        # 兼容windows 和部分ASCII编码的老旧系统
        sys.stdout = TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        sys.stderr = TextIOWrapper(sys.stderr.buffer, encoding="utf-8")
    init_config(__description__, __doc__, __version__, build_date)

    log_level = get_config("log.level", INFO)  # type: int # type: ignore
    log_format = get_config("log.format")  # type: str | None # type: ignore
    if log_format:
        # A custom log format is already set; no further action is required.
        pass
    elif log_level < INFO:
        # Override log format in debug mode to include filename and line number for detailed debugging
        log_format = "%(asctime)s %(levelname)s [%(name)s.%(funcName)s](%(filename)s:%(lineno)d): %(message)s"
    elif log_level > INFO:
        log_format = "%(asctime)s %(levelname)s: %(message)s"
    else:
        log_format = "%(asctime)s %(levelname)s [%(name)s]: %(message)s"
    basicConfig(
        level=log_level,
        format=log_format,
        datefmt=get_config("log.datefmt", "%Y-%m-%dT%H:%M:%S"),  # type: ignore
        filename=get_config("log.file"),  # type: ignore
    )
    logger = getLogger()
    logger.name = "ddns"

    debug("DDNS[ %s ] run: %s %s", __version__, os_name, sys.platform)

    # dns provider class
    dns_name = get_config("dns", "debug")  # type: str # type: ignore
    provider_class = get_provider_class(dns_name)
    ssl_config = get_config("ssl", "auto")  # type: str | bool # type: ignore
    dns = provider_class(get_config("id"), get_config("token"), logger=logger, verify_ssl=ssl_config)  # type: ignore

    if get_config("config"):
        info("loaded Config from: %s", path.abspath(get_config("config")))  # type: ignore

    proxy = get_config("proxy") or "DIRECT"
    proxy_list = proxy if isinstance(proxy, list) else proxy.strip(";").replace(",", ";").split(";")

    cache_config = get_config("cache", True)  # type: bool | str  # type: ignore
    if cache_config is False:
        cache = None
    elif cache_config is True:
        cache = Cache(path.join(gettempdir(), "ddns.cache"), logger)
    else:
        cache = Cache(cache_config, logger)

    if cache is None:
        info("Cache is disabled!")
    elif get_config("config_modified_time", float("inf")) >= cache.time:  # type: ignore
        info("Cache file is outdated.")
        cache.clear()
    elif len(cache) == 0:
        debug("Cache is empty.")
    else:
        debug("Cache loaded with %d entries.", len(cache))
    ttl = get_config("ttl")  # type: str # type: ignore
    line = get_config("line")  # type: str | None # type: ignore
    update_ip("4", cache, dns, ttl, line, proxy_list)
    update_ip("6", cache, dns, ttl, line, proxy_list)


if __name__ == "__main__":
    main()
