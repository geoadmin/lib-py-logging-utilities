import logging
import unittest
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed

from logging_utilities.context import get_logging_context
from logging_utilities.context import remove_logging_context
from logging_utilities.context import set_logging_context
from logging_utilities.context.thread_context import ThreadMappingContext
from logging_utilities.formatters.json_formatter import JsonFormatter
from logging_utilities.log_record import reset_log_record_factory
from logging_utilities.log_record import set_log_record_ignore_missing_factory

initial_factory = logging.getLogRecordFactory()


def create_dummy_log(factory):
    return factory(__name__, logging.DEBUG, __file__, 0, '', [], None)


class ThreadContextTest(unittest.TestCase):
    # pylint: disable=invalid-name

    def test_thread_context_empty(self):
        ctx = ThreadMappingContext()
        self.assertEqual(len(ctx), 0)
        self.assertEqual(ctx, {})

    def test_thread_context_init(self):
        ctx = ThreadMappingContext()
        ctx.init({'a': 1})
        self.assertNotEqual(len(ctx), 0)
        self.assertEqual(ctx, {'a': 1})

        ctx.init({'c': 3})
        self.assertEqual(ctx, {'c': 3})

    def test_thread_context_init_invalid(self):
        ctx = ThreadMappingContext()
        self.assertRaises(ValueError, ctx.init, 'a string')

    def test_thread_context_len(self):
        ctx = ThreadMappingContext()
        ctx.init({'a': 1})
        self.assertEqual(len(ctx), 1)

    def test_thread_context_get(self):
        ctx = ThreadMappingContext()
        ctx.init({'a': 1})
        self.assertEqual(ctx.get('b', 'not found'), 'not found')
        try:
            self.assertEqual(ctx.get('b'), None)
        except KeyError:
            self.fail('get() should never raise KeyError')

        self.assertEqual(ctx.get('a'), 1)

        self.assertEqual(ctx['a'], 1)

    def test_thread_context_pop(self):
        ctx = ThreadMappingContext()
        ctx.init({'a': 1, 'b': 2})

        self.assertEqual(ctx.pop('a'), 1)
        self.assertNotIn('a', ctx)

        self.assertIn('b', ctx)

        self.assertRaises(KeyError, ctx.pop, 'c')
        self.assertIsNone(ctx.pop('c', None))
        self.assertEqual(ctx.pop('c', 'not found'), 'not found')

    def test_thread_context_set(self):
        ctx = ThreadMappingContext()

        ctx['a'] = 1
        self.assertEqual(ctx, {'a': 1})

        ctx.set('b', 2)
        self.assertEqual(ctx, {'a': 1, 'b': 2})

    def test_thread_context_del(self):
        ctx = ThreadMappingContext()
        ctx.init({'a': 1, 'b': 2, 'c': 3})

        del ctx['a']
        self.assertEqual(ctx, {'b': 2, 'c': 3})

        ctx.delete('b')
        self.assertEqual(ctx, {'c': 3})

    def test_thread_context_clear(self):
        ctx = ThreadMappingContext()
        ctx.init({'a': 1, 'b': 2, 'c': 3})

        ctx.clear()
        self.assertEqual(ctx, {})

    def test_thread_context_contains(self):
        ctx = ThreadMappingContext()
        ctx.init({'a': 1, 'b': 2})

        self.assertTrue('a' in ctx)
        self.assertFalse('c' in ctx)

    def test_thread_context_iter(self):
        ctx = ThreadMappingContext()
        ctx.init({'a': 1, 'b': 2})

        for k, v in ctx.items():
            self.assertIn(k, ['a', 'b'])
            if k == 'a':
                self.assertEqual(v, 1)
            elif k == 'b':
                self.assertEqual(v, 2)
            else:
                self.fail(f'Invalid key {k}')

        self.assertListEqual(list(ctx.keys()), ['a', 'b'])

        self.assertListEqual(list(ctx.values()), [1, 2])

    def test_thread_context_str(self):
        ctx = ThreadMappingContext()
        ctx.init({'a': 1, 'b': 2, 'c': 'my string'})
        self.assertEqual(str(ctx), "{'a': 1, 'b': 2, 'c': 'my string'}")


