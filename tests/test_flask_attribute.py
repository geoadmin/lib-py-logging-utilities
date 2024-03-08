import logging
import unittest
from logging import Formatter
from urllib.parse import quote

from flask import Flask

from logging_utilities.filters.flask_attribute import FlaskRequestAttribute
from logging_utilities.log_record import reset_log_record_factory
from logging_utilities.log_record import set_log_record_ignore_missing_factory

app = Flask(__name__)

FLASK_DEFAULT_FMT = "%(levelname)s:%(message)s:%(flask_request_url)s:%(flask_request_json)s:" \
                    "%(flask_request_query_string)s"
FLASK_DEFAULT_ATTRIBUTES = ['url', 'method', 'headers', 'json', 'query_string']


class FlaskAttributeTest(unittest.TestCase):

    def setUp(self):
        super().setUp()
        self.maxDiff = None

    @classmethod
    def _configure_flask_attribute(cls, logger, fmt, flask_attributes):
        logger.setLevel(logging.DEBUG)

        for handler in logger.handlers:
            flask_attribute = FlaskRequestAttribute(attributes=flask_attributes)
            handler.addFilter(flask_attribute)
            handler.setFormatter(Formatter(fmt))

    def test_empty_flask_attribute_no_context(self):
        with self.assertLogs('test_formatter', level=logging.DEBUG) as ctx:
            logger = logging.getLogger('test_formatter')
            self._configure_flask_attribute(logger, FLASK_DEFAULT_FMT, FLASK_DEFAULT_ATTRIBUTES)
            reset_log_record_factory()
            with self.assertRaises((ValueError, KeyError)):
                logger.info('Simple message')

    def test_empty_flask_attribute_no_context_ignore(self):
        with self.assertLogs('test_formatter', level=logging.DEBUG) as ctx:
            logger = logging.getLogger('test_formatter')
            self._configure_flask_attribute(logger, FLASK_DEFAULT_FMT, FLASK_DEFAULT_ATTRIBUTES)
            set_log_record_ignore_missing_factory()
            logger.info('Simple message')
            logger.info('Composed message: %s', 'this is a composed message')
            logger.info('Composed message %s', 'with extra', extra={'extra1': 23})
            reset_log_record_factory()
        self.assertEqual(
            ctx.output,
            [
                'INFO:Simple message:::',
                'INFO:Composed message: this is a composed message:::',
                'INFO:Composed message with extra:::'
            ]
        )

    def test_flask_attribute_json_data(self):
        with self.assertLogs('test_formatter', level=logging.DEBUG) as ctx:
            logger = logging.getLogger('test_formatter')
            self._configure_flask_attribute(logger, FLASK_DEFAULT_FMT, FLASK_DEFAULT_ATTRIBUTES)

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
                'INFO:Simple message:http://localhost/make_report/2017::',
                'INFO:Composed message: this is a composed message:http://localhost/make_report/2017::',
                'INFO:Composed message with extra:http://localhost/make_report/2017::',
                'INFO:Simple message:http://localhost/make_report/2017::',
                "INFO:Simple message:http://localhost/make_report/2017:non json data:",
                'INFO:Simple message:http://localhost/make_report/2017:{}:',
                "INFO:Simple message:http://localhost/make_report/2017:{'jsonData': 'this is a json data'}:",
            ]
        )

    def test_flask_attribute_query_string(self):
        with self.assertLogs('test_formatter', level=logging.DEBUG) as ctx:
            logger = logging.getLogger('test_formatter')
            self._configure_flask_attribute(logger, FLASK_DEFAULT_FMT, FLASK_DEFAULT_ATTRIBUTES)
            with app.test_request_context('/make_report/2017?param1=value1'):
                logger.info('Simple message')
                logger.info('Composed message: %s', 'this is a composed message')
                logger.info('Composed message %s', 'with extra', extra={'extra1': 23})

            with app.test_request_context('/make_report/2017?param1=value1&param2=value2'):
                logger.info('Simple message')

            with app.test_request_context(
                '/make_report/2017?param1={}'.format(quote("This a string ?"))
            ):
                logger.info('Simple message')

        self.assertEqual(
            ctx.output,
            [
                # pylint: disable=line-too-long
                'INFO:Simple message:http://localhost/make_report/2017?param1=value1::param1=value1',
                'INFO:Composed message: this is a composed message:http://localhost/make_report/2017?param1=value1::param1=value1',
                'INFO:Composed message with extra:http://localhost/make_report/2017?param1=value1::param1=value1',
                'INFO:Simple message:http://localhost/make_report/2017?param1=value1&param2=value2::param1=value1&param2=value2',
                'INFO:Simple message:http://localhost/make_report/2017?param1=This%20a%20string%20?::param1=This%20a%20string%20%3F',
            ]
        )

    def test_flask_attribute_data(self):
        with self.assertLogs('test_formatter', level=logging.DEBUG) as ctx:
            logger = logging.getLogger('test_formatter')
            self._configure_flask_attribute(logger, "%(message)s:%(flask_request_data)s", ['data'])
            data = "arbitrary data <Could be xml=true/>"
            with app.test_request_context(
                '/make_report/2017', data=data, headers={"Content-Type": "text/plain"}
            ):
                logger.info('Simple message')
                logger.info('Composed message: %s', 'this is a composed message')
                logger.info('Composed message %s', 'with extra', extra={'extra1': 23})

        self.assertEqual(
            ctx.output,
            [
                'Simple message:{}'.format(data),
                'Composed message: this is a composed message:{}'.format(data),
                'Composed message with extra:{}'.format(data),
            ]
        )

    def test_flask_attribute_form(self):
        with self.assertLogs('test_formatter', level=logging.DEBUG) as ctx:
            logger = logging.getLogger('test_formatter')
            self._configure_flask_attribute(
                logger,
                "%(message)s:%(flask_request_form)s:%(flask_request_mimetype)s",
                ['form', 'mimetype']
            )
            form = {'key1': 'value2', 'key2': '234'}
            with app.test_request_context('/make_report/2017', data=form):
                logger.info('Simple message')
                logger.info('Composed message: %s', 'this is a composed message')
                logger.info('Composed message %s', 'with extra', extra={'extra1': 23})

        self.assertEqual(
            ctx.output,
            [
                'Simple message:{}:application/x-www-form-urlencoded'.format(form),
                'Composed message: this is a composed message:{}:application/x-www-form-urlencoded'.
                format(form),
                'Composed message with extra:{}:application/x-www-form-urlencoded'.format(form),
            ]
        )

    def test_flask_attribute_args(self):
        with self.assertLogs('test_formatter', level=logging.DEBUG) as ctx:
            logger = logging.getLogger('test_formatter')
            self._configure_flask_attribute(logger, "%(message)s:%(flask_request_args)s", ['args'])

            with app.test_request_context('/make_report/2017?key1=value1&key2={"a":2}'):
                logger.info('Simple message')
                logger.info('Composed message %s', 'with extra', extra={'extra1': 23})

        self.assertEqual(
            ctx.output,
            [
                "Simple message:{'key1': 'value1', 'key2': '{\"a\":2}'}",
                "Composed message with extra:{'key1': 'value1', 'key2': '{\"a\":2}'}",
            ]
        )

    def test_flask_attribute_mimetype(self):
        with self.assertLogs('test_formatter', level=logging.DEBUG) as ctx:
            logger = logging.getLogger('test_formatter')
            self._configure_flask_attribute(
                logger,
                "%(message)s:%(flask_request_mimetype)s:%(flask_request_mimetype_params)s",
                ['mimetype', 'mimetype_params']
            )
            data = "arbitrary data <Could be xml=true/>"
            with app.test_request_context(
                '/make_report/2017', data=data, headers={"Content-Type": "text/plain"}
            ):
                logger.info('Simple message')
                logger.info('Composed message: %s', 'this is a composed message')
                logger.info('Composed message %s', 'with extra', extra={'extra1': 23})

            with app.test_request_context(
                '/make_report/2017',
                data=data,
                headers={"Content-Type": "text/plain; charset=utf-8"}
            ):
                logger.info('Simple message')
                logger.info('Composed message: %s', 'this is a composed message')
                logger.info('Composed message %s', 'with extra', extra={'extra1': 23})

        self.assertEqual(
            ctx.output,
            [
                'Simple message:text/plain:{}',
                'Composed message: this is a composed message:text/plain:{}',
                'Composed message with extra:text/plain:{}',
                "Simple message:text/plain:{'charset': 'utf-8'}",
                "Composed message: this is a composed message:text/plain:{'charset': 'utf-8'}",
                "Composed message with extra:text/plain:{'charset': 'utf-8'}",
            ]
        )

    def test_flask_attribute_view_args(self):
        with self.assertLogs('test_formatter', level=logging.DEBUG) as ctx:
            logger = logging.getLogger('test_formatter')
            self._configure_flask_attribute(
                logger, "%(message)s:%(flask_request_view_args)s", ['view_args']
            )

            # Handler required by add_url_rule function
            def handle_time(time):
                return

            # Request without view_args
            with app.test_request_context('/make_report'):
                logger.info('Simple message')
                logger.info('Composed message: %s', 'this is a composed message')
                logger.info('Composed message %s', 'with extra', extra={'extra1': 23})

            # Request with view args
            app.add_url_rule('/make_report/<time>', view_func=handle_time)
            with app.test_request_context('/make_report/current'):
                logger.info('Simple message')
                logger.info('Composed message: %s', 'this is a composed message')
                logger.info('Composed message %s', 'with extra', extra={'extra1': 23})

        self.assertEqual(
            ctx.output,
            [
                'Simple message:{}',
                'Composed message: this is a composed message:{}',
                'Composed message with extra:{}',
                "Simple message:{'time': 'current'}",
                "Composed message: this is a composed message:{'time': 'current'}",
                "Composed message with extra:{'time': 'current'}",
            ]
        )
