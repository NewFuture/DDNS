# -*- coding: utf-8 -*-
"""
cache module
文件缓存
"""


from os import path, stat
from pickle import dump, load
from time import time

from logging import info, debug, error

try:
    from collections.abc import MutableMapping
except ImportError:
    # Python 2 imports
    from collections import MutableMapping


class Cache(MutableMapping):
    """
    using file to Cache data as dictionary
    """

    def __init__(self, path, sync=False):
        self.__data = {}
        self.__filename = path
        self.__sync = sync
        self.__time = time()
        self.__changed = False
        self.load()

    @property
    def time(self):
        """
        缓存修改时间
        """
        return self.__time

    def load(self, file=None):
        """
        load data from path
        """
        if not file:
            file = self.__filename

        debug('load cache data from %s', file)
        if path.isfile(file):
            with open(self.__filename, 'rb') as data:
                try:
                    self.__data = load(data)
                    self.__time = stat(file).st_mtime
                except ValueError:
                    self.__data = {}
                    self.__time = time()
                except Exception as e:
                    error(e)
                    self.__data = {}
                    self.__time = time()
        else:
            info('cache file not exist')
            self.__data = {}
            self.__time = time()
        return self

    def data(self, key=None, default=None):
        """
        获取当前字典或者制定得键值
        """
        if self.__sync:
            self.load()

        if key is None:
            return self.__data
        else:
            return self.__data.get(key, default)

    def sync(self):
        """Sync the write buffer with the cache files and clear the buffer.
        """
        if self.__changed:
            with open(self.__filename, 'wb') as data:
                dump(self.__data, data)
                debug('save cache data to %s', self.__filename)
            self.__time = time()
            self.__changed = False
        return self

    def close(self):
        """Sync the write buffer, then close the cache.
        If a closed :class:`FileCache` object's methods are called, a
        :exc:`ValueError` will be raised.
        """
        self.sync()
        del self.__data
        del self.__filename
        del self.__time
        self.__sync = False

    def __update(self):
        self.__changed = True
        if self.__sync:
            self.sync()
        else:
            self.__time = time()

    def clear(self):
        if self.data():
            self.__data = {}
            self.__update()

    def __setitem__(self, key, value):
        if self.data(key) != value:
            self.__data[key] = value
            self.__update()

    def __delitem__(self, key):
        if key in self.data():
            del self.__data[key]
            self.__update()

    def __getitem__(self, key):
        return self.data(key)

    def __iter__(self):
        for key in self.data():
            yield key

    def __len__(self):
        return len(self.data())

    def __contains__(self, key):
        return key in self.data()

    def __str__(self):
        return self.data().__str__()

    def __del__(self):
        self.close()
