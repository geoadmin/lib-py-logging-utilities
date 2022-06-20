from datetime import datetime
import re
import json
import logging
import sys
import unittest
from collections import OrderedDict

from nose2.tools import params

from logging_utilities.filters import ConstAttribute
from logging_utilities.formatters.json_formatter import JsonFormatter

# From python3.7, dict is ordered
if sys.version_info >= (3, 7):
    dictionary = dict
else:
    dictionary = OrderedDict


class BasicJsonFormatterTest(unittest.TestCase):
    maxDiff = None

    @classmethod
    def _configure_logger(cls, logger, fmt=None, add_always_extra=False, style='%'):
        logger.setLevel(logging.DEBUG)

        for handler in logger.handlers:
            formatter = JsonFormatter(fmt, add_always_extra=add_always_extra, style=style)
            handler.setFormatter(formatter)

    @classmethod
    def _configure_logger_with_const_attribute(cls, logger, remove_empty=False):
        logger.setLevel(logging.DEBUG)

        for handler in logger.handlers:
            const_attribute = ConstAttribute(application="test_application", empty_attr='')
            handler.addFilter(const_attribute)
            formatter = JsonFormatter(
                dictionary([
                    ('level', 'levelname'),
                    ('app', 'application'),
                    ('empty_attr', 'empty_attr'),
                    ('message', 'message'),
                ]),
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
        message1 = json.loads(ctx.output[0], object_pairs_hook=dictionary)
        message2 = json.loads(ctx.output[1], object_pairs_hook=dictionary)
        message3 = json.loads(ctx.output[2], object_pairs_hook=dictionary)
        self.assertDictEqual(
            message1,
            dictionary([
                ("levelname", "INFO"),
                ("name", "test_formatter"),
                ("message", "Simple message"),
            ])
        )
        self.assertDictEqual(
            message2,
            dictionary([
                ("levelname", "INFO"),
                ("name", "test_formatter"),
                ("message", "Composed message: this is a composed message"),
            ])
        )
        self.assertDictEqual(
            message3,
            dictionary([
                ("levelname", "INFO"),
                ("name", "test_formatter"),
                ("message", "Composed message with extra"),
            ])
        )

    @params(
        (
            '%',
            dictionary([
                ('time', '%(asctime)s'),
                ('level', dictionary([('name', '%(levelname)s'), ('level', '%(levelno)d')])),
                ('pid_thid', '%(process)x/%(thread)x'),
                ('message', '%(message)s'),
            ])
        ),
        (
            '%',
            dictionary([
                ('time', 'asctime'),
                ('level', dictionary([('name', 'levelname'), ('level', '%(levelno)d')])),
                ('pid_thid', '%(process)x/%(thread)x'),
                ('message', 'message'),
            ])
        ),
        (
            '{',
            dictionary([
                ('time', '{asctime}'),
                ('level', dictionary([('name', '{levelname}'), ('level', '{levelno:d}')])),
                ('pid_thid', '{process:x}/{thread:x}'),
                ('message', '{message}'),
            ])
        ),
        (
            '$',
            dictionary([
                ('time', '${asctime}'),
                ('level', dictionary([('name', '${levelname}'), ('level', '${levelno}')])),
                ('pid_thid', '${process}/${thread}'),
                ('message', '${message}'),
            ])
        ),
    )
    def test_log_format_styles(self, style, fmt):
        with self.assertLogs('test_formatter', level=logging.DEBUG) as ctx:
            logger = logging.getLogger('test_formatter')
            self._configure_logger(logger, fmt=fmt, style=style)
            logger.info('Simple message')
            logger.info('Composed message: %s', 'this is a composed message')
            logger.info('Composed message %s', 'with extra', extra={'extra1': 23})
        messages = [
            json.loads(ctx.output[0], object_pairs_hook=dictionary),
            json.loads(ctx.output[1], object_pairs_hook=dictionary),
            json.loads(ctx.output[2], object_pairs_hook=dictionary)
        ]
        for message in messages:
            self.assertListEqual(list(message.keys()), ['time', 'level', 'pid_thid', 'message'])
            try:
                time_attr = datetime.strptime(message['time'], "%Y-%m-%d %X,%f")
            except ValueError as error:
                self.fail('Invalid time format in %s' % message['time'])
            self.assertAlmostEqual(time_attr.timestamp(), datetime.now().timestamp(), delta=10)
            self.assertListEqual(list(message['level'].keys()), ['name', 'level'])
            self.assertEqual(message['level']['level'], str(logging.INFO))
            self.assertIsNotNone(
                re.match(r'^[a-fA-F0-9]+/[a-fA-F0-9]+$', message['pid_thid']),
                msg='Invalid pid_thid value: %s' % message['pid_thid']
            )
        self.assertEqual(messages[0]['message'], "Simple message")
        self.assertEqual(messages[1]['message'], "Composed message: this is a composed message")
        self.assertEqual(messages[2]['message'], "Composed message with extra")

    def test_log_levelno(self):
        with self.assertLogs('test_formatter', level=logging.DEBUG) as ctx:
            logger = logging.getLogger('test_formatter')
            self._configure_logger(
                logger,
                fmt=dictionary([
                    ('levelno_int', 'levelno'),
                    ('levelno_str', '%(levelno)d'),
                    ('message', '%(message)s'),
                ])
            )
            logger.info('Simple message')
        message = json.loads(ctx.output[0], object_pairs_hook=dictionary)
        self.assertEqual(message['levelno_int'], logging.INFO)
        self.assertEqual(message['levelno_str'], str(logging.INFO))

    def test_embedded_object(self):
        with self.assertLogs('test_formatter', level=logging.DEBUG) as ctx:
            logger = logging.getLogger('test_formatter')
            self._configure_logger(
                logger,
                fmt=dictionary([
                    ('levelname', 'levelname'),
                    ('msg', 'message'),
                    (
                        'system',
                        dictionary([
                            ('context', dictionary([
                                ('module', 'module'),
                                ('file', 'filename'),
                            ]))
                        ])
                    ),
                ])
            )
            logger.info('Simple message')
            logger.info('Composed message: %s', 'this is a composed message')
            logger.info('Composed message %s', 'with extra', extra={'extra1': 23})
        message1 = json.loads(ctx.output[0], object_pairs_hook=dictionary)
        message2 = json.loads(ctx.output[1], object_pairs_hook=dictionary)
        message3 = json.loads(ctx.output[2], object_pairs_hook=dictionary)
        self.assertDictEqual(
            message1,
            dictionary([
                ("levelname", "INFO"),
                ("msg", "Simple message"),
                (
                    "system",
                    dictionary([(
                        "context",
                        dictionary([("module", "test_json_formatter"),
                                    ("file", "test_json_formatter.py")])
                    )])
                ),
            ])
        )
        self.assertDictEqual(
            message2,
            dictionary([
                ("levelname", "INFO"),
                ("msg", "Composed message: this is a composed message"),
                (
                    "system",
                    dictionary([(
                        "context",
                        dictionary([("module", "test_json_formatter"),
                                    ("file", "test_json_formatter.py")])
                    )])
                ),
            ])
        )
        self.assertDictEqual(
            message3,
            dictionary([
                ("levelname", "INFO"),
                ("msg", "Composed message with extra"),
                (
                    "system",
                    dictionary([(
                        "context",
                        dictionary([("module", "test_json_formatter"),
                                    ("file", "test_json_formatter.py")])
                    )])
                ),
            ])
        )

    def test_embedded_list(self):
        with self.assertLogs('test_formatter', level=logging.DEBUG) as ctx:
            logger = logging.getLogger('test_formatter')
            self._configure_logger(
                logger,
                fmt=dictionary([
                    ("levelname", "levelname"),
                    ("name", "name"),
                    ("message", "message"),
                    (
                        "list", [
                            dictionary([("file", "filename")]),
                            dictionary([("module", "module")]),
                        ]
                    ),
                ])
            )
            logger.info('Composed message %s', 'with list')
        message = json.loads(ctx.output[0], object_pairs_hook=dictionary)
        self.assertDictEqual(
            message,
            dictionary([
                ("levelname", "INFO"),
                ("name", "test_formatter"),
                ("message", "Composed message with list"),
                ('list', [{
                    "file": "test_json_formatter.py"
                }, {
                    "module": "test_json_formatter"
                }]),
            ])
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
        message = json.loads(ctx.output[0], object_pairs_hook=dictionary)
        self.assertDictEqual(
            message,
            dictionary([
                ("levelname", "INFO"),
                ("name", "test_formatter"),
                ("message", "Composed message with extra"),
                ('extra-list', [{
                    "extra-1": "file"
                }, {
                    "extra-2": "module"
                }]),
            ])
        )

    def test_exception(self):
        with self.assertLogs('test_formatter', level=logging.DEBUG) as ctx:
            logger = logging.getLogger('test_formatter')
            self._configure_logger(logger)
            try:
                raise ValueError("My value error")
            except ValueError as err:
                logger.exception('Exception message: %s', err)
        message = json.loads(ctx.output[0], object_pairs_hook=dictionary)
        expected_msg = dictionary([
            ("levelname", "ERROR"),
            ("name", "test_formatter"),
            ("message", "Exception message: My value error"),
            (
                "exc_text",
                'Traceback (most recent call last):\n'
                '    raise ValueError("My value error")\n'
                'ValueError: My value error'
            ),
        ])
        self.assertEqual(message.keys(), expected_msg.keys())
        self.assertEqual(message['levelname'], expected_msg['levelname'])
        self.assertEqual(message['name'], expected_msg['name'])
        self.assertEqual(message['message'], expected_msg['message'])
        self.assertEqual(message['exc_text'][:36], expected_msg['exc_text'][:36])
        self.assertEqual(message['exc_text'][-66:], expected_msg['exc_text'][-66:])

    def test_remove_empty(self):
        with self.assertLogs('test_formatter', level=logging.DEBUG) as ctx:
            logger = logging.getLogger('test_formatter')
            self._configure_logger_with_const_attribute(logger, remove_empty=True)
            logger.info('Composed message %s', 'remove empty')
        self.assertDictEqual(
            json.loads(ctx.output[0], object_pairs_hook=dictionary),
            dictionary([
                ("level", "INFO"),
                ("app", "test_application"),
                ("message", "Composed message remove empty"),
            ])
        )

    def test_leave_empty(self):
        with self.assertLogs('test_formatter', level=logging.DEBUG) as ctx:
            logger = logging.getLogger('test_formatter')
            self._configure_logger_with_const_attribute(logger, remove_empty=False)
            logger.info('Composed message %s', 'leave empty')
        self.assertDictEqual(
            json.loads(ctx.output[0], object_pairs_hook=dictionary),
            dictionary([
                ("level", "INFO"),
                ("app", "test_application"),
                ('empty_attr', ''),
                ("message", "Composed message leave empty"),
            ])
        )

    def test_non_serializable_extra(self):

        class TestObject:

            def __str__(self):
                return 'Test Object'

        with self.assertLogs('test_formatter', level=logging.DEBUG) as ctx:
            logger = logging.getLogger('test_formatter')
            self._configure_logger(logger, add_always_extra=True)
            logger.info(
                'Composed message %s',
                'with non serializable extra',
                extra=dictionary([('test-object', TestObject())])
            )
        self.assertDictEqual(
            json.loads(ctx.output[0], object_pairs_hook=dictionary),
            dictionary([
                ("levelname", "INFO"),
                ('name', 'test_formatter'),
                ("message", "Composed message with non serializable extra"),
                ('test-object', 'Test Object'),
            ])
        )
