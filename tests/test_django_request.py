import json
import logging
import sys
import unittest
from collections import OrderedDict

from django.conf import settings
from django.test import RequestFactory

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


class DjangoAppendRequestFilterTest(unittest.TestCase):

    def setUp(self) -> None:
        self.factory = RequestFactory()

    @classmethod
    def _configure_django_filter(cls, _logger, django_filter):
        _logger.setLevel(logging.DEBUG)
        for handler in _logger.handlers:
            handler.setFormatter(JsonFormatter(add_always_extra=True))
            handler.addFilter(django_filter)

    def test_django_request_log(self):
        request = self.factory.get("/some_path?test=some_value")
        with self.assertLogs('test_formatter', level=logging.DEBUG) as ctx:
            test_logger = logging.getLogger("test_formatter")
            self._configure_django_filter(
                test_logger,
                DjangoAppendRequestFilter(
                    request, request_attributes=["path", "method", "META.QUERY_STRING"]
                )
            )

            test_logger.debug("first message")
            test_logger.info("second message")

        message1 = json.loads(ctx.output[0], object_pairs_hook=dictionary)
        self.assertDictEqual(
            message1,
            dictionary([("levelname", "DEBUG"), ("name", "test_formatter"),
                        ("message", "first message"), ("request.method", "GET"),
                        ("request.path", "/some_path"),
                        ("request.META.QUERY_STRING", "test=some_value")])
        )
        message2 = json.loads(ctx.output[1], object_pairs_hook=dictionary)
        self.assertDictEqual(
            message2,
            dictionary([("levelname", "INFO"), ("name", "test_formatter"),
                        ("message", "second message"), ("request.method", "GET"),
                        ("request.path", "/some_path"),
                        ("request.META.QUERY_STRING", "test=some_value")])
        )

    def test_django_request_log_always_add(self):
        request = self.factory.get("/some_path?test=some_value")
        with self.assertLogs('test_formatter', level=logging.DEBUG) as ctx:
            test_logger = logging.getLogger("test_formatter")
            self._configure_django_filter(
                test_logger,
                DjangoAppendRequestFilter(
                    request, request_attributes=["does", "not", "exist"], always_add=True
                )
            )

            test_logger.debug("first message")
            test_logger.info("second message")

        message1 = json.loads(ctx.output[0], object_pairs_hook=dictionary)
        self.assertDictEqual(
            message1,
            dictionary([("levelname", "DEBUG"), ("name", "test_formatter"),
                        ("message", "first message"), ("request.does", "-"), ("request.not", "-"),
                        ("request.exist", "-")])
        )
        message2 = json.loads(ctx.output[1], object_pairs_hook=dictionary)
        self.assertDictEqual(
            message2,
            dictionary([("levelname", "INFO"), ("name", "test_formatter"),
                        ("message", "second message"), ("request.does", "-"), ("request.not", "-"),
                        ("request.exist", "-")])
        )
