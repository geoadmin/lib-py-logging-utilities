import json
import logging
import sys
import unittest
from collections import OrderedDict

from django.conf import settings
from django.test import RequestFactory

from logging_utilities.django_middlewares.request_middleware import \
    AddRequestToLogMiddleware
from logging_utilities.filters.django_append_request import \
    DjangoAppendRequestFilter
from logging_utilities.formatters.json_formatter import JsonFormatter

# From python3.7, dict is ordered
if sys.version_info.major >= 3 and sys.version_info.minor >= 7:
    dictionary = dict
else:
    dictionary = OrderedDict

if not settings.configured:
    settings.configure()

logger = logging.getLogger(__name__)


class AddRequestToLogMiddlewareTest(unittest.TestCase):

    def setUp(self) -> None:
        self.factory = RequestFactory()

    @classmethod
    def _configure_django_filter(cls, _logger):
        for handler in _logger.handlers:
            handler.setFormatter(JsonFormatter(add_always_extra=True))
            django_filter = DjangoAppendRequestFilter(
                attributes=["method", "path", "META.QUERY_STRING", "headers"]
            )
            handler.addFilter(django_filter)

    def test_request_log(self):

        def test_handler(request):
            logger.info("test message")
            return "some response"

        with self.assertLogs(logger, level=logging.DEBUG) as ctx:
            self._configure_django_filter(logger)
            my_header = {"HTTP_CUSTOM_KEY": "VALUE"}
            request = self.factory.get("/some_path?test=some_value", **my_header)
            middleware = AddRequestToLogMiddleware(test_handler, root_logger="tests")
            middleware(request)

        message1 = json.loads(ctx.output[0], object_pairs_hook=dictionary)
        print(message1)
        self.assertDictEqual(
            message1,
            dictionary([("levelname", "INFO"), ("name", __name__), ("message", "test message"),
                        ("request.method", "GET"), ("request.path", "/some_path"),
                        ("request.META.QUERY_STRING", "test=some_value"),
                        ('request.headers', "{'Cookie': '', 'Custom-Key': 'VALUE'}")])
        )
