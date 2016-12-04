# -*- coding: utf-8 -*-
r"""
cache module
文件缓存
"""

import logging as LOG
import os
import pickle
import time

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
        self.__changed = False
        self.load()

    @property
    def time(self):
        """
        缓存修改时间
        """
        return self.__time

    def load(self, path=None):
        """
        load data from path
        """
        if not path:
            path = self.__filename

        LOG.debug('load cache data from %s', path)
        if os.path.isfile(path):
            with open(self.__filename, 'r') as data:
                self.__data = pickle.load(data)
            self.__time = os.stat(path).st_mtime
        else:
            LOG.info('cache file not exist')
            self.__data = {}
            self.__time = time.time()
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
            with open(self.__filename, 'w') as data:
                pickle.dump(self.__data, data)
                LOG.debug('save cache data to %s', self.__filename)
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

    def __setitem__(self, key, value):
        if self.data(key) != value:
            self.__data[key] = value
            self.__changed = True
            if self.__sync:
                self.sync()

    def __delitem__(self, key):
        if key in self.data():
            del self.__data[key]
            self.__changed = True
            if self.__sync:
                self.sync()

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


def main():
    """
    test
    """
    LOG.basicConfig(level=LOG.DEBUG)
    # LOG.debug('test log')
    cache = Cache('test.txt')
    cache['s'] = ['a', 's']
    print cache
    print cache['s']
    print cache.time
    cache['t'] = '哈哈'
    print cache.time


if __name__ == '__main__':
    main()
