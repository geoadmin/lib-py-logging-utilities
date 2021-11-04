import logging
import unittest
from logging import Formatter
from urllib.parse import quote

from flask import Flask

from logging_utilities.filters import ConstAttribute
from logging_utilities.filters.flask_attribute import FlaskRequestAttribute

app = Flask(__name__)


class RecordAttributesTest(unittest.TestCase):

    def setUp(self):
        super().setUp()
        self.maxDiff = None

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
            const_attribute = FlaskRequestAttribute(
                attributes=['url', 'method', 'headers', 'json', 'query_string']
            )
            handler.addFilter(const_attribute)
            handler.setFormatter(
                Formatter(
                    "%(levelname)s:%(message)s:%(flask_request_url)s:%(flask_request_json)s:%(flask_request_query_string)s"
                )
            )

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
                'INFO:Simple message:::',
                'INFO:Composed message: this is a composed message:::',
                'INFO:Composed message with extra:::'
            ]
        )

    def test_flask_attribute_json(self):
        with self.assertLogs('test_formatter', level=logging.DEBUG) as ctx:
            logger = logging.getLogger('test_formatter')
            self._configure_flask_attribute(logger)

            with app.test_request_context('/make_report/2017', data={'format': 'short'}):
                logger.info('Simple message')
                logger.info('Composed message: %s', 'this is a composed message')
                logger.info('Composed message %s', 'with extra', extra={'extra1': 23})

            with app.test_request_context('/make_report/2017', data=''):
                logger.info('Simple message')

            with app.test_request_context(
                '/make_report/2017', data='non json data', content_type='application/json'
            ):
                logger.info('Simple message')

            with app.test_request_context(
                '/make_report/2017', data='{}', content_type='application/json'
            ):
                logger.info('Simple message')

            with app.test_request_context(
                '/make_report/2017',
                data='{"jsonData": "this is a json data"}',
                content_type='application/json'
            ):
                logger.info('Simple message')
        self.assertEqual(
            ctx.output,
            [
                # pylint: disable=line-too-long
                'INFO:Simple message:http://localhost/make_report/2017:None:',
                'INFO:Composed message: this is a composed message:http://localhost/make_report/2017:None:',
                'INFO:Composed message with extra:http://localhost/make_report/2017:None:',
                'INFO:Simple message:http://localhost/make_report/2017:None:',
                "INFO:Simple message:http://localhost/make_report/2017:b'non json data':",
                'INFO:Simple message:http://localhost/make_report/2017:{}:',
                "INFO:Simple message:http://localhost/make_report/2017:{'jsonData': 'this is a json data'}:",
            ]
        )

    def test_flask_attribute_query_string(self):
        with self.assertLogs('test_formatter', level=logging.DEBUG) as ctx:
            logger = logging.getLogger('test_formatter')
            self._configure_flask_attribute(logger)

            with app.test_request_context('/make_report/2017?param1=value1'):
                logger.info('Simple message')
                logger.info('Composed message: %s', 'this is a composed message')
                logger.info('Composed message %s', 'with extra', extra={'extra1': 23})

            with app.test_request_context('/make_report/2017?param1=value1&param2=value2'):
                logger.info('Simple message')

            with app.test_request_context(f'/make_report/2017?param1={quote("This a string ?")}'):
                logger.info('Simple message')

        self.assertEqual(
            ctx.output,
            [
                # pylint: disable=line-too-long
                'INFO:Simple message:http://localhost/make_report/2017?param1=value1:None:param1=value1',
                'INFO:Composed message: this is a composed message:http://localhost/make_report/2017?param1=value1:None:param1=value1',
                'INFO:Composed message with extra:http://localhost/make_report/2017?param1=value1:None:param1=value1',
                'INFO:Simple message:http://localhost/make_report/2017?param1=value1&param2=value2:None:param1=value1&param2=value2',
                'INFO:Simple message:http://localhost/make_report/2017?param1=This%20a%20string%20%3F:None:param1=This%20a%20string%20%3F',
            ]
        )
