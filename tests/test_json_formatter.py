import json
import logging
import re
import sys
import unittest
from collections import OrderedDict
from datetime import datetime

from nose2.tools import params

from logging_utilities.filters import ConstAttribute
from logging_utilities.formatters.json_formatter import JsonFormatter

# From python3.7, dict is ordered
if sys.version_info.major >= 3 and sys.version_info.minor >= 7:
    dictionary = dict
else:
    dictionary = OrderedDict


class BasicJsonFormatterTest(unittest.TestCase):
    maxDiff = None

    @classmethod
    def _configure_logger(
        cls,
        logger,
        fmt=None,
        add_always_extra=False,
        remove_empty=False,
        ignore_missing=False,
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

    def test_string_fmt_param(self):
        with self.assertLogs('test_formatter', level=logging.DEBUG) as ctx:
            logger = logging.getLogger('test_formatter')
            self._configure_logger(logger, '{"level": "levelname", "message": "message"}')
            logger.info('Simple message')

        message = json.loads(ctx.output[0], object_pairs_hook=dictionary)
        self.assertDictEqual(
            message, dictionary([
                ("level", "INFO"),
                ("message", "Simple message"),
            ])
        )

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

    if sys.version_info.major >= 3 and sys.version_info.minor >= 8:
        # Python version prior to 3.8 do not raise any exception on non existing attribute
        @params(
            'non.existing', '%(non_existing)s', '%(non.existing)s', '%(non.existing)s with text'
        )
        def test_missing_attribute_raise(self, attribute):
            with self.assertLogs('test_formatter', level=logging.DEBUG) as ctx:
                logger = logging.getLogger('test_formatter')
                self._configure_logger(
                    logger,
                    dictionary([
                        ('level', 'levelname'),
                        ('non-existing', attribute),
                        ('message', 'message'),
                    ]),
                )
                with self.assertRaises((ValueError, KeyError)):
                    logger.info('Simple message')
            self.assertListEqual(ctx.output, [])

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

    def test_list_embedded_object(self):
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

    def test_list_embedded_list(self):
        with self.assertLogs('test_formatter', level=logging.DEBUG) as ctx:
            logger = logging.getLogger('test_formatter')
            self._configure_logger(
                logger,
                fmt=dictionary([
                    ("levelname", "levelname"),
                    ("name", "name"),
                    ("message", "message"),
                    ("list", [["filename", "module"], ["levelname", "levelno"]]),
                ])
            )
            logger.info('Composed message %s', 'with embedded list')
        message = json.loads(ctx.output[0], object_pairs_hook=dictionary)
        self.assertDictEqual(
            message,
            dictionary([
                ("levelname", "INFO"),
                ("name", "test_formatter"),
                ("message", "Composed message with embedded list"),
                (
                    'list', [["test_json_formatter.py", "test_json_formatter"],
                             ["INFO", logging.INFO]]
                ),
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

    def test_stack_info(self):
        with self.assertLogs('test_formatter', level=logging.DEBUG) as ctx:
            logger = logging.getLogger('test_formatter')
            self._configure_logger(
                logger,
                fmt=dictionary([
                    ('levelname', 'levelname'),
                    ('name', 'name'),
                    ('message', 'message'),
                ])
            )
            logger.info('Message with stack info', stack_info=True)
        message = json.loads(ctx.output[0], object_pairs_hook=dictionary)
        self.assertListEqual(list(message.keys()), ['levelname', 'name', 'message', 'stack_info'])
        self.assertEqual(message['levelname'], 'INFO')
        self.assertEqual(message['name'], 'test_formatter')
        self.assertEqual(message['message'], 'Message with stack info')
        self.assertTrue(
            message['stack_info'].startswith('Stack (most recent call last):\n'),
            msg='stack_info do not start with "Stack (most recent call last):\\n"'
        )

    def test_exception(self):
        with self.assertLogs('test_formatter', level=logging.DEBUG) as ctx:
            logger = logging.getLogger('test_formatter')
            self._configure_logger(
                logger,
                fmt=dictionary([
                    ('levelname', 'levelname'),
                    ('name', 'name'),
                    ('message', 'message'),
                    (
                        'exception_dict',
                        dictionary([("exc_info", "exc_info"), ("exc_text", "exc_text")])
                    ),
                    ('exception_list', ["exc_info", "exc_info"]),
                    ("exc_info", "exc_info"),
                    ("exc_text", "exc_text"),
                ])
            )
            try:
                raise ValueError("My value error")
            except ValueError as err:
                logger.exception('Exception message: %s', err)
        message = json.loads(ctx.output[0], object_pairs_hook=dictionary)
        exc_text = 'Traceback (most recent call last):\n' + \
                   '    raise ValueError("My value error")\n' + \
                   'ValueError: My value error'
        expected_msg = dictionary([
            ("levelname", "ERROR"),
            ("name", "test_formatter"),
            ("message", "Exception message: My value error"),
            ("exception_dict", dictionary([("exc_info", True), ("exc_text", exc_text)])),
            ("exception_list", [True, exc_text]),
            ("exc_info", True),
            ("exc_text", exc_text),
        ])
        self.assertListEqual(list(message.keys()), list(expected_msg.keys()))
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

    def test_remove_non_existing(self):
        with self.assertLogs('test_formatter', level=logging.DEBUG) as ctx:
            logger = logging.getLogger('test_formatter')
            self._configure_logger(
                logger,
                fmt=dictionary([
                    ("level", "levelname"),
                    ("message", "message"),
                    ("non-existing-attribute", "%(nonExistingAttribute)s"),
                    ("2nd-non-existing-attribute", "non_existing.dotted.attribute"),
                    ("3rd-non-existing-attribute", 'some_var'),
                    (
                        "3rd-non-existing-attribute",
                        'Some random text, 1.2 float. Should not be added.'
                    ),
                ]),
                remove_empty=True,
                ignore_missing=True
            )
            logger.info('Composed message %s', 'remove non existing attribute')
        self.assertDictEqual(
            json.loads(ctx.output[0], object_pairs_hook=dictionary),
            dictionary([("level", "INFO"),
                        ("message", "Composed message remove non existing attribute")])
        )

    def test_ignore_trailing_dot_in_key(self):
        with self.assertLogs('test_formatter', level=logging.DEBUG) as ctx:
            logger = logging.getLogger('test_formatter')
            self._configure_logger(
                logger,
                fmt=dictionary([
                    ("level", "levelname"),
                    ("message", "message"),
                    ("trailing-dotted-key", "dotted_key."),
                ]),
                remove_empty=False,
                ignore_missing=True
            )
            logger.info('Composed message %s', 'remove non existing dotted key')
            logger.info(
                'Composed message %s',
                'existing dotted key as dict',
                extra={"dotted_key": {
                    "a": 12, "b": "this is b"
                }}
            )
        self.assertDictEqual(
            json.loads(ctx.output[0], object_pairs_hook=dictionary),
            dictionary([("level", "INFO"),
                        ("message", "Composed message remove non existing dotted key"),
                        ("trailing-dotted-key", dictionary())])
        )
        self.assertDictEqual(
            json.loads(ctx.output[1], object_pairs_hook=dictionary),
            dictionary([("level", "INFO"),
                        ("message", "Composed message existing dotted key as dict"),
                        ("trailing-dotted-key", dictionary([("a", 12), ("b", "this is b")]))])
        )

    def test_ignore_double_trailing_dot_in_key(self):
        with self.assertLogs('test_formatter', level=logging.DEBUG) as ctx:
            logger = logging.getLogger('test_formatter')
            self._configure_logger(
                logger,
                fmt=dictionary([
                    ("level", "levelname"),
                    ("message", "message"),
                    ("trailing-dotted-key", "dotted_key.."),
                ]),
                remove_empty=False,
                ignore_missing=True
            )
            logger.info('Composed message %s', 'remove non existing dotted key')
            logger.info(
                'Composed message %s',
                'existing dotted key as dict',
                extra={"dotted_key": ['a', 'b']}
            )
        self.assertDictEqual(
            json.loads(ctx.output[0], object_pairs_hook=dictionary),
            dictionary([("level", "INFO"),
                        ("message", "Composed message remove non existing dotted key"),
                        ("trailing-dotted-key", [])])
        )
        self.assertDictEqual(
            json.loads(ctx.output[1], object_pairs_hook=dictionary),
            dictionary([("level", "INFO"),
                        ("message", "Composed message existing dotted key as dict"),
                        ("trailing-dotted-key", ['a', 'b'])])
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

    def test_sub_key(self):
        with self.assertLogs('test_formatter', level=logging.DEBUG) as ctx:
            logger = logging.getLogger('test_formatter')
            self._configure_logger(
                logger,
                fmt=dictionary([
                    ('level', 'levelname'),
                    ('request', dictionary([('path', 'request.path')])),
                    ('message', 'message'),
                ]),
                ignore_missing=True
            )
            logger.info(
                'Composed message %s',
                'with extra request',
                extra={'request': {
                    'path': '/my/path', 'method': 'GET', 'scheme': 'https'
                }}
            )
            logger.info('Composed message %s', 'without extra request')
        self.assertDictEqual(
            json.loads(ctx.output[0], object_pairs_hook=dictionary),
            dictionary([
                ("level", "INFO"),
                ("request", dictionary([("path", "/my/path")])),
                ("message", "Composed message with extra request"),
            ])
        )
        self.assertDictEqual(
            json.loads(ctx.output[1], object_pairs_hook=dictionary),
            dictionary([
                ("level", "INFO"),
                ("request", dictionary([("path", "")])),
                ("message", "Composed message without extra request"),
            ])
        )

    def test_sub_key_list(self):
        with self.assertLogs('test_formatter', level=logging.DEBUG) as ctx:
            logger = logging.getLogger('test_formatter')
            self._configure_logger(
                logger,
                fmt=dictionary([
                    ('level', 'levelname'),
                    ('request', ['request.path', 'request.method']),
                    ('message', 'message'),
                ]),
                ignore_missing=True
            )
            logger.info(
                'Composed message %s',
                'with extra request',
                extra={'request': {
                    'path': '/my/path', 'method': 'GET', 'scheme': 'https'
                }}
            )
            logger.info('Composed message %s', 'without extra request')
        self.assertDictEqual(
            json.loads(ctx.output[0], object_pairs_hook=dictionary),
            dictionary([
                ("level", "INFO"),
                ("request", ["/my/path", "GET"]),
                ("message", "Composed message with extra request"),
            ])
        )
        self.assertDictEqual(
            json.loads(ctx.output[1], object_pairs_hook=dictionary),
            dictionary([
                ("level", "INFO"),
                ("request", ['', '']),
                ("message", "Composed message without extra request"),
            ])
        )

    def test_sub_key_remove_empty(self):
        with self.assertLogs('test_formatter', level=logging.DEBUG) as ctx:
            logger = logging.getLogger('test_formatter')
            self._configure_logger(
                logger,
                fmt=dictionary([
                    ('level', 'levelname'),
                    ('request', dictionary([('path', 'request.path')])),
                    ('message', 'message'),
                ]),
                remove_empty=True,
                ignore_missing=True
            )
            logger.info(
                'Composed message %s',
                'with extra request',
                extra={'request': {
                    'path': '/my/path', 'method': 'GET'
                }}
            )
            logger.info('Composed message %s', 'without extra request')
        self.assertDictEqual(
            json.loads(ctx.output[0], object_pairs_hook=dictionary),
            dictionary([
                ("level", "INFO"),
                ("request", dictionary([("path", "/my/path")])),
                ("message", "Composed message with extra request"),
            ])
        )
        self.assertDictEqual(
            json.loads(ctx.output[1], object_pairs_hook=dictionary),
            dictionary([
                ("level", "INFO"),
                ("message", "Composed message without extra request"),
            ])
        )

    def test_sub_key_list_remove_empty(self):
        with self.assertLogs('test_formatter', level=logging.DEBUG) as ctx:
            logger = logging.getLogger('test_formatter')
            self._configure_logger(
                logger,
                fmt=dictionary([
                    ('level', 'levelname'),
                    ('request', ['request.path', 'request.method']),
                    ('message', 'message'),
                ]),
                remove_empty=True,
                ignore_missing=True
            )
            logger.info(
                'Composed message %s',
                'with extra request',
                extra={'request': {
                    'path': '/my/path', 'method': 'GET', 'scheme': 'https'
                }}
            )
            logger.info('Composed message %s', 'without extra request')
        self.assertDictEqual(
            json.loads(ctx.output[0], object_pairs_hook=dictionary),
            dictionary([
                ("level", "INFO"),
                ("request", ["/my/path", "GET"]),
                ("message", "Composed message with extra request"),
            ])
        )
        self.assertDictEqual(
            json.loads(ctx.output[1], object_pairs_hook=dictionary),
            dictionary([
                ("level", "INFO"),
                ("message", "Composed message without extra request"),
            ])
        )

    def test_missing_attribute(self):
        with self.assertLogs('test_formatter', level=logging.DEBUG) as ctx:
            logger = logging.getLogger('test_formatter')
            self._configure_logger(
                logger,
                fmt=dictionary([
                    ('level', 'levelname'),
                    ('1-missing-attr', 'this is a constant'),
                    ('2-missing-attr', 'my_constant'),
                    ('3-missing-attr', 'This is a constant with dot.'),
                    ('4-missing-attr', 'my.constant%()s'),
                    ('5-missing-attr', 'my.constant.%()s'),
                    ('6-missing-attr', '%(This is a constant with dot.)s'),
                    ('7-missing-attr', '%(test.a.)s'),
                    ('my-extra', 'my_extra'),
                    ('message', 'message'),
                ]),
                remove_empty=False,
                ignore_missing=True
            )
            logger.info(
                'Composed message %s',
                'with extra and constants',
                extra={'my_extra': 'this is an extra'}
            )
            logger.info('Composed message %s', 'without extra')
        self.assertDictEqual(
            json.loads(ctx.output[0], object_pairs_hook=dictionary),
            dictionary([
                ("level", "INFO"),
                ('1-missing-attr', ''),
                ('2-missing-attr', ''),
                ('3-missing-attr', {}),
                ('4-missing-attr', ''),
                ('5-missing-attr', ''),
                ('6-missing-attr', ''),
                ('7-missing-attr', ''),
                ("my-extra", "this is an extra"),
                ("message", "Composed message with extra and constants"),
            ])
        )
        self.assertDictEqual(
            json.loads(ctx.output[1], object_pairs_hook=dictionary),
            dictionary([
                ("level", "INFO"),
                ('1-missing-attr', ''),
                ('2-missing-attr', ''),
                ('3-missing-attr', {}),
                ('4-missing-attr', ''),
                ('5-missing-attr', ''),
                ('6-missing-attr', ''),
                ('7-missing-attr', ''),
                ("my-extra", ""),
                ("message", "Composed message without extra"),
            ])
        )
