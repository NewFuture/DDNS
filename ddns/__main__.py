# -*- coding:utf-8 -*-
"""
DDNS
@author: New Future
@modified: rufengsuixing
"""

from os import path, environ, name as os_name
from io import TextIOWrapper
from subprocess import check_output
from tempfile import gettempdir
from logging import basicConfig, info, warning, error, debug, INFO

import sys

from .__init__ import __version__, __description__, __doc__, build_date
from .util import ip
from .util.cache import Cache
from .util.config import init_config, get_config

environ["DDNS_VERSION"] = __version__


def is_false(value):
    """
    判断值是否为 False
    字符串 'false', 或者 False, 或者 'none';
    0 不是 False
    """
    if isinstance(value, str):
        return value.strip().lower() in ['false', 'none']
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
        elif index.startswith('cmd:'):  # cmd
            value = str(check_output(index[4:]).strip().decode('utf-8'))
        elif index.startswith('shell:'):  # shell
            value = str(check_output(
                index[6:], shell=True).strip().decode('utf-8'))
        elif index.startswith('url:'):  # 自定义 url
            value = getattr(ip, "public_v" + ip_type)(index[4:])
        elif index.startswith('regex:'):  # 正则 regex
            value = getattr(ip, "regex_v" + ip_type)(index[6:])
        else:
            value = getattr(ip, index + "_v" + ip_type)()
    except Exception as e:
        error("Failed to get %s address: %s", ip_type, e)
    return value


def change_dns_record(dns, proxy_list, **kw):
    for proxy in proxy_list:
        if not proxy or (proxy.upper() in ['DIRECT', 'NONE']):
            dns.Config.PROXY = None
        else:
            dns.Config.PROXY = proxy
        record_type, domain = kw['record_type'], kw['domain']
        info("%s(%s) ==> %s [via %s]", domain, record_type, kw['ip'], proxy)
        try:
            return dns.update_record(domain, kw['ip'], record_type=record_type)
        except Exception as e:
            error("Failed to update %s record for %s: %s", record_type, domain, e)
    return False


def update_ip(ip_type, cache, dns, proxy_list):
    """
    更新IP
    """
    ipname = 'ipv' + ip_type
    domains = get_config(ipname)
    if not domains:
        return None
    if not isinstance(domains, list):
        domains = domains.strip('; ').replace(',', ';').replace(' ', ';').split(';')

    index_rule = get_config('index' + ip_type, "default")
    address = get_ip(ip_type, index_rule)
    if not address:
        error('Fail to get %s address!', ipname)
        return False

    if cache and (address == cache.get(ipname)):
        info('%s address not changed, using cache.', ipname)
        return True

    record_type = 'A' if ip_type == '4' else 'AAAA'
    update_success = False
    for domain in domains:
        domain = domain.lower()
        if change_dns_record(dns, proxy_list, domain=domain, ip=address, record_type=record_type):
            update_success = True

    if isinstance(cache, dict):
        cache[ipname] = update_success and address

    return update_success


def main():
    """
    更新
    """
    encode = sys.stdout.encoding
    if encode is not None and encode.lower() != 'utf-8' and hasattr(sys.stdout, 'buffer'):
        # 兼容windows 和部分ASCII编码的老旧系统
        sys.stdout = TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    init_config(__description__, __doc__, __version__, build_date)

    log_level = get_config('log.level', INFO)
    log_format = get_config('log.format')
    if log_format:
        # A custom log format is already set; no further action is required.
        pass
    elif log_level < INFO:
        # Override log format in debug mode to include filename and line number for detailed debugging
        log_format = '%(asctime)s %(levelname)s [%(module)s.%(funcName)s](%(filename)s:%(lineno)d): %(message)s'
    elif log_level > INFO:
        log_format = '%(asctime)s %(levelname)s: %(message)s'
    else:
        log_format = '%(asctime)s %(levelname)s [%(module)s]: %(message)s'
    basicConfig(
        level=log_level,
        format=log_format,
        datefmt=get_config('log.datefmt', '%Y-%m-%dT%H:%M:%S'),
        filename=get_config('log.file'),
    )

    info("DDNS[ %s ] run: %s %s", __version__, os_name, sys.platform)

    # Dynamically import the dns module as configuration
    dns_provider = str(get_config('dns', 'dnspod').lower())
    # dns_module = __import__(
    #     '.dns', fromlist=[dns_provider], package=__package__)
    dns = getattr(__import__('ddns.provider', fromlist=[dns_provider]), dns_provider)
    # dns = getattr(dns_module, dns_provider)
    dns.Config.ID = get_config('id')
    dns.Config.TOKEN = get_config('token')
    dns.Config.TTL = get_config('ttl')

    if get_config("config"):
        info('loaded Config from: %s', path.abspath(get_config('config')))

    proxy = get_config('proxy') or 'DIRECT'
    proxy_list = proxy if isinstance(
        proxy, list) else proxy.strip(';').replace(',', ';').split(';')

    cache_config = get_config('cache', True)
    if cache_config is False:
        cache = cache_config
    elif cache_config is True:
        cache = Cache(path.join(gettempdir(), 'ddns.cache'))
    else:
        cache = Cache(cache_config)

    if cache is False:
        info('Cache is disabled!')
    elif not get_config('config_modified_time') or get_config('config_modified_time') >= cache.time:
        warning('Cache file is outdated.')
        cache.clear()
    else:
        debug('Cache is empty.')
    update_ip('4', cache, dns, proxy_list)
    update_ip('6', cache, dns, proxy_list)


if __name__ == '__main__':
    main()
