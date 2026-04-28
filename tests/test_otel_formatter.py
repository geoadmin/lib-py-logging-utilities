import json
import logging
import sys
import tempfile
import unittest
from collections import OrderedDict

from logging_utilities.formatters.otel_formatter import OtelFormatter

if sys.version_info.major >= 3 and sys.version_info.minor >= 7:
    dictionary = dict
else:
    dictionary = OrderedDict


def _make_logger(name, formatter):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    for handler in logger.handlers:
        handler.setFormatter(formatter)
    return logger


class TestOtelFormatterDefaults(unittest.TestCase):

    def test_default_keys_present(self):
        with self.assertLogs('otel.defaults', level=logging.DEBUG) as ctx:
            logger = _make_logger('otel.defaults', OtelFormatter(ignore_missing=True))
            logger.info('hello')

        msg = json.loads(ctx.output[0])
        for key in ('severity_text', 'body.string', 'log.logger'):
            self.assertIn(key, msg, f'expected key {key!r} in output')

    def test_severity_text_value(self):
        with self.assertLogs('otel.severity', level=logging.DEBUG) as ctx:
            logger = _make_logger('otel.severity', OtelFormatter(ignore_missing=True))
            logger.warning('warn msg')

        msg = json.loads(ctx.output[0])
        self.assertEqual(msg['severity_text'], 'WARNING')

    def test_body_string_value(self):
        with self.assertLogs('otel.body', level=logging.DEBUG) as ctx:
            logger = _make_logger('otel.body', OtelFormatter(ignore_missing=True))
            logger.info('the body')

        msg = json.loads(ctx.output[0])
        self.assertEqual(msg['body.string'], 'the body')

    def test_remove_empty_default(self):
        # remove_empty=True by default: keys with empty values should be absent
        with self.assertLogs('otel.remove_empty', level=logging.DEBUG) as ctx:
            logger = _make_logger('otel.remove_empty', OtelFormatter())
            logger.info('msg')

        msg = json.loads(ctx.output[0])
        # duration and otelSpanID/otelTraceID are absent when not set
        self.assertNotIn('event.duration', msg)
        self.assertNotIn('otelSpanID', msg)
        self.assertNotIn('otelTraceID', msg)


class TestOtelFormatterFmtMerge(unittest.TestCase):

    def test_fmt_overrides_default(self):
        custom_fmt = dictionary([('body.string', 'message'), ('custom_key', 'levelname')])
        with self.assertLogs('otel.merge', level=logging.DEBUG) as ctx:
            logger = _make_logger('otel.merge', OtelFormatter(fmt=custom_fmt, ignore_missing=True))
            logger.error('err')

        msg = json.loads(ctx.output[0])
        # custom key added
        self.assertEqual(msg['custom_key'], 'ERROR')
        # default key still present
        self.assertIn('severity_text', msg)

    def test_fmt_overrides_default_value(self):
        # Override an existing default key's mapping
        custom_fmt = dictionary([('severity_text', 'name')])
        with self.assertLogs('otel.override', level=logging.DEBUG) as ctx:
            logger = _make_logger(
                'otel.override', OtelFormatter(fmt=custom_fmt, ignore_missing=True)
            )
            logger.info('msg')

        msg = json.loads(ctx.output[0])
        self.assertEqual(msg['severity_text'], 'otel.override')

    def test_fmt_file_merges_with_default(self):
        file_fmt = {'extra_from_file': 'levelname', 'severity_text': 'name'}
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.json', delete=False, encoding='utf-8'
        ) as f:
            json.dump(file_fmt, f)
            tmp_path = f.name

        with self.assertLogs('otel.fmtfile', level=logging.DEBUG) as ctx:
            logger = _make_logger(
                'otel.fmtfile', OtelFormatter(fmtFile=tmp_path, ignore_missing=True)
            )
            logger.info('msg')

        msg = json.loads(ctx.output[0])
        # fmtFile key present
        self.assertIn('extra_from_file', msg)
        # fmtFile overrides default
        self.assertEqual(msg['severity_text'], 'otel.fmtfile')
        # default keys still present
        self.assertIn('body.string', msg)

    def test_fmt_wins_over_fmt_file(self):
        file_fmt = {'severity_text': 'name'}
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.json', delete=False, encoding='utf-8'
        ) as f:
            json.dump(file_fmt, f)
            tmp_path = f.name

        # fmt overrides fmtFile for the same key
        custom_fmt = dictionary([('severity_text', 'levelname')])
        with self.assertLogs('otel.fmtfile_vs_fmt', level=logging.DEBUG) as ctx:
            logger = _make_logger(
                'otel.fmtfile_vs_fmt',
                OtelFormatter(fmt=custom_fmt, fmtFile=tmp_path, ignore_missing=True),
            )
            logger.warning('msg')

        msg = json.loads(ctx.output[0])
        self.assertEqual(msg['severity_text'], 'WARNING')


class TestOtelFormatterServiceName(unittest.TestCase):

    def test_service_name_injected(self):
        with self.assertLogs('otel.svcname', level=logging.DEBUG) as ctx:
            fmt = dictionary([('service.name', 'service_name')])
            logger = _make_logger(
                'otel.svcname',
                OtelFormatter(fmt=fmt, service_name='my-service', ignore_missing=True),
            )
            logger.info('msg')

        msg = json.loads(ctx.output[0])
        self.assertEqual(msg['service.name'], 'my-service')

    def test_no_service_name_when_not_set(self):
        with self.assertLogs('otel.nosvcname', level=logging.DEBUG) as ctx:
            fmt = dictionary([('service.name', 'service_name')])
            logger = _make_logger(
                'otel.nosvcname',
                OtelFormatter(fmt=fmt, ignore_missing=True),
            )
            logger.info('msg')

        msg = json.loads(ctx.output[0])
        # service_name not on record and ignore_missing=True → absent (remove_empty=True)
        self.assertNotIn('service.name', msg)


if __name__ == '__main__':
    unittest.main()
