# -*- coding:utf-8 -*-
"""
DDNS
@author: NewFuture, rufengsuixing
"""

from os import path, name as os_name
from io import TextIOWrapper
from subprocess import check_output
from tempfile import gettempdir
from logging import basicConfig, getLogger, INFO
from time import time
import sys

from .__init__ import __version__, __description__, build_date
from .config import load_config, Config  # noqa: F401
from .provider import get_provider_class, SimpleProvider
from .util import ip
from .util.cache import Cache

logger = getLogger()
# Set user agent for All Providers
SimpleProvider.user_agent = SimpleProvider.user_agent.format(version=__version__)


def get_ip(ip_type, index):
    """
    get IP address
    """
    if index is False:  # disabled
        return False
    for i in index:
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
                return getattr(ip, index + "_v" + ip_type)()
        except Exception as e:
            logger.error("Failed to get %s address: %s", ip_type, e)
    return None


def change_dns_record(dns, **kw):
    # type: (SimpleProvider,  **(Any)) -> bool
    record_type, domain = kw["record_type"], kw["domain"]
    try:
        return dns.set_record(domain, kw["ip"], record_type=record_type, ttl=kw["ttl"], line=kw.get("line"))
    except Exception as e:
        logger.exception("Failed to update %s record for %s: %s", record_type, domain, e)
    return False


def update_ip(dns, cache, index_rule, domains, record_type, config):
    # type: (SimpleProvider, Cache | None, list[str]|bool, list[str], str, Config) -> bool | None
    """
    更新IP
    """
    # ipname = "ipv" + ip_type
    if not domains:
        return None

    # index_rule = getattr(config, "index" + ip_type, "default")  # type: str # type: ignore
    ip_type = "4" if record_type == "A" else "6"
    address = get_ip(ip_type, index_rule)
    if not address:
        logger.error("Fail to get %s address!", ip_type)
        return False

    update_success = False

    # Check cache and update each domain individually
    for domain in domains:
        domain = domain.lower()
        cache_key = "{}:{}".format(domain, record_type)
        if cache and cache.get(cache_key) == address:
            logger.info("%s[%s] address not changed, using cache: %s", domain, record_type, address)
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

    # dns provider class
    provider_class = get_provider_class(config.dns)
    dns = provider_class(
        config.id, config.token, endpoint=config.endpoint, logger=logger, proxy=config.proxy, verify_ssl=config.ssl
    )

    if config.cache is False:
        cache = None
    elif config.cache is True:
        cache_path = path.join(gettempdir(), "ddns.%s.cache" % config.md5())
        cache = Cache(cache_path, logger)
    else:
        cache = Cache(config.cache, logger)

    if cache is None:
        logger.info("Cache is disabled!")
    elif cache.time > time():  # type: ignore
        logger.info("Cache file is outdated.")
        cache.clear()
    elif len(cache) == 0:
        logger.debug("Cache is empty.")
    else:
        logger.debug("Cache loaded with %d entries.", len(cache))

    update_ip(dns, cache, config.index4, config.ipv4, "A", config)
    update_ip(dns, cache, config.index6, config.ipv6, "AAAA", config)


if __name__ == "__main__":
    logger.name = "ddns"
    main()