class LoggingContextTest(unittest.TestCase):

    def tearDown(self):
        super().tearDown()
        remove_logging_context()
        self.assertEqual(initial_factory, logging.getLogRecordFactory())

    def test_logging_context_empty(self):
        set_logging_context()
        factory_with_context = logging.getLogRecordFactory()

        # Make sure the factory has been changed
        self.assertNotEqual(initial_factory, factory_with_context)

        # Create a dummy log to check the contex
        record = create_dummy_log(factory_with_context)
        self.assertTrue(hasattr(record, 'context'))
        self.assertIn('context', record.__dict__)
        self.assertEqual({}, record.context)

    def test_logging_context_set(self):
        ctx1 = {'a': 1}
        set_logging_context(ctx1)
        record = create_dummy_log(logging.getLogRecordFactory())
        self.assertEqual(ctx1, record.context)

        ctx2 = {'a': 2}
        set_logging_context(ctx2)
        record = create_dummy_log(logging.getLogRecordFactory())
        self.assertEqual(ctx2, record.context)

    def test_logging_context_get(self):
        self.assertIsNone(get_logging_context())

        ctx1 = {'a': 1}
        set_logging_context(ctx1)

        self.assertEqual(ctx1, get_logging_context())

    def test_logging_context_modify(self):
        set_logging_context()
        factory_with_context = logging.getLogRecordFactory()

        record = create_dummy_log(factory_with_context)
        self.assertTrue(hasattr(record, 'context'))
        self.assertIn('context', record.__dict__)
        self.assertEqual(record.context, {})

        # Modify the context
        context = get_logging_context()
        context['a'] = 'added a string'
        record = create_dummy_log(factory_with_context)
        self.assertTrue(hasattr(record, 'context'))
        self.assertIn('context', record.__dict__)
        self.assertEqual(record.context, context)
        self.assertEqual(record.__dict__['context'], context)

        # Modify the context again
        context['a'] = 1
        context['b'] = 2
        self.assertEqual(record.context, context)

    def test_logging_context_set_in_thread(self):
        set_logging_context()
        contexts = {'1': {'a': 1}, '2': {'a': 2}, '3': {'b': 3}}

        def _test_logging_context_thread(ctx_id):
            set_logging_context(contexts[ctx_id])
            record = create_dummy_log(logging.getLogRecordFactory())
            self.assertTrue(hasattr(record, 'context'))
            self.assertEqual(contexts[ctx_id], record.context)
            return str(record.context)

        with ThreadPoolExecutor(max_workers=len(contexts)) as executor:
            future_to_ctx_id = {
                executor.submit(_test_logging_context_thread, ctx_id): ctx_id for ctx_id in contexts
            }
            for future in as_completed(future_to_ctx_id):
                ctx_id = future_to_ctx_id[future]
                try:
                    context = future.result()
                except Exception as exception:  # pylint: disable=broad-except
                    self.fail(f'Excpetion {exception} raised in thread')
                self.assertEqual(str(contexts[ctx_id]), context)

    def test_logging_context_with_custom_log_record(self):
        record = create_dummy_log(logging.getLogRecordFactory())
        with self.assertRaises(KeyError):
            record.__dict__['non_existant_attribute']  # pylint: disable=pointless-statement

        set_log_record_ignore_missing_factory()
        record = create_dummy_log(logging.getLogRecordFactory())
        self.assertEqual(record.__dict__['non_existant_attribute'], '')

        set_logging_context({'a': 'my-context'})
        record = create_dummy_log(logging.getLogRecordFactory())
        self.assertTrue(hasattr(record, 'context'))
        self.assertEqual(record.context, {'a': 'my-context'})
        self.assertEqual(record.__dict__['non_existant_attribute'], '')
        reset_log_record_factory()

        record = create_dummy_log(logging.getLogRecordFactory())
        self.assertFalse(hasattr(record, 'context'))

    def test_logging_context_logger_standard_fmt(self):
        set_logging_context({'a': 'my-context'})
        with self.assertLogs('test_formatter', level=logging.DEBUG) as ctx:
            logger = logging.getLogger('test_formatter')
            logger.setLevel(logging.DEBUG)

            for handler in logger.handlers:
                formatter = logging.Formatter("%(message)s - %(context)s")
                handler.setFormatter(formatter)

            logger.debug('My message with context')
        self.assertEqual(ctx.output[0], "My message with context - {'a': 'my-context'}")

    def test_logging_context_logger_json_fmt(self):
        set_logging_context({'a': 'my-context'})
        with self.assertLogs('test_formatter', level=logging.DEBUG) as ctx:
            logger = logging.getLogger('test_formatter')
            logger.setLevel(logging.DEBUG)

            for handler in logger.handlers:
                formatter = JsonFormatter(
                    {
                        "message": "message", "context": "context"
                    },
                    default=dict,
                )
                handler.setFormatter(formatter)

            logger.debug('My message with context')
        self.assertEqual(
            ctx.output[0], '{"message": "My message with context", "context": {"a": "my-context"}}'
        )

    def test_logging_context_logger_json_fmt_sub_element(self):
        set_logging_context({'a': 'my-context'})
        with self.assertLogs('test_formatter', level=logging.DEBUG) as ctx:
            logger = logging.getLogger('test_formatter')
            logger.setLevel(logging.DEBUG)

            for handler in logger.handlers:
                formatter = JsonFormatter(
                    {
                        "message": "message", "context": "context.a"
                    },
                    default=dict,
                )
                handler.setFormatter(formatter)

            logger.debug('My message with context')
        self.assertEqual(
            ctx.output[0], '{"message": "My message with context", "context": "my-context"}'
        )
