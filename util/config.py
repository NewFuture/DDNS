#!/usr/bin/env python
# -*- coding:utf-8 -*-
from argparse import Action, ArgumentParser, Namespace, RawTextHelpFormatter
from json import load as loadjson, dump as dumpjson
from os import stat, environ, path
from logging import error, getLevelName
from ast import literal_eval

import sys


__cli_args = Namespace()
__config = {}  # type: dict
log_levels = ['CRITICAL', 'FATAL', 'ERROR',
              'WARN', 'WARNING', 'INFO', 'DEBUG', 'NOTSET']

# 支持数组的参数列表
ARRAY_PARAMS = ['index4', 'index6', 'ipv4', 'ipv6', 'proxy']
# 简单数组，支持’,’, ‘;’ 分隔的参数列表
SIMPLE_ARRAY_PARAMS = ['ipv4', 'ipv6', 'proxy']


def str2bool(v):
    """
    parse string to boolean
    """
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        return v


def log_level(value):
    """
    parse string to log level
    """
    return getLevelName(value.upper())


def parse_array_string(value, enable_simple_split):
    """
    解析数组字符串
    仅当 trim 之后以 '[' 开头以 ']' 结尾时，才尝试使用 ast.literal_eval 解析
    默认返回原始字符串
    """
    if not isinstance(value, str):
        return value

    trimmed = value.strip()
    if trimmed.startswith('[') and trimmed.endswith(']'):
        try:
            # 尝试使用 ast.literal_eval 解析数组
            parsed_value = literal_eval(trimmed)
            # 确保解析结果是列表或元组
            if isinstance(parsed_value, (list, tuple)):
                return list(parsed_value)
        except (ValueError, SyntaxError) as e:
            # 解析失败时返回原始字符串
            error('Failed to parse array string: %s. Exception: %s', value, e)
    elif enable_simple_split and ',' in trimmed:
        # 尝试使用逗号或分号分隔符解析
        return [item.strip() for item in trimmed.split(',') if item.strip()]
    return value


def init_config(description, doc, version):
    """
    配置
    """
    global __cli_args
    parser = ArgumentParser(description=description,
                            epilog=doc, formatter_class=RawTextHelpFormatter)
    parser.add_argument('-v', '--version',
                        action='version', version=version)
    parser.add_argument('-c', '--config', help='run with config file [配置文件路径]')

    # 参数定义
    parser.add_argument('--dns', help='DNS Provider [DNS服务提供商]', choices=[
                        'alidns', 'cloudflare', 'dnscom', 'dnspod', 'dnspod_com', 'he', 'huaweidns', 'callback'])
    parser.add_argument('--id', help='api ID [授权账户]')
    parser.add_argument('--token', help='api token or Secret key [授权访问凭证或密钥]')
    parser.add_argument('--index4', nargs='*', action=ExtendAction,
                        help='list to get ipv4 [IPV4 获取方式]')
    parser.add_argument('--index6', nargs='*', action=ExtendAction,
                        help='list to get ipv6 [IPV6获取方式]')
    parser.add_argument('--ipv4', nargs='*', action=ExtendAction,
                        help='ipv4 domain list [IPV4域名列表]')
    parser.add_argument('--ipv6', nargs='*', action=ExtendAction,
                        help='ipv6 domain list [IPV6域名列表]')
    parser.add_argument('--ttl', type=int, help='ttl for DNS [DNS 解析 TTL 时间]')
    parser.add_argument('--proxy', nargs='*', action=ExtendAction,
                        help='https proxy [设置http 代理，多代理逐个尝试直到成功]')
    parser.add_argument('--cache',  type=str2bool, nargs='?',
                        const=True, help='cache flag [启用缓存，可配配置路径或开关]')
    parser.add_argument('--log.file', metavar='LOG_FILE',
                        help='log file [日志文件，默认标准输出]')
    parser.add_argument('--log.level', type=log_level,
                        metavar='|'.join(log_levels))

    __cli_args = parser.parse_args()
    is_configfile_required = not get_config("token") and not get_config("id")
    config_file = get_config("config")
    if not config_file:
        # 未指定配置文件且需要读取文件时，依次查找
        cfgs = [
            path.abspath('config.json'),
            path.expanduser('~/.ddns/config.json'),
            '/etc/ddns/config.json'
        ]
        config_file = next((cfg for cfg in cfgs if path.isfile(cfg)), cfgs[0])

    if path.isfile(config_file):
        __load_config(config_file)
        __cli_args.config = config_file
    elif is_configfile_required:
        error('Config file is required, but not found: %s', config_file)
        # 如果需要配置文件但没有指定，则自动生成
        if generate_config(config_file):
            sys.stdout.write(
                'Default configure file %s is generated.\n' % config_file)
            sys.exit(1)
        else:
            sys.exit('fail to load config from file: %s\n' % config_file)


def __load_config(config_path):
    """
    加载配置
    """
    global __config
    try:
        with open(config_path, 'r') as configfile:
            __config = loadjson(configfile)
            __config["config_modified_time"] = stat(config_path).st_mtime
            if 'log' in __config:
                if 'level' in __config['log'] and __config['log']['level'] is not None:
                    __config['log.level'] = log_level(__config['log']['level'])
                if 'file' in __config['log']:
                    __config['log.file'] = __config['log']['file']
            elif 'log.level' in __config:
                __config['log.level'] = log_level(__config['log.level'])
    except Exception as e:
        error('Failed to load config file `%s`: %s', config_path, e)
        raise
        # 重新抛出异常


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
    # 检查环境变量
    env_name = 'DDNS_' + key.replace('.', '_')  # type:str
    variations = [env_name, env_name.upper(), env_name.lower()]
    value = next((environ.get(v) for v in variations if v in environ), None)

    # 如果找到环境变量值且参数支持数组，尝试解析为数组
    if value is not None and key in ARRAY_PARAMS:
        return parse_array_string(value, key in SIMPLE_ARRAY_PARAMS)

    return value if value is not None else default


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


def generate_config(config_path):
    """
    生成配置文件
    """
    configure = {
        '$schema': 'https://ddns.newfuture.cc/schema/v4.0.json',
        'id': 'YOUR ID or EMAIL for DNS Provider',
        'token': 'YOUR TOKEN or KEY for DNS Provider',
        'dns': 'dnspod',
        'ipv4': [
            'newfuture.cc',
            'ddns.newfuture.cc'
        ],
        'ipv6': [
            'newfuture.cc',
            'ipv6.ddns.newfuture.cc'
        ],
        'index4': 'default',
        'index6': 'default',
        'ttl': None,
        'proxy': None,
        'log': {
            'level': 'INFO',
            'file': None
        }
    }
    try:
        with open(config_path, 'w') as f:
            dumpjson(configure, f, indent=2, sort_keys=True)
            return True
    except IOError:
        error('Cannot open config file to write: `%s`!', config_path)
        return False
    except Exception as e:
        error('Failed to write config file `%s`: %s', config_path, e)
        return False
