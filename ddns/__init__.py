# -*- coding:utf-8 -*-
"""
ddns Package
"""

__description__ = "automatically update DNS records to my IP [域名自动指向本机IP]"

# 编译时，版本会被替换
__version__ = "${BUILD_VERSION}"

# 时间也会被替换掉
build_date = "${BUILD_DATE}"

__doc__ = """
ddns[%s]
(i) homepage or docs [文档主页]: https://ddns.newfuture.cc/
(?) issues or bugs [问题和帮助]: https://github.com/NewFuture/DDNS/issues
Copyright (c) New Future (MIT License)
""" % (
    __version__
)
