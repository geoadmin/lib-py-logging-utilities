import threading
from collections.abc import Mapping

from .base import BaseContext


class ThreadMappingContext(BaseContext):
    '''Thread local mapping contex

    This class implements all Mapping (e.g. dictionary) functionality but on a
    thread local context.
    '''
    __marker = object()

    def __init__(self):
        self.__local = threading.local()
        self.__local.data = {}

    def __str__(self):
        return str(self.__local.data)

    def __getitem__(self, __key):
        return self.__local.data[__key]

    def __setitem__(self, __key, __value):
        self.__local.data[__key] = __value

    def __delitem__(self, __key):
        del self.__local.data[__key]

    def __len__(self):
        return len(self.__local.data)

    def __iter__(self):
        return self.__local.data.__iter__()

    def __contains__(self, __o):
        return self.__local.data.__contains__(__o)

    def init(self, data=None):
        if data is None:
            self.__local.data = {}
        else:
            if not isinstance(data, Mapping):
                raise ValueError('Data must be a Mapping sequence')
            self.__local.data = data

    def get(self, key, default=None):
        return self.__local.data.get(key, default)

    def pop(self, key, default=__marker):
        if default == self.__marker:
            return self.__local.data.pop(key)
        return self.__local.data.pop(key, default)

    def set(self, key, value):
        self.__local.data[key] = value

    def delete(self, key):
        del self.__local.data[key]

    def clear(self):
        self.__local.data = {}
