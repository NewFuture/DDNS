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
from .config import load_config, Config  # noqa: F401
from .provider import get_provider_class, SimpleProvider
from . import ip
from .cache import Cache

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
        config.id, config.token, endpoint=config.endpoint, logger=logger, proxy=config.proxy, verify_ssl=config.ssl
    )
    cache = Cache.new(config.cache, config.md5(), logger)
    return (
        update_ip(dns, cache, config.index4, config.ipv4, "A", config) is not False
        and update_ip(dns, cache, config.index6, config.ipv6, "AAAA", config) is not False
    )


def main():
    encode = sys.stdout.encoding
    if encode is not None and encode.lower() != "utf-8" and hasattr(sys.stdout, "buffer"):
        # 兼容windows 和部分ASCII编码的老旧系统
        sys.stdout = TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        sys.stderr = TextIOWrapper(sys.stderr.buffer, encoding="utf-8")
    logger.name = "ddns"
    config = load_config(__description__, __version__, build_date)
    run(config)


if __name__ == "__main__":
    main()
