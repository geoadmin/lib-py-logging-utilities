import json
import logging
import sys
import unittest
from collections import OrderedDict

from logging_utilities.formatters.json_formatter import JsonFormatter
from logging_utilities.filters import ConstAttribute

# From python3.7, dict is ordered
if sys.version_info >= (3, 7):
    dictionary = dict
else:
    dictionary = OrderedDict


class BasicJsonFormatterTest(unittest.TestCase):
    maxDiff = None

    @classmethod
    def _configure_logger(cls, logger, fmt=None, add_always_extra=False):
        logger.setLevel(logging.DEBUG)

        for handler in logger.handlers:
            formatter = JsonFormatter(fmt, add_always_extra=add_always_extra)
            handler.setFormatter(formatter)

    @classmethod
    def _configure_logger_with_const_attribute(cls, logger, remove_empty=False):
        logger.setLevel(logging.DEBUG)

        for handler in logger.handlers:
            const_attribute = ConstAttribute(application="test_application", empty_attr='')
            handler.addFilter(const_attribute)
            formatter = JsonFormatter(
                dictionary(
                    [
                        ('level', 'levelname'), ('app', 'application'),
                        ('empty_attr', 'empty_attr'), ('message', 'message')
                    ]
                ),
                remove_empty=remove_empty,
                filter_attributes=['application', 'empty_attr']
            )
            handler.setFormatter(formatter)

    def test_simple_log(self):
        with self.assertLogs('test_formatter', level=logging.DEBUG) as ctx:
            logger = logging.getLogger('test_formatter')
            self._configure_logger(logger)
            logger.info('Simple message')
            logger.info('Composed message: %s', 'this is a composed message')
            logger.info('Composed message %s', 'with extra', extra={'extra1': 23})
        self.assertEqual(
            ctx.output,
            [
                json.dumps(
                    {
                        "levelname": "INFO", "name": "test_formatter", "message": "Simple message"
                    }
                ),
                json.dumps(
                    {
                        "levelname": "INFO",
                        "name": "test_formatter",
                        "message": "Composed message: this is a composed message"
                    }
                ),
                json.dumps(
                    {
                        "levelname": "INFO",
                        "name": "test_formatter",
                        "message": "Composed message with extra"
                    }
                )
            ]
        )

    def test_embedded_object(self):
        with self.assertLogs('test_formatter', level=logging.DEBUG) as ctx:
            logger = logging.getLogger('test_formatter')
            self._configure_logger(
                logger,
                fmt=dictionary(
                    [
                        ('levelname', 'levelname'), ('msg', 'message'),
                        ('system', {
                            'context': {
                                'module': 'module', 'file': 'filename'
                            }
                        })
                    ]
                )
            )
            logger.info('Simple message')
            logger.info('Composed message: %s', 'this is a composed message')
            logger.info('Composed message %s', 'with extra', extra={'extra1': 23})
        self.assertEqual(
            ctx.output,
            [
                json.dumps(
                    {
                        "levelname": "INFO",
                        "msg": "Simple message",
                        "system":
                            {
                                "context": {
                                    "module": "test_formatter", "file": "test_formatter.py"
                                }
                            }
                    }
                ),
                json.dumps(
                    {
                        "levelname": "INFO",
                        "msg": "Composed message: this is a composed message",
                        "system":
                            {
                                "context": {
                                    "module": "test_formatter", "file": "test_formatter.py"
                                }
                            }
                    }
                ),
                json.dumps(
                    {
                        "levelname": "INFO",
                        "msg": "Composed message with extra",
                        "system":
                            {
                                "context": {
                                    "module": "test_formatter", "file": "test_formatter.py"
                                }
                            }
                    }
                )
            ]
        )

    def test_embedded_list(self):
        with self.assertLogs('test_formatter', level=logging.DEBUG) as ctx:
            logger = logging.getLogger('test_formatter')
            self._configure_logger(
                logger,
                fmt=OrderedDict(
                    [
                        ("levelname", "levelname"), ("name", "name"), ("message", "message"),
                        (
                            "list",
                            [
                                OrderedDict([("file", "filename")]),
                                OrderedDict([("module", "module")])
                            ]
                        )
                    ]
                )
            )
            logger.info('Composed message %s', 'with list')
        self.assertEqual(
            ctx.output,
            [
                json.dumps(
                    {
                        "levelname": "INFO",
                        "name": "test_formatter",
                        "message": "Composed message with list",
                        'list': [{
                            "file": "test_formatter.py"
                        }, {
                            "module": "test_formatter"
                        }]
                    }
                )
            ]
        )

    def test_extra_list(self):
        with self.assertLogs('test_formatter', level=logging.DEBUG) as ctx:
            logger = logging.getLogger('test_formatter')
            self._configure_logger(logger, add_always_extra=True)
            logger.info(
                'Composed message %s',
                'with extra',
                extra={'extra-list': [{
                    "extra-1": "file"
                }, {
                    "extra-2": "module"
                }]}
            )
        self.assertEqual(
            ctx.output,
            [
                json.dumps(
                    {
                        "levelname": "INFO",
                        "name": "test_formatter",
                        "message": "Composed message with extra",
                        'extra-list': [{
                            "extra-1": "file"
                        }, {
                            "extra-2": "module"
                        }]
                    }
                )
            ]
        )

    def test_exception(self):
        with self.assertLogs('test_formatter', level=logging.DEBUG) as ctx:
            logger = logging.getLogger('test_formatter')
            self._configure_logger(logger)
            try:
                raise ValueError("My value error")
            except ValueError as err:
                logger.exception('Exception message: %s', err)
        self.assertDictEqual(
            json.loads(ctx.output[0], object_pairs_hook=dictionary),
            dictionary(
                [
                    ("levelname", "ERROR"),
                    ("name", "test_formatter"),
                    ("message", "Exception message: My value error"),
                    (
                        "exc_text",
                        'Traceback (most recent call last):\n'
                        # pylint: disable=line-too-long
                        '  File "/home/ltshb/repo-lib/lib-py-log-json-formatter/tests/test_formatter.py", '
                        'line 213, in test_exception\n'
                        '    raise ValueError("My value error")\n'
                        'ValueError: My value error'
                    )
                ]
            )
        )

    def test_remove_empty(self):
        with self.assertLogs('test_formatter', level=logging.DEBUG) as ctx:
            logger = logging.getLogger('test_formatter')
            self._configure_logger_with_const_attribute(logger, remove_empty=True)
            logger.info('Composed message %s', 'remove empty')
        self.assertDictEqual(
            json.loads(ctx.output[0], object_pairs_hook=dictionary),
            dictionary(
                [
                    ("level", "INFO"), ("app", "test_application"),
                    ("message", "Composed message remove empty")
                ]
            )
        )

    def test_leave_empty(self):
        with self.assertLogs('test_formatter', level=logging.DEBUG) as ctx:
            logger = logging.getLogger('test_formatter')
            self._configure_logger_with_const_attribute(logger, remove_empty=False)
            logger.info('Composed message %s', 'leave empty')
        self.assertDictEqual(
            json.loads(ctx.output[0], object_pairs_hook=dictionary),
            dictionary(
                [
                    ("level", "INFO"), ("app", "test_application"), ('empty_attr', ''),
                    ("message", "Composed message leave empty")
                ]
            )
        )
