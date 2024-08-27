import logging
from typing import Any
from typing import Callable
from typing import Optional
from typing import Type
from typing import TypeVar

from django.core.handlers.wsgi import WSGIRequest

from logging_utilities.filters.django_append_request import \
    DjangoAppendRequestFilter

# Create a generic variable that can be 'WrappedRequest', or any subclass.
T = TypeVar('T', bound='WrappedRequest')


class WrappedRequest(WSGIRequest):
    """WrappedRequest adds the 'logging_filter' field to a standard request to track it.
    """

    @classmethod
    def from_parent(
        cls: Type[T], parent: WSGIRequest, logging_filter: Optional[DjangoAppendRequestFilter]
    ) -> T:
        return cls(parent.environ, logging_filter)

    def __init__(self, environ: Any, logging_filter: Optional[DjangoAppendRequestFilter]) -> None:
        super().__init__(environ)
        self.logging_filter = logging_filter


class AddRequestToLogMiddleware():
    """Middleware that adds a logging filter *DjangoAppendRequestFilter* to the request.
    """

    def __init__(self, get_response: Callable[[WSGIRequest], Any], root_logger: str = ""):
        self.root_logger = root_logger
        self.get_response = get_response

    def __call__(self, request: WSGIRequest) -> Any:
        w_request = WrappedRequest.from_parent(request, None)
        response = self.process_request(w_request)
        if not response:
            response = self.get_response(w_request)
        response = self.process_response(w_request, response)

        return response

    def _find_loggers(self) -> dict[str, logging.Logger]:
        """Return loggers part of root.
        """
        result: dict[str, logging.Logger] = {}
        prefix = self.root_logger + "."
        for name, log in logging.Logger.manager.loggerDict.items():
            if not isinstance(log, logging.Logger) or not name.startswith(prefix):
                continue  # not under self.root_logger
            result[name] = log
        # also add root logger
        result[self.root_logger] = logging.getLogger(self.root_logger)
        return result

    def _find_handlers(self) -> list[logging.Handler]:
        """List handlers of all loggers
        """
        handlers = set()
        for logger in self._find_loggers().values():
            for handler in logger.handlers:
                handlers.add(handler)
        return list(handlers)

    def _find_handlers_with_filter(self, filter_cls: type) -> dict[logging.Handler, list[Any]]:
        """Dict of handlers mapped to their filters.
        Only include handlers that have at least one filter of type *filter_cls*.
        """
        result = {}
        for handler in self._find_handlers():
            attrs = []
            for f in handler.filters:
                if isinstance(f, filter_cls):
                    attrs.extend(f.attributes)
            if attrs:
                result[handler] = attrs
        return result

    def _add_filter(self, f: DjangoAppendRequestFilter) -> None:
        """Add the filter to relevant handlers.
        Relevant handlers are once that already include a filter of the same type.
        This is how we "overrite" the filter with the current request.
        """
        filter_cls = type(f)
        for handler, attrs in self._find_handlers_with_filter(filter_cls).items():
            f.attributes = attrs
            handler.addFilter(f)

    def process_request(self, request: WrappedRequest) -> Any:
        """Add a filter that includes the current request. Add the filter to the request to be
        removed again later.
        """
        request.logging_filter = DjangoAppendRequestFilter(request)
        self._add_filter(request.logging_filter)
        return self.get_response(request)

    def _remove_filter(self, f: DjangoAppendRequestFilter) -> None:
        """Remove the filter from any handlers that may have it.
        """
        filter_cls = type(f)
        for handler in self._find_handlers_with_filter(filter_cls):
            handler.removeFilter(f)

    def process_response(self, request: WrappedRequest, response: Any) -> Any:
        """Remove the filter if set.
        """
        if request.logging_filter:
            self._remove_filter(request.logging_filter)
        return response
