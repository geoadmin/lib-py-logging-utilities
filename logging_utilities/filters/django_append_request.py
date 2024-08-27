import functools
from logging import LogRecord
from typing import Optional

from django.core.handlers.wsgi import WSGIRequest


def request_getattr(obj, attr, *args):

    def _getattr(obj, attr):
        if isinstance(obj, dict):
            return obj.get(attr)
        return getattr(obj, attr, *args)

    return functools.reduce(_getattr, [obj] + attr.split('.'))


class DjangoAppendRequestFilter():
    """Logging Django request attributes

    This filter adds Django request context attributes to the log record.
    """

    def __init__(self, request: Optional[WSGIRequest] = None, attributes=None, always_add=False):
        """Initialize the filter

        Args:
            request: (WSGIRequest | None)
                Request from which to read the attributes from.
            attributes: (list | None)
                Request attributes that should be added to log entries.
            always_add: bool
                Always add attributes even if they are missing. Missing attributes with have the
                value "-".
        """
        self.request = request
        self.attributes = attributes if attributes else list()
        self.always_add = always_add

    def filter(self, record: LogRecord) -> bool:
        request = self.request
        for attr in self.attributes:
            val = request_getattr(request, attr, "-")
            if self.always_add or val != "-":
                setattr(record, "request." + attr, val)

        return True
