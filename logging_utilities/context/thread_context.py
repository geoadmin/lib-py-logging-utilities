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
        self.ensure_data()

    def ensure_data(self):
        """Ensure the current thread has a `data` attribute in its local storage.

        The `threading.local()` object provides each thread with its own independent attribute
        namespace. Attributes created in one thread are not visible to other threads. This means
        that even if `data` was initialized in the thread where this object was constructed,
        new threads will not automatically have a `data` attribute since the constructor is not
        run again.

        Calling this method guarantees that `self.__local.data` exists in the *current* thread,
        creating an empty dictionary if needed. It must be invoked on every access path
        (e.g., __getitem__, __iter__).
        """
        if not hasattr(self.__local, 'data'):
            self.__local.data = {}

    def __str__(self):
        self.ensure_data()
        return str(self.__local.data)

    def __getitem__(self, __key):
        self.ensure_data()
        return self.__local.data[__key]

    def __setitem__(self, __key, __value):
        self.ensure_data()
        self.__local.data[__key] = __value

    def __delitem__(self, __key):
        self.ensure_data()
        del self.__local.data[__key]

    def __len__(self):
        self.ensure_data()
        return len(self.__local.data)

    def __iter__(self):
        self.ensure_data()
        return self.__local.data.__iter__()

    def __contains__(self, __o):
        self.ensure_data()
        return self.__local.data.__contains__(__o)

    def init(self, data=None):
        self.ensure_data()
        if data is None:
            self.__local.data = {}
        else:
            if not isinstance(data, Mapping):
                raise ValueError('Data must be a Mapping sequence')
            self.__local.data = data

    def get(self, key, default=None):
        self.ensure_data()
        return self.__local.data.get(key, default)

    def pop(self, key, default=__marker):
        self.ensure_data()
        if default == self.__marker:
            return self.__local.data.pop(key)
        return self.__local.data.pop(key, default)

    def set(self, key, value):
        self.ensure_data()
        self.__local.data[key] = value

    def delete(self, key):
        self.ensure_data()
        del self.__local.data[key]

    def clear(self):
        self.ensure_data()
        self.__local.data = {}
