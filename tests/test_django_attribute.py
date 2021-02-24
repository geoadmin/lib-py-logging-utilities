import json
import logging
import sys
import unittest
from collections import OrderedDict

from django.conf import settings
from django.test import RequestFactory

from logging_utilities.filters.django_request import JsonDjangoRequest
from logging_utilities.formatters.json_formatter import JsonFormatter

# From python3.7, dict is ordered
if sys.version_info >= (3, 7):
    dictionary = dict
else:
    dictionary = OrderedDict

settings.configure()

logger = logging.getLogger(__name__)


class RecordDjangoAttributesTest(unittest.TestCase):

    def setUp(self):
        # Every test needs access to the request factory.
        self.factory = RequestFactory()

    @classmethod
    def _configure_django_filter(cls, _logger, include_keys=None, exclude_keys=None):
        _logger.setLevel(logging.DEBUG)

        for handler in _logger.handlers:
            django_filter = JsonDjangoRequest(include_keys=include_keys, exclude_keys=exclude_keys)
            handler.addFilter(django_filter)
            formatter = JsonFormatter(
                dictionary([
                    ('level', 'levelname'),
                    ('message', 'message'),
                    ('request', 'request'),
                ]),
                remove_empty=True
            )
            handler.setFormatter(formatter)

    def test_django_include_keys(self):
        # pylint: disable=protected-access
        django_filter = JsonDjangoRequest(
            include_keys=[
                'request.META.METHOD',
                'request.environ',
                'request.environ._include',
            ]
        )
        # True assertions
        self.assertTrue(django_filter._include_key('request', 'request'))
        self.assertTrue(django_filter._include_key('request.META', 'META'))
        self.assertTrue(django_filter._include_key('request.META.METHOD', 'METHOD'))
        self.assertTrue(django_filter._include_key('request.environ', 'environ'))
        self.assertTrue(django_filter._include_key('request.environ.CONTENT_TYPE', 'CONTENT_TYPE'))
        self.assertTrue(django_filter._include_key('request.environ._include', '_include'))
        # False assertions
        self.assertFalse(django_filter._include_key('test', 'test'))
        self.assertFalse(django_filter._include_key('request.path', 'path'))
        self.assertFalse(django_filter._include_key('request.path.full', 'full'))
        self.assertFalse(django_filter._include_key('request.META.CONTENT_TYPE', 'CONTENT_TYPE'))
        self.assertFalse(django_filter._include_key('request.META.extend.TYPE', 'TYPE'))
        self.assertFalse(django_filter._include_key('request.environ._type', '_type'))

    def test_django_exclude_keys(self):
        # pylint: disable=protected-access
        django_filter = JsonDjangoRequest(exclude_keys=['request.META.METHOD', 'request.environ'])
        # True assertions
        self.assertTrue(django_filter._exclude_key('request.META.METHOD', 'METHOD'))
        self.assertTrue(django_filter._exclude_key('request.environ', 'environ'))
        self.assertTrue(django_filter._exclude_key('request.environ.CONTENT_TYPE', 'CONTENT_TYPE'))
        self.assertTrue(django_filter._exclude_key('request.environ._include', '_include'))
        self.assertTrue(django_filter._exclude_key('request.environ._type', '_type'))
        # False assertions
        self.assertFalse(django_filter._exclude_key('test', 'test'))
        self.assertFalse(django_filter._exclude_key('request.path', 'path'))
        self.assertFalse(django_filter._exclude_key('request.path.full', 'full'))
        self.assertFalse(django_filter._exclude_key('request.META.CONTENT_TYPE', 'CONTENT_TYPE'))
        self.assertFalse(django_filter._exclude_key('request.META.extend.TYPE', 'TYPE'))
        self.assertFalse(django_filter._exclude_key('request', 'request'))
        self.assertFalse(django_filter._exclude_key('request.META', 'META'))

    def test_django_request_jsonify(self):
        request = self.factory.get('/my_path?test=true&test_2=false')
        with self.assertLogs('test_formatter', level=logging.DEBUG) as ctx:
            test_logger = logging.getLogger('test_formatter')
            self._configure_django_filter(
                test_logger,
                include_keys=[
                    'request.META.REQUEST_METHOD', 'request.META.SERVER_NAME', 'request.environ'
                ],
                exclude_keys=['request.META.SERVER_NAME', 'request.environ.wsgi']
            )
            test_logger.info('Simple message', extra={'request': request})
            test_logger.info(
                'Composed message: %s', 'this is a composed message', extra={'request': request}
            )
        message1 = json.loads(ctx.output[0], object_pairs_hook=dictionary)
        message2 = json.loads(ctx.output[1], object_pairs_hook=dictionary)
        logger.debug('message1=%s', message1)
        logger.debug('message2=%s', message2)
        self.assertDictEqual(
            message1,
            dictionary([
                ("level", "INFO"),
                ("message", "Simple message"),
                (
                    "request",
                    dictionary([("META", dictionary([("REQUEST_METHOD", "GET")])),
                                (
                                    "environ",
                                    dictionary([
                                        ("HTTP_COOKIE", ""),
                                        ("PATH_INFO", "/my_path"),
                                        ("QUERY_STRING", "test=true&test_2=false"),
                                        ("REMOTE_ADDR", "127.0.0.1"),
                                        ("REQUEST_METHOD", "GET"),
                                        ("SCRIPT_NAME", ""),
                                        ("SERVER_NAME", "testserver"),
                                        ("SERVER_PORT", "80"),
                                        ("SERVER_PROTOCOL", "HTTP/1.1"),
                                    ])
                                )])
                ),
            ]),
            msg="First message differ"
        )
        self.assertDictEqual(
            message2,
            dictionary([("level", "INFO"),
                        ("message", "Composed message: this is a composed message"),
                        (
                            "request",
                            dictionary([("META", dictionary([("REQUEST_METHOD", "GET")])),
                                        (
                                            "environ",
                                            dictionary([
                                                ("HTTP_COOKIE", ""),
                                                ("PATH_INFO", "/my_path"),
                                                ("QUERY_STRING", "test=true&test_2=false"),
                                                ("REMOTE_ADDR", "127.0.0.1"),
                                                ("REQUEST_METHOD", "GET"),
                                                ("SCRIPT_NAME", ""),
                                                ("SERVER_NAME", "testserver"),
                                                ("SERVER_PORT", "80"),
                                                ("SERVER_PROTOCOL", "HTTP/1.1"),
                                            ])
                                        )])
                        )]),
            msg="Second message differ"
        )

    def test_django_request_jsonify_other(self):
        requests = ({'a': 1}, OrderedDict([('a', 1)]), ['a'], 45, 45.5, 'a')
        with self.assertLogs('test_formatter', level=logging.DEBUG) as ctx:
            test_logger = logging.getLogger('test_formatter')
            self._configure_django_filter(
                test_logger,
                include_keys=[
                    'request.META.REQUEST_METHOD', 'request.META.SERVER_NAME', 'request.environ'
                ],
                exclude_keys=['request.META.SERVER_NAME', 'request.environ.wsgi']
            )
            for request in requests:
                test_logger.info('Simple message', extra={'request': request})

        for i, request in enumerate(requests):
            message = json.loads(ctx.output[i], object_pairs_hook=dictionary)
            self.assertEqual(request, message['request'])
