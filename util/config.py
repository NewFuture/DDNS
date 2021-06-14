#!/usr/bin/env python
# -*- coding:utf-8 -*-
from argparse import ArgumentParser, ArgumentTypeError, Namespace, RawTextHelpFormatter
from json import load as loadjson, dump as dumpjson
from logging import error
from os import stat, environ
from time import time

import sys

__cli_args = {}  # type: Namespace
__config = {}  # type: dict


def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise ArgumentTypeError('Boolean value expected.')


def init_config(description, doc, version):
    global __cli_args
    """
    配置
    """
    parser = ArgumentParser(description=description,
                            epilog=doc, formatter_class=RawTextHelpFormatter)
    parser.add_argument('-v', '--version',
                        action='version', version=version)
    parser.add_argument('-c', '--config', help="run with config file [配置文件路径]")

    # 参数定义
    parser.add_argument('--dns', help="DNS Provider [DNS服务提供商]", choices=[
                        'alidns', 'cloudflare', 'dnscom', 'dnspod', 'dnspod_com', 'he', 'huaweidns', 'callback'])
    parser.add_argument('--id', help="api ID [授权账户]")
    parser.add_argument('--token', help="api token or Secret key [授权访问凭证或密钥]")
    parser.add_argument('--ipv4', nargs="*",
                        help="ipv4 domain list [IPV4域名列表]")
    parser.add_argument('--ipv6', nargs="*",
                        help="ipv6 domain list [IPV6域名列表]")
    parser.add_argument('--index4', help="the way to get ipv4 [IPV4 获取方式]")
    parser.add_argument('--index6', help="the way to get ipv6 [IPV6获取方式]")
    parser.add_argument('--ttl', type=int, help="ttl for DNS [DNS 解析 TTL 时间]")
    parser.add_argument('--proxy', nargs="*",
                        help="https proxy [设置http 代理，多代理逐个尝试直到成功]")
    parser.add_argument('--debug',  type=str2bool, nargs='?',
                        const=True, help="debug mode [是否开启调试,默认否]", )
    parser.add_argument('--cache',  type=str2bool, nargs='?',
                        const=True, help="eusing cache [是否缓存记录,默认是]")

    __cli_args = parser.parse_args()
    is_configfile_optional = get_config("token") or get_config("id")
    config_file = get_config("config")
    if not is_configfile_optional or config_file is not None:
        __load_config(config_file or "config.json", is_configfile_optional)
        __cli_args.config = config_file or "config.json"


def __load_config(path="config.json", skip_auto_generation=False):
    """
    加载配置
    """
    global __config, config_modified_time
    try:
        with open(path) as configfile:
            __config = loadjson(configfile)
            __config["config_modified_time"] = stat(path).st_mtime
    except IOError:
        if skip_auto_generation:
            __config["config_modified_time"] = time()
            return
        error(' Config file `%s` does not exist!' % path)
        with open(path, 'w') as configfile:
            configure = {
                "$schema": "https://ddns.newfuture.cc/schema/v2.8.json",
                "id": "YOUR ID or EMAIL for DNS Provider",
                "token": "YOUR TOKEN or KEY for DNS Provider",
                "dns": "dnspod",
                "ipv4": [
                    "newfuture.cc",
                    "ddns.newfuture.cc"
                ],
                "ipv6": [
                    "newfuture.cc",
                    "ipv6.ddns.newfuture.cc"
                ],
                "index4": "default",
                "index6": "default",
                "ttl": None,
                "proxy": None,
                "debug": False,
            }
            dumpjson(configure, configfile, indent=2, sort_keys=True)
            sys.stdout.write(
                "New template configure file `%s` is generated.\n" % path)
            sys.exit(1)
    except:
        sys.exit('fail to load config from file: %s' % path)


def get_config(key, default=None):
    """
    读取配置
    1. 命令行参数
    2. 配置文件
    3. 环境变量
    """
    if hasattr(__cli_args, key) and getattr(__cli_args, key) is not None:
        return getattr(__cli_args, key)
    if key in __config:
        return __config.get(key)
    env_name = 'DDNS_'+key.upper()  # type:str
    if env_name in environ:  # 大写环境变量
        return environ.get(env_name)
    if env_name.lower() in environ:  # 小写环境变量
        return environ.get(env_name.lower())
    return default
