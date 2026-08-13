import json
import logging
import sys
import unittest
from collections import OrderedDict

from flask import Flask

from logging_utilities.filters.flask_attribute import FlaskRequestAttribute
from logging_utilities.formatters.json_formatter import JsonFormatter

# From python3.7, dict is ordered
if sys.version_info.major >= 3 and sys.version_info.minor >= 7:
    dictionary = dict
else:
    dictionary = OrderedDict

app = Flask(__name__)


class FlaskJsonFormatterTest(unittest.TestCase):

    @classmethod
    def _configure_logger(
        cls,
        logger,
        fmt=None,
        add_always_extra=False,
        remove_empty=False,
        ignore_missing=False,
        flask_attributes=None,
        style='%'
    ):
        logger.setLevel(logging.DEBUG)

        for handler in logger.handlers:
            formatter = JsonFormatter(
                fmt,
                add_always_extra=add_always_extra,
                remove_empty=remove_empty,
                ignore_missing=ignore_missing,
                style=style
            )
            handler.setFormatter(formatter)
            flask_attribute = FlaskRequestAttribute(attributes=flask_attributes)
            handler.addFilter(flask_attribute)

    def test_json_formatter_flask_no_context(self):

        with self.assertLogs('test_formatter', level=logging.DEBUG) as ctx:
            logger = logging.getLogger('test_formatter')
            self._configure_logger(
                logger,
                fmt=dictionary([
                    ('level', 'levelname'),
                    (
                        'request',
                        dictionary([
                            ('path', '%(flask_request_path)s'),
                            ('headers', dictionary([('Accept', 'flask_request_headers.Accept')]))
                        ])
                    ),
                    ('message', 'message'),
                ]),
                remove_empty=True,
                ignore_missing=True,
                flask_attributes=['path', 'headers']
            )
            logger.info('Simple message')

        self.assertDictEqual(
            json.loads(ctx.output[0], object_pairs_hook=dictionary),
            dictionary([
                ("level", "INFO"),
                ("message", "Simple message"),
            ])
        )

    def test_json_formatter_flask(self):

        with self.assertLogs('test_formatter', level=logging.DEBUG) as ctx:
            logger = logging.getLogger('test_formatter')
            self._configure_logger(
                logger,
                fmt=dictionary([
                    ('level', 'levelname'),
                    (
                        'request',
                        dictionary([
                            ('path', '%(flask_request_path)s'),
                            ('headers', dictionary([('Accept', 'flask_request_headers.Accept')]))
                        ]),
                    ),
                    ('message', 'message'),
                ]),
                remove_empty=False,
                ignore_missing=True,
                flask_attributes=['path', 'headers']
            )

            with app.test_request_context('/make_report/2017'):
                logger.info('Simple message')

            with app.test_request_context('/make_report/2017', headers={'Accept': '*/*'}):
                logger.info('Simple message with headers')

        self.assertDictEqual(
            json.loads(ctx.output[0], object_pairs_hook=dictionary),
            dictionary([
                ("level", "INFO"),
                ("message", "Simple message"),
                (
                    "request",
                    dictionary([("path", "/make_report/2017"),
                                ("headers", dictionary([("Accept", "")]))])
                ),
            ])
        )

        self.assertDictEqual(
            json.loads(ctx.output[1], object_pairs_hook=dictionary),
            dictionary([
                ("level", "INFO"),
                ("message", "Simple message with headers"),
                (
                    "request",
                    dictionary([("path", "/make_report/2017"),
                                ("headers", dictionary([("Accept", "*/*")]))])
                ),
            ])
        )

    def test_json_formatter_flask_remove_empty(self):

        with self.assertLogs('test_formatter', level=logging.DEBUG) as ctx:
            logger = logging.getLogger('test_formatter')
            self._configure_logger(
                logger,
                fmt=dictionary([
                    ('level', 'levelname'),
                    (
                        'request',
                        dictionary([
                            ('path', '%(flask_request_path)s'),
                            ('headers', dictionary([('Accept', 'flask_request_headers.Accept')]))
                        ]),
                    ),
                    ('message', 'message'),
                ]),
                remove_empty=True,
                ignore_missing=True,
                flask_attributes=['path', 'headers']
            )

            with app.test_request_context('/make_report/2017'):
                logger.info('Simple message')

            with app.test_request_context('/make_report/2017', headers={'Accept': '*/*'}):
                logger.info('Simple message with headers')

        self.assertDictEqual(
            json.loads(ctx.output[0], object_pairs_hook=dictionary),
            dictionary([
                ("level", "INFO"),
                ("message", "Simple message"),
                ("request", dictionary([("path", "/make_report/2017")])),
            ])
        )

        self.assertDictEqual(
            json.loads(ctx.output[1], object_pairs_hook=dictionary),
            dictionary([
                ("level", "INFO"),
                ("message", "Simple message with headers"),
                (
                    "request",
                    dictionary([("path", "/make_report/2017"),
                                ("headers", dictionary([("Accept", "*/*")]))])
                ),
            ])
        )
