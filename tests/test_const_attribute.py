import logging
import unittest
from logging import Formatter

from nose2.tools import params

from logging_utilities.filters import ConstAttribute


class RecordAttributesIgnoreMissingTest(unittest.TestCase):

    def setUp(self):
        super().setUp()
        self.maxDiff = None

    @classmethod
    def _configure_const_attribute(cls, logger, fmt, value):
        logger.setLevel(logging.DEBUG)

        for handler in logger.handlers:
            const_attribute = ConstAttribute(const_key=value)
            handler.addFilter(const_attribute)
            handler.setFormatter(Formatter(fmt))

    @params('string value', 1, 1.1, [1, 'b'], None, {}, {'a': 1, 'b': {'c': ['a']}})
    def test_const_attribute(self, value):
        with self.assertLogs('test_formatter', level=logging.DEBUG) as ctx:
            logger = logging.getLogger('test_formatter')
            self._configure_const_attribute(
                logger, "%(levelname)s:%(const_key)s:%(message)s", value
            )
            logger.info('Simple message')
            logger.info('Composed message: %s', 'this is a composed message')
            logger.info('Composed message %s', 'with extra', extra={'extra1': 23})
        self.assertEqual(
            ctx.output,
            [
                'INFO:{}:Simple message'.format(value),
                'INFO:{}:Composed message: this is a composed message'.format(value),
                'INFO:{}:Composed message with extra'.format(value)
            ]
        )

    @params('string value', 1, 1.1, [1, 'b'], None, {}, {'a': 1, 'b': {'c': ['a']}})
    def test_const_attribute_and_extra(self, value):
        with self.assertLogs('test_formatter', level=logging.DEBUG) as ctx:
            logger = logging.getLogger('test_formatter')
            self._configure_const_attribute(
                logger, "%(levelname)s:%(const_key)s:%(message)s:%(extra1)s", value
            )
            logger.info('Composed message %s', 'with extra', extra={'extra1': 23})
        self.assertEqual(ctx.output, ['INFO:{}:Composed message with extra:23'.format(value)])
