import logging
import unittest
from collections import OrderedDict

from logging_utilities.formatters.extra_formatter import ExtraFormatter


class ExtraFormatterTest(unittest.TestCase):
    maxDiff = None

    @classmethod
    def _configure_logger(
        cls,
        logger,
        fmt=None,
        extra_fmt=None,
        extra_default='',
        extra_pretty_print=False,
        pretty_print_kwargs=None
    ):
        logger.setLevel(logging.DEBUG)

        for handler in logger.handlers:
            formatter = ExtraFormatter(
                fmt,
                extra_default=extra_default,
                extra_fmt=extra_fmt,
                extra_pretty_print=extra_pretty_print,
                pretty_print_kwargs=pretty_print_kwargs
            )
            handler.setFormatter(formatter)

    def test_missing_extra(self):
        with self.assertLogs('test_formatter', level=logging.DEBUG) as ctx:
            logger = logging.getLogger('test_formatter')
            self._configure_logger(logger, fmt="%(message)s", extra_fmt=':%(extra1)s')
            logger.info('Simple message')
            logger.info('Composed message: %s', 'this is a composed message')
            logger.info('Simple message with extra', extra={'extra1': 23})
            logger.info('Composed message %s', 'with extra', extra={'extra1': 23})
        self.assertEqual(ctx.output[0], 'Simple message')
        self.assertEqual(ctx.output[1], 'Composed message: this is a composed message')
        self.assertEqual(ctx.output[2], 'Simple message with extra:23')
        self.assertEqual(ctx.output[3], 'Composed message with extra:23')

    def test_missing_extra_default_none(self):
        with self.assertLogs('test_formatter', level=logging.DEBUG) as ctx:
            logger = logging.getLogger('test_formatter')
            self._configure_logger(
                logger, fmt="%(message)s", extra_fmt=':%(extra1)s:%(extra2)s', extra_default=None
            )
            logger.info('Simple message')
            logger.info('Composed message: %s', 'this is a composed message')
            logger.info('Simple message with extra', extra={'extra1': 23})
            logger.info('Composed message %s', 'with extra', extra={'extra1': 23})
        self.assertEqual(ctx.output[0], 'Simple message')
        self.assertEqual(ctx.output[1], 'Composed message: this is a composed message')
        self.assertEqual(ctx.output[2], 'Simple message with extra:23:None')
        self.assertEqual(ctx.output[3], 'Composed message with extra:23:None')

    def test_extra_format_as_dict(self):
        with self.assertLogs('test_formatter', level=logging.DEBUG) as ctx:
            logger = logging.getLogger('test_formatter')
            self._configure_logger(logger, fmt="%(message)s", extra_fmt=':extra=%s')
            logger.info('Simple message')
            logger.info('Composed message: %s', 'this is a composed message')
            logger.info('Simple message with extra', extra={'extra2': 1})
            logger.info('Composed message %s', 'with extra', extra={'extra2': 1})
        self.assertEqual(ctx.output[0], 'Simple message')
        self.assertEqual(ctx.output[1], 'Composed message: this is a composed message')
        self.assertEqual(ctx.output[2], 'Simple message with extra:extra={\'extra2\': 1}')
        self.assertEqual(ctx.output[3], 'Composed message with extra:extra={\'extra2\': 1}')

    def test_extra_format_as_dict_duplicate_extra(self):
        # Make sure to not replicate extra in the dict that have been added to the standard format
        with self.assertLogs('test_formatter', level=logging.DEBUG) as ctx:
            logger = logging.getLogger('test_formatter')
            self._configure_logger(
                logger, fmt="%(message)s - %(extra1)s", extra_fmt=' - other_extra=%s'
            )
            logger.info('Simple message with extra', extra={'extra1': 1, 'extra2': 2})
            logger.info('Composed message %s', 'with extra', extra={'extra1': 1, 'extra2': 2})
        self.assertEqual(
            ctx.output[0], 'Simple message with extra - 1 - other_extra={\'extra2\': 2}'
        )
        self.assertEqual(
            ctx.output[1], 'Composed message with extra - 1 - other_extra={\'extra2\': 2}'
        )

    def test_extra_format_as_dict_pretty_print(self):
        with self.assertLogs('test_formatter', level=logging.DEBUG) as ctx:
            logger = logging.getLogger('test_formatter')
            self._configure_logger(
                logger, fmt="%(message)s", extra_fmt=':extra=%s', extra_pretty_print=True
            )
            logger.info('Simple message')
            logger.info('Composed message: %s', 'this is a composed message')
            logger.info('Simple message with extra', extra={'extra2': 1})
            logger.info('Composed message %s', 'with extra', extra={'extra2': 1})
            logger.info(
                'Big extra using pretty print',
                extra=OrderedDict([
                    ('extra1', list(map(lambda i: 'test ' * i, range(5)))),
                    ('extra2', {
                        'extra2.1': list(map(lambda i: 'test ' * i, range(5)))
                    }),
                ])
            )
        self.assertEqual(ctx.output[0], 'Simple message')
        self.assertEqual(ctx.output[1], 'Composed message: this is a composed message')
        self.assertEqual(ctx.output[2], 'Simple message with extra:extra={\'extra2\': 1}')
        self.assertEqual(ctx.output[3], 'Composed message with extra:extra={\'extra2\': 1}')
        self.assertEqual(
            ctx.output[4],
            """Big extra using pretty print:extra={'extra1': ['',
            'test ',
            'test test ',
            'test test test ',
            'test test test test '],
 'extra2': {'extra2.1': ['',
                         'test ',
                         'test test ',
                         'test test test ',
                         'test test test test ']}}"""
        )

    def test_extra_format_as_dict_pretty_print_with_args(self):
        with self.assertLogs('test_formatter', level=logging.DEBUG) as ctx:
            logger = logging.getLogger('test_formatter')
            self._configure_logger(
                logger,
                fmt="%(message)s",
                extra_fmt=':extra=%s',
                extra_pretty_print=True,
                pretty_print_kwargs={
                    'indent': 2, 'width': 20
                }
            )
            logger.info('Simple message')
            logger.info('Composed message: %s', 'this is a composed message')
            logger.info('Simple message with extra', extra={'extra2': 1})
            logger.info('Composed message %s', 'with extra', extra={'extra2': 1})
            logger.info(
                'Big extra using pretty print',
                extra=OrderedDict([
                    ('extra1', list(map(lambda i: 'test ' * i, range(5)))),
                    ('extra2', {
                        'extra2.1': list(map(lambda i: 'test ' * i, range(5)))
                    }),
                ])
            )
        self.assertEqual(ctx.output[0], 'Simple message')
        self.assertEqual(ctx.output[1], 'Composed message: this is a composed message')
        self.assertEqual(ctx.output[2], 'Simple message with extra:extra={\'extra2\': 1}')
        self.assertEqual(ctx.output[3], 'Composed message with extra:extra={\'extra2\': 1}')
        # yapf: disable
        self.assertEqual(
            ctx.output[4],
        """Big extra using pretty print:extra={ 'extra1': [ '',
              'test ',
              'test '
              'test ',
              'test '
              'test '
              'test ',
              'test '
              'test '
              'test '
              'test '],
  'extra2': { 'extra2.1': [ '',
                            'test ',
                            'test '
                            'test ',
                            'test '
                            'test '
                            'test ',
                            'test '
                            'test '
                            'test '
                            'test ']}}"""
        )
        # yapf: enable

    def test_extra_format_custom(self):
        with self.assertLogs('test_formatter', level=logging.DEBUG) as ctx:
            logger = logging.getLogger('test_formatter')
            self._configure_logger(
                logger, fmt="%(message)s", extra_fmt=':extra2=%(extra2)s:extra3=%(extra3)s'
            )
            logger.info('Simple message')
            logger.info('Composed message: %s', 'this is a composed message')
            logger.info('Simple message with extra', extra={'extra1': 23, 'extra2': 1})
            logger.info(
                'Composed message %s',
                'with extra',
                extra={
                    'extra1': 23, 'extra2': 1, 'extra3': 'test'
                }
            )
        self.assertEqual(ctx.output[0], 'Simple message')
        self.assertEqual(ctx.output[1], 'Composed message: this is a composed message')
        self.assertEqual(ctx.output[2], 'Simple message with extra:extra2=1:extra3=')
        self.assertEqual(ctx.output[3], 'Composed message with extra:extra2=1:extra3=test')

    def test_extra_format_custom_default_none(self):
        with self.assertLogs('test_formatter', level=logging.DEBUG) as ctx:
            logger = logging.getLogger('test_formatter')
            self._configure_logger(
                logger,
                fmt="%(message)s",
                extra_fmt=':extra2=%(extra2)s:extra3=%(extra3)s',
                extra_default=None
            )
            logger.info('Simple message')
            logger.info('Composed message: %s', 'this is a composed message')
            logger.info('Simple message with extra', extra={'extra1': 23, 'extra2': 1})
            logger.info(
                'Composed message %s',
                'with extra',
                extra={
                    'extra1': 23, 'extra2': 1, 'extra3': 'test'
                }
            )
        self.assertEqual(ctx.output[0], 'Simple message')
        self.assertEqual(ctx.output[1], 'Composed message: this is a composed message')
        self.assertEqual(ctx.output[2], 'Simple message with extra:extra2=1:extra3=None')
        self.assertEqual(ctx.output[3], 'Composed message with extra:extra2=1:extra3=test')

    def test_extra_format_custom_pretty_print(self):
        with self.assertLogs('test_formatter', level=logging.DEBUG) as ctx:
            logger = logging.getLogger('test_formatter')
            self._configure_logger(
                logger,
                fmt="%(message)s",
                extra_fmt=':extra2=%(extra2)s:extra3=%(extra3)s',
                extra_pretty_print=True
            )
            logger.info('Simple message')
            logger.info('Composed message: %s', 'this is a composed message')
            with self.assertRaises(ValueError):
                logger.info('Simple message with extra', extra={'extra1': 23, 'extra2': 1})
                logger.info(
                    'Composed message %s',
                    'with extra',
                    extra={
                        'extra1': 23, 'extra2': 1, 'extra3': 'test'
                    }
                )
        self.assertEqual(ctx.output[0], 'Simple message')
        self.assertEqual(ctx.output[1], 'Composed message: this is a composed message')
