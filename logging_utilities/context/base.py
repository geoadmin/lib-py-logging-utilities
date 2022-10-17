from abc import abstractmethod
from collections.abc import MutableMapping


class BaseContext(MutableMapping):
    __marker = object()

    @abstractmethod
    def init(self, data):
        pass  # pragma: no cover

    @abstractmethod
    def get(self, key, default=None):
        pass  # pragma: no cover

    @abstractmethod
    def pop(self, key, default=__marker):
        pass  # pragma: no cover

    @abstractmethod
    def set(self, key, value):
        pass  # pragma: no cover

    @abstractmethod
    def delete(self, key: str):
        pass  # pragma: no cover

    @abstractmethod
    def clear(self):
        pass  # pragma: no cover
