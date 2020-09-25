import logging
import unittest
from logging import Formatter

from logging_utilities.filters import ConstAttribute
from logging_utilities.filters.flask_attribute import FlaskRequestAttribute


class RecordAttributesTest(unittest.TestCase):

    @classmethod
    def _configure_const_attribute(cls, logger):
        logger.setLevel(logging.DEBUG)

        for handler in logger.handlers:
            const_attribute = ConstAttribute(application="test_application")
            handler.addFilter(const_attribute)
            handler.setFormatter(Formatter("%(levelname)s:%(application)s:%(message)s"))

    @classmethod
    def _configure_flask_attribute(cls, logger):
        logger.setLevel(logging.DEBUG)

        for handler in logger.handlers:
            const_attribute = FlaskRequestAttribute(attributes=['url', 'method', 'headers', 'json'])
            handler.addFilter(const_attribute)
            handler.setFormatter(Formatter("%(levelname)s:%(message)s:%(flask_request_url)s"))

    def test_const_attribute(self):
        with self.assertLogs('test_formatter', level=logging.DEBUG) as ctx:
            logger = logging.getLogger('test_formatter')
            self._configure_const_attribute(logger)
            logger.info('Simple message')
            logger.info('Composed message: %s', 'this is a composed message')
            logger.info('Composed message %s', 'with extra', extra={'extra1': 23})
        self.assertEqual(
            ctx.output,
            [
                'INFO:test_application:Simple message',
                'INFO:test_application:Composed message: this is a composed message',
                'INFO:test_application:Composed message with extra'
            ]
        )

    def test_empty_flask_attribute(self):
        with self.assertLogs('test_formatter', level=logging.DEBUG) as ctx:
            logger = logging.getLogger('test_formatter')
            self._configure_flask_attribute(logger)
            logger.info('Simple message')
            logger.info('Composed message: %s', 'this is a composed message')
            logger.info('Composed message %s', 'with extra', extra={'extra1': 23})
        self.assertEqual(
            ctx.output,
            [
                'INFO:Simple message:',
                'INFO:Composed message: this is a composed message:',
                'INFO:Composed message with extra:'
            ]
        )
