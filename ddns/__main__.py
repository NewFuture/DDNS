# -*- coding:utf-8 -*-
"""
DDNS
@author: NewFuture, rufengsuixing
"""

import sys
from io import TextIOWrapper
from logging import getLogger
from subprocess import check_output

from . import ip
from .__init__ import __description__, __version__, build_date
from .cache import Cache
from .config import Config, load_configs  # noqa: F401
from .provider import SimpleProvider, get_provider_class  # noqa: F401

logger = getLogger()


def _get_cache_verify_every(config):
    # type: (Config) -> int
    """Return the configured cache verification interval in cache-hit counts."""
    value = getattr(config, "cache_verify_every", 0) or 0
    return value if value > 0 else 0


def _get_cache_verify_counter_key(config, domain, record_type):
    # type: (Config, str, str) -> str
    """Build the persisted counter key for a provider-specific DNS record."""
    return "{}:{}:{}".format(config.dns, domain, record_type)


def _get_cache_verify_count(cache, counter_key):
    # type: (Cache | None, str) -> int
    """Get the persisted cache-hit skip counter for a record."""
    if isinstance(cache, Cache):
        return cache.get_cache_verify_count(counter_key)
    return 0


def _set_cache_verify_count(cache, counter_key, count):
    # type: (Cache | None, str, int) -> None
    """Persist the cache-hit skip counter for a record."""
    if isinstance(cache, Cache):
        cache.set_cache_verify_count(counter_key, count)


def _clear_cache_verify_count(cache, counter_key):
    # type: (Cache | None, str) -> None
    """Clear the cache-hit skip counter for a record."""
    if isinstance(cache, Cache):
        cache.del_cache_verify_count(counter_key)
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
    verify_every = _get_cache_verify_every(config)

    for domain in domains:
        domain = domain.lower()
        cache_key = "{}:{}".format(domain, record_type)
        counter_key = _get_cache_verify_counter_key(config, domain, record_type)
        force_verify = False
        if cache and cache.get(cache_key) == address:
            verify_count = _get_cache_verify_count(cache, counter_key)
            if verify_every and verify_count >= verify_every:
                force_verify = True
                logger.info(
                    "%s[%s] address unchanged after %d cached skips, verifying upstream: %s",
                    domain,
                    record_type,
                    verify_count,
                    address,
                )
            else:
                if verify_every:
                    verify_count += 1
                    _set_cache_verify_count(cache, counter_key, verify_count)
                    logger.info(
                        "%s[%s] address not changed, using cache (%d/%d): %s",
                        domain,
                        record_type,
                        verify_count,
                        verify_every,
                        address,
                    )
                else:
                    logger.info("%s[%s] address not changed, using cache: %s", domain, record_type, address)
                update_success = True
                continue

        try:
            result = dns.set_record(
                domain, address, record_type=record_type, ttl=config.ttl, line=config.line, **config.extra
            )
            if result:
                logger.warning("set %s[IPv%s]: %s successfully.", domain, ip_type, address)
                update_success = True
                if isinstance(cache, dict):
                    cache[cache_key] = address
                _clear_cache_verify_count(cache, counter_key)
            else:
                if force_verify:
                    _set_cache_verify_count(cache, counter_key, verify_every)
                logger.error("Failed to update %s record for %s", record_type, domain)
        except Exception as e:
            if force_verify:
                _set_cache_verify_count(cache, counter_key, verify_every)
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


def main():
    stdout = sys.stdout  # pythonw 模式无 stdout
    if stdout and stdout.encoding and stdout.encoding.lower() != "utf-8" and hasattr(stdout, "buffer"):
        # 兼容windows 和部分ASCII编码的老旧系统
        sys.stdout = TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        sys.stderr = TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

    # Windows 下输出一个空行
    if stdout and sys.platform.startswith("win"):
        stdout.write("\r\n")

    logger.name = "ddns"

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
