import logging
import unittest
from logging import Formatter
from logging import Logger

from nose2.tools import params

from logging_utilities.log_record import LogRecordIgnoreMissing
from logging_utilities.log_record import _DictIgnoreMissing
from logging_utilities.log_record import reset_log_record_factory
from logging_utilities.log_record import set_log_record_ignore_missing_factory


class DictIgnoreMissingTest(unittest.TestCase):

    def test_dict_ignore_missing_default(self):
        dct = _DictIgnoreMissing()
        self.assertEqual(dct['unknown'], '')

    @params(None, 'my-default', 0, 100, {'1': 'default'}, {}, [], [1], ['default'])
    def test_dict_ignore_missing(self, default):

        class _DictIgnoreMissingX(_DictIgnoreMissing):
            _dft_value = default

        dct = _DictIgnoreMissingX()
        self.assertEqual(dct['unknown'], default)


class LogRecordIgnoreMissingTest(unittest.TestCase):

    def test_log_record_missing_default(self):
        record = LogRecordIgnoreMissing(
            'my-record', logging.INFO, 'my/path', 0, 'my message', None, False
        )
        self.assertEqual(record.__dict__['unknown'], '')
        self.assertEqual(record.__dict__['name'], 'my-record')
        self.assertEqual(record.__dict__['levelno'], logging.INFO)

    def test_logger_missing_default(self):
        set_log_record_ignore_missing_factory()
        logger = Logger('my-logger')

        record = logger.makeRecord(
            'my-record',
            logging.INFO,
            'test',
            0,
            'my message: %s %d', ('test', 2),
            False,
            extra={'my-extra': 'this is an extra'}
        )

        self.assertEqual(record.__dict__['name'], 'my-record')
        self.assertEqual(record.__dict__['levelno'], logging.INFO)
        self.assertEqual(record.getMessage(), 'my message: test 2')
        self.assertEqual(record.__dict__['my-extra'], 'this is an extra')
        self.assertEqual(record.__dict__['unknown'], '')
        reset_log_record_factory()

    @params(None, 'my-default', 0, 100, {'1': 'default'}, {}, [], [1], ['default'])
    def test_logger_missing(self, default):
        set_log_record_ignore_missing_factory(dft_value=default)
        logger = Logger('my-logger')

        record = logger.makeRecord(
            'my-record',
            logging.INFO,
            'test',
            0,
            'my message: %s %d', ('test', 2),
            False,
            extra={'my-extra': 'this is an extra'}
        )

        self.assertEqual(record.__dict__['name'], 'my-record')
        self.assertEqual(record.__dict__['levelno'], logging.INFO)
        self.assertEqual(record.getMessage(), 'my message: test 2')
        self.assertEqual(record.__dict__['my-extra'], 'this is an extra')
        self.assertEqual(record.__dict__['unknown'], default)
        reset_log_record_factory()


class LoggerIgnoreMissingTest(unittest.TestCase):

    def setUp(self):
        super().setUp()
        self.maxDiff = None

    @classmethod
    def _configure_logging(cls, logger, fmt):
        logger.setLevel(logging.DEBUG)

        for handler in logger.handlers:
            handler.setFormatter(Formatter(fmt))

    def test_logger_ignore_missing_extra_default(self):
        with self.assertLogs('test_formatter', level=logging.DEBUG) as ctx:
            set_log_record_ignore_missing_factory()
            logger = logging.getLogger('test_formatter')
            self._configure_logging(logger, "%(levelname)s:%(message)s:%(missing_attribute)s")
            logger.info('Simple message')
            logger.info('Composed message: %s', 'this is a composed message')
            logger.info('Composed message %s', 'with extra', extra={'extra1': 23})
            reset_log_record_factory()
        self.assertEqual(
            ctx.output,
            [
                'INFO:Simple message:',
                'INFO:Composed message: this is a composed message:',
                'INFO:Composed message with extra:'
            ]
        )

    @params(None, 'my-default', 0, 100, {'1': 'default'}, {}, [], [1], ['default'])
    def test_logger_ignore_missing_extra(self, default):
        with self.assertLogs('test_formatter', level=logging.DEBUG) as ctx:
            set_log_record_ignore_missing_factory(default)
            logger = logging.getLogger('test_formatter')
            self._configure_logging(logger, "%(levelname)s:%(message)s:%(missing_attribute)s")
            logger.info('Simple message')
            logger.info('Composed message: %s', 'this is a composed message')
            logger.info('Composed message %s', 'with extra', extra={'extra1': 23})
            reset_log_record_factory()
        self.assertEqual(
            ctx.output,
            [
                'INFO:Simple message:' + str(default),
                'INFO:Composed message: this is a composed message:' + str(default),
                'INFO:Composed message with extra:' + str(default)
            ]
        )
