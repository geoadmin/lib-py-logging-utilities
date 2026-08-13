import json
import logging
import sys
import unittest
from collections import OrderedDict

from django.conf import settings
from django.test import RequestFactory

from logging_utilities.filters.add_thread_context_filter import \
    AddThreadContextFilter
from logging_utilities.formatters.json_formatter import JsonFormatter
from logging_utilities.thread_context import thread_context

if not settings.configured:
    settings.configure()

# From python3.7, dict is ordered
if sys.version_info.major >= 3 and sys.version_info.minor >= 7:
    dictionary = dict
else:
    dictionary = OrderedDict

logger = logging.getLogger(__name__)


class AddThreadContextFilterTest(unittest.TestCase):

    def setUp(self) -> None:
        self.factory = RequestFactory()

    @classmethod
    def _configure_json_filter(cls, _logger):
        _logger.setLevel(logging.DEBUG)
        for handler in _logger.handlers:
            handler.setFormatter(JsonFormatter(add_always_extra=True))

    def test_add_thread_context_no_request(self):
        with self.assertLogs('test_logger', level=logging.DEBUG) as ctx:
            test_logger = logging.getLogger("test_logger")
            self._configure_json_filter(test_logger)
            test_logger.addFilter(
                AddThreadContextFilter(
                    contexts=[{
                        'logger_key': 'http_request', 'context_key': 'request'
                    }]
                )
            )
            test_logger.debug("some message")

        message1 = json.loads(ctx.output[0], object_pairs_hook=dictionary)
        self.assertDictEqual(
            message1,
            dictionary([("levelname", "DEBUG"), ("name", "test_logger"),
                        ("message", "some message")])
        )

    def test_add_thread_context(self):
        test_cases = [
            {
                'logger_name': 'test_1',
                'var_key': 'request',
                'var_val': "some value",
                'attr_name': 'http_request',
                'expect_value': "some value",
                'log_message': 'a log message has appeared',
            },
            {
                'logger_name': 'test_2',
                'var_key': 'request',
                'var_val': self.factory.get("/some_path"),
                'attr_name': 'request',
                'expect_value': "<WSGIRequest: GET '/some_path'>",
                'log_message': 'another log message has appeared',
            },
        ]

        for tc in test_cases:
            with self.assertLogs(tc['logger_name'], level=logging.DEBUG) as ctx:
                test_logger = logging.getLogger(tc['logger_name'])
                setattr(thread_context, tc['var_key'], tc['var_val'])
                self._configure_json_filter(test_logger)
                test_logger.addFilter(
                    AddThreadContextFilter(
                        contexts=[{
                            'logger_key': tc['attr_name'], 'context_key': tc['var_key']
                        }]
                    )
                )

                test_logger.debug(tc['log_message'])
                setattr(thread_context, tc['var_key'], None)

            message1 = json.loads(ctx.output[0], object_pairs_hook=dictionary)
            self.assertDictEqual(
                message1,
                dictionary([("levelname", "DEBUG"), ("name", tc['logger_name']),
                            ("message", tc['log_message']), (tc['attr_name'], tc['expect_value'])])
            )
