import unittest

from nose2.tools import params

from logging_utilities.formatters.json_formatter import EnhancedPercentStyle


class RegexTests(unittest.TestCase):

    @params(
        '%(asctime)s',
        '%(my.dotted.key)s',
        '%(my.dotted.key)s with constant',
        'leading constant %(my.dotted.key)s with constant',
        'constant%(my.dotted.key)sconstant',
        '%(my.dotted.key)d',
        '%(my.dotted.key)3.4d',
    )
    def test_json_formatter_enhanced_percent_style_regex_match(self, value):
        self.assertIsNotNone(EnhancedPercentStyle.validation_pattern.search(value))

    @params(
        'my.key',
        'my.key2',
        'my.',
        'k1.k3.',
        'k_1.',
        'k_.sk_2',
        '_my.key',
        '_1.',
        '_1._1',
        '_1a._2b._3b',
        'a.b.c.',
        'a1a.b2b.c2c.',
        'a1a_.b2_b.c_2c.',
        'my key.',
        '1.2',
        'This is a text. It contains dot.',
        'my.key ',
        ' my.key',
        'my.key-test',
        '1',
        '1.test',
        '_1.1test',
        '%()s',
        'asd %()s asdf'
    )
    def test_json_formatter_enhanced_percent_style_regex_not_match(self, value):
        self.assertIsNone(EnhancedPercentStyle.validation_pattern.search(value))
