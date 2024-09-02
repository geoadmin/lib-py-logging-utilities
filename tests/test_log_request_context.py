import json
import logging
import sys
import time
import unittest
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor

from django.conf import settings
from django.test import RequestFactory

from logging_utilities.django_middlewares.add_request_context import \
    AddToThreadContextMiddleware
from logging_utilities.filters.add_thread_context_filter import \
    AddThreadContextFilter
from logging_utilities.filters.django_request import JsonDjangoRequest
from logging_utilities.formatters.json_formatter import JsonFormatter

# From python3.7, dict is ordered
if sys.version_info.major >= 3 and sys.version_info.minor >= 7:
    dictionary = dict
else:
    dictionary = OrderedDict

if not settings.configured:
    settings.configure()

logger = logging.getLogger(__name__)


class AddRequestToLogTest(unittest.TestCase):

    def setUp(self) -> None:
        self.factory = RequestFactory()

    @classmethod
    def _configure_django_filter(cls, _logger):
        for handler in _logger.handlers:
            handler.setFormatter(JsonFormatter(add_always_extra=True))
            handler.addFilter(
                AddThreadContextFilter(
                    contexts=[{
                        'logger_key': 'request', 'context_key': 'request'
                    }]
                )
            )
            handler.addFilter(
                JsonDjangoRequest(
                    include_keys=["request.path", "request.META.QUERY_STRING"], attr_name="request"
                )
            )

    def test_log_request_context(self):

        def test_handler(request):
            logger.info("some value")
            return "some response"

        with self.assertLogs(logger, level=logging.DEBUG) as ctx:
            # Global config of filter
            self._configure_django_filter(logger)
            request = self.factory.get("/some_path?test=some_value")
            middleware = AddToThreadContextMiddleware(test_handler)
            middleware(request)

        print(ctx.output[0])
        message1 = json.loads(ctx.output[0], object_pairs_hook=dictionary)
        self.assertDictEqual(
            message1,
            dictionary([
                ("levelname", "INFO"),
                ("name", "tests.test_log_request_context"),
                ("message", "some value"),
                (
                    "request",
                    dictionary([("path", "/some_path"),
                                ("META", dictionary([("QUERY_STRING", "test=some_value")]))])
                ),
            ])
        )


class MultiprocessLoggingTest(unittest.TestCase):

    def setUp(self) -> None:
        self.factory = RequestFactory()

    @classmethod
    def _configure_django_filter(cls, _logger):
        for handler in _logger.handlers:
            handler.setFormatter(JsonFormatter(add_always_extra=True))
            handler.addFilter(
                AddThreadContextFilter(
                    contexts=[{
                        'logger_key': 'request', 'context_key': 'request'
                    }]
                )
            )
            handler.addFilter(JsonDjangoRequest(include_keys=["request.path"], attr_name="request"))

    def test_threaded_logging(self):

        def test_handler(request):
            time.sleep(1)
            logger.info(request.path)
            return "some response"

        paths = [
            "/first_path",
            "/second_path",
            "/third_path",
        ]

        def execute_request(path):
            request = self.factory.get(path)
            middleware = AddToThreadContextMiddleware(test_handler)
            middleware(request)

        with self.assertLogs(logger, level=logging.DEBUG) as ctx:
            # Global config of filter
            self._configure_django_filter(logger)
            with ThreadPoolExecutor() as executor:
                futures = []
                for path in paths:
                    futures.append(executor.submit(execute_request, path))

        for output in ctx.output:
            msg = json.loads(output, object_pairs_hook=dictionary)
            self.assertEqual(msg["message"], msg["request"]["path"])
