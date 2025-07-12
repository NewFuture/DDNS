# -*- coding: utf-8 -*-
"""
cache module
文件缓存
"""

from logging import getLogger, Logger  # noqa: F401
from os import path, stat
from json import load, dump
from tempfile import gettempdir
from time import time


class Cache(dict):
    """
    using file to Cache data as dictionary
    """

    def __init__(self, path, logger=None, sync=False):
        # type: (str, Logger | None, bool) -> None
        super(Cache, self).__init__()
        self.__filename = path
        self.__sync = sync
        self.__time = time()
        self.__changed = False
        self.__logger = (logger or getLogger()).getChild("Cache")
        self.load()

    @property
    def time(self):
        """
        缓存修改时间
        """
        return self.__time or 0

    def load(self, file=None):
        """
        load data from path
        """
        if not file:
            file = self.__filename

        self.__logger.debug("load cache data from %s", file)
        if file:
            try:
                with open(file, "r") as data:
                    loaded_data = load(data)
                    self.clear()
                    self.update(loaded_data)
                    self.__time = stat(file).st_mtime
                    return self
            except (IOError, OSError):
                self.__logger.info("cache file not exist or cannot be opened")
            except ValueError:
                pass
            except Exception as e:
                self.__logger.warning(e)
        else:
            self.__logger.info("cache file not exist")

        self.clear()
        self.__time = time()
        self.__changed = True
        return self

    def sync(self):
        """Sync the write buffer with the cache files and clear the buffer."""
        if self.__changed and self.__filename:
            with open(self.__filename, "w") as data:
                # 只保存非私有字段（不以__开头的字段）
                filtered_data = {k: v for k, v in super(Cache, self).items() if not k.startswith("__")}
                dump(filtered_data, data, separators=(",", ":"))
                self.__logger.debug("save cache data to %s", self.__filename)
            self.__time = time()
            self.__changed = False
        return self

    def close(self):
        """Sync the write buffer, then close the cache.
        If a closed :class:`FileCache` object's methods are called, a
        :exc:`ValueError` will be raised.
        """
        if self.__filename:
            self.sync()
        self.__filename = None
        self.__time = None
        self.__sync = False

    def __update(self):
        self.__changed = True
        if self.__sync:
            self.sync()
        else:
            self.__time = time()

    def clear(self):
        # 只清除非私有字段（不以__开头的字段）
        keys_to_remove = [key for key in super(Cache, self).keys() if not key.startswith("__")]
        if keys_to_remove:
            for key in keys_to_remove:
                super(Cache, self).__delitem__(key)
            self.__update()

    def get(self, key, default=None):
        """
        获取指定键的值，如果键不存在则返回默认值
        :param key: 键
        :param default: 默认值
        :return: 键对应的值或默认值
        """
        if key is None and default is None:
            return {k: v for k, v in super(Cache, self).items() if not k.startswith("__")}
        return super(Cache, self).get(key, default)

    def __setitem__(self, key, value):
        if self.get(key) != value:
            super(Cache, self).__setitem__(key, value)
            # 私有字段（以__开头）不触发同步
            if not key.startswith("__"):
                self.__update()

    def __delitem__(self, key):
        # 检查键是否存在，如果不存在则直接返回，不抛错
        if not super(Cache, self).__contains__(key):
            return
        super(Cache, self).__delitem__(key)
        # 私有字段（以__开头）不触发同步
        if not key.startswith("__"):
            self.__update()

    def __getitem__(self, key):
        return super(Cache, self).__getitem__(key)

    def __iter__(self):
        # 只迭代非私有字段（不以__开头的字段）
        for key in super(Cache, self).__iter__():
            if not key.startswith("__"):
                yield key

    def __items__(self):
        # 只返回非私有字段（不以__开头的字段）
        return ((key, value) for key, value in super(Cache, self).items() if not key.startswith("__"))

    def __len__(self):
        # 不计算以__开头的私有字段
        return len([key for key in super(Cache, self).keys() if not key.startswith("__")])

    def __contains__(self, key):
        return super(Cache, self).__contains__(key)

    def __str__(self):
        return super(Cache, self).__str__()

    def __del__(self):
        self.close()

    @staticmethod
    def new(config_cache, hash, logger):
        # type: (str|bool, str, Logger) -> Cache|None
        """
        new cache from a file path.
        :param path: Path to the cache file.
        :param logger: Optional logger for debug messages.
        :return: Cache instance with loaded data.
        """
        if config_cache is False:
            cache = None
        elif config_cache is True:
            cache_path = path.join(gettempdir(), "ddns.%s.cache" % hash)
            cache = Cache(cache_path, logger)
        else:
            cache = Cache(config_cache, logger)

        if cache is None:
            logger.debug("Cache is disabled!")
        elif cache.time + 72 * 3600 < time():  # 72小时有效期
            logger.info("Cache file is outdated.")
            cache.clear()
        elif len(cache) == 0:
            logger.debug("Cache is empty.")
        else:
            logger.debug("Cache loaded with %d entries.", len(cache))
        return cache
