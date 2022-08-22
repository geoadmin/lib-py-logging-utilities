import unittest

from nose2.tools import params

from logging_utilities.formatters.json_formatter import dotted_key_regex


class RegexTests(unittest.TestCase):

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
        'a1a_.b2_b.c_2c.'
    )
    def test_json_formatter_dotted_key_regex_match(self, key):
        self.assertIsNotNone(dotted_key_regex.match(key))

    @params(
        'my key.',
        '1.2',
        'This is a text. It contains dot.',
        'my.key ',
        ' my.key',
        'my.key-test',
        '1',
        '1.test',
        '_1.1test'
    )
    def test_json_formatter_dotted_key_regex_no_match(self, key):
        self.assertIsNone(dotted_key_regex.match(key))
