import json
import logging
import unittest

from logging_utilities.filters.attr_type_filter import AttrTypeFilter
from logging_utilities.filters.attr_type_filter import is_instance
from logging_utilities.formatters.json_formatter import JsonFormatter


class TestObject:

    def __str__(self):
        return 'Test Object'


class TestSubobject(TestObject):

    def __str__(self):
        return 'Test Subobject'


class IsInstanceTest(unittest.TestCase):

    def test_pass_types(self):
        self.assertTrue(is_instance(TestObject(), TestObject))
        self.assertFalse(is_instance(TestObject(), TestSubobject))
        self.assertTrue(is_instance(TestSubobject(), TestObject))
        self.assertTrue(is_instance(TestSubobject(), TestSubobject))
        self.assertFalse(is_instance(TestSubobject(), str))

    def test_pass_dotless_strings(self):
        self.assertTrue(is_instance(TestObject(), 'TestObject'))
        self.assertFalse(is_instance(TestObject(), 'TestSubobject'))
        self.assertTrue(is_instance(TestSubobject(), 'TestObject'))
        self.assertTrue(is_instance(TestSubobject(), 'TestSubobject'))
        self.assertFalse(is_instance(TestSubobject(), 'str'))

    def test_pass_dotted_strings(self):
        self.assertTrue(is_instance(TestObject(), 'tests.test_attr_type_filter.TestObject'))
        self.assertFalse(is_instance(TestObject(), 'tests.test_attr_type_filter.TestSubobject'))
        self.assertTrue(is_instance(TestSubobject(), 'tests.test_attr_type_filter.TestObject'))
        self.assertTrue(is_instance(TestSubobject(), 'tests.test_attr_type_filter.TestSubobject'))
        self.assertFalse(is_instance(TestSubobject(), 'builtins.str'))


class AttrTypeFilterTest(unittest.TestCase):

    def setUp(self):
        self.logger = logging.getLogger('test_formatter')
        self.logger.setLevel(logging.DEBUG)

    def log_and_assert(self, type_validators, extra_dict, filtered_extra_dict):
        with self.assertLogs(self.logger, level=logging.INFO) as ctx:
            for handler in self.logger.handlers:
                handler.setFormatter(JsonFormatter(add_always_extra=True))
                for validator in type_validators:
                    handler.addFilter(validator)
            self.logger.info('Composed message %s', 'with extra', extra=extra_dict)
        message = json.loads(ctx.output[0], object_pairs_hook=dict)
        self.assertDictEqual(
            message,
            {
                "levelname": "INFO",
                "name": "test_formatter",
                "message": "Composed message with extra",
                **filtered_extra_dict
            },
        )

    def test_include_filter(self):
        self.log_and_assert(
            type_validators=[
                AttrTypeFilter({
                    'request': 'dict',
                    'unexistent': 'str',
                    'entry': bool,
                    'abc': ['bool', str, 'int', 'TestSubobject'],
                    'def': 'TestObject',
                    'ghi': 'TestObject',
                    'ghi2': 'tests.test_attr_type_filter.TestObject',
                    'jkl': ['bool', str, 'int', 'TestSubobject'],
                    'mno': 'TestSubobject'
                })
            ],
            extra_dict={
                'entry': 'hey',  #no match
                'abc': TestObject(),  #no match
                'def': TestObject(),  #match
                'ghi': TestSubobject(),  #match (checks that super class detection works)
                'ghi2': TestSubobject(),  #match
                'jkl': TestSubobject(),  #match
                'mno': TestObject(),  #no match
                'request': {  #match
                    'path': '/my/path', 'method': 'GET', 'comment': TestObject()
                }
            },
            filtered_extra_dict={
                "request": {
                    "path": '/my/path',
                    "method": "GET",
                    "comment": "Test Object"  #str() serializer is used if extra is not serializable
                },
                'def': 'Test Object',
                'ghi': 'Test Subobject',
                'ghi2': 'Test Subobject',
                'jkl': 'Test Subobject',
            }
        )

    def test_exclude_filter(self):
        self.log_and_assert(
            type_validators=[
                AttrTypeFilter(
                    is_blacklist=True,
                    typecheck_list={
                        'request': 'dict',
                        'unexistent': 'str',
                        'entry': bool,
                        'abc': ['bool', str, 'int'],
                    }
                )
            ],
            extra_dict={
                'entry': 'hey',  #no match
                'abc': TestObject(),  #no match
                'request': {  #match
                    'path': '/my/path', 'method': 'GET', 'comment': TestObject()
                }
            },
            filtered_extra_dict={
                'entry': 'hey', 'abc': 'Test Object'
            }
        )

    def test_include_and_exclude_filter(self):
        self.log_and_assert(
            type_validators=[
                AttrTypeFilter({
                    'entry': 'bool',
                    'entry3': 'int',
                    'request': 'builtins.dict',
                    'abc': 'tests.test_attr_type_filter.TestObject',
                    'unexistent': 'str',
                }),
                AttrTypeFilter(
                    is_blacklist=True,
                    typecheck_list={
                        'entry2': str,
                        'entry3': int,
                        'abc': [bool, str, int],
                        'nested': dict,
                    }
                )
            ],
            extra_dict={
                'entry': 'hey',  #no match, no filter => hidden
                'abc': TestObject(),  #no filter, no match => show
                "entry2": "hey2",  #no filter, match => hidden
                'request': {  #match, no filter => show
                    'path': '/my/path',
                    'scheme': 'https',
                },
                "entry3": "hey3",  #no match, no match => hidden
                'nested': {  #no filter, match => hidden
                    'param1': 'text1',
                    'param2': 'text2',
                }
            },
            filtered_extra_dict={
                'abc': 'Test Object', 'request': {
                    'path': '/my/path', 'scheme': 'https'
                }
            }
        )
