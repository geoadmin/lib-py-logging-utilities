import logging
import re
import sys
import warnings
from collections import OrderedDict

from django.http import HttpRequest

# From python3.7, dict is ordered. Ordered dict are preferred in order to keep the json output
# in the same order as its definition
if sys.version_info.major >= 3 and sys.version_info.minor >= 7:
    dictionary = dict
else:
    dictionary = OrderedDict


def _pattern(text):
    return r'^{}\b'.format(text.replace('.', '[.]'))


class JsonDjangoRequest(logging.Filter):
    """Convert Django request to a json object

    This filter recursively converts a django HttpRequest object to a python dictionary that can be
    dumped into a json string. This is useful for example if you want to log an extra parameter of
    type HttpRequest with the JSON formatter. If the specified attribute is not of type HttpRequest,
    it will simply be ignored and passed through.

    Additionally the attributes of the request that needs to be jsonify can be configured using the
    `include_keys` and/or `exclude_keys` parameters.

    The django framework adds sometimes an HttpRequest or socket object under "record.request" when
    logging. So if you decide to use the attribute name "request" for this filter, beware that you
    will need to handle the case where the attribute is of type 'socket' separately, for example by
    filtering it out using the attribute type filter. (see example in README)
    """

    def __init__(self, include_keys=None, exclude_keys=None, attr_name='http_request'):
        """Initialize the filter

        Args:
            include_keys: (list | None)
                All request attributes that match any of the dotted keys of the list will be added
                to the jsonifiable object. When None then all attributes are added
                (default behavior).
            exclude_keys: (list | None)
                All request attributes that match any of the dotted keys of the list will not be
                added to the jsonifiable object. NOTE this has precedence to include_keys
                which means that if a key is in both lists, then it is not added.
            attr_name: str
                The name of the attribute that stores the HttpRequest object. The default is
                'http_request'.
                (Note that django sometimes stores an "HttpRequest" under the attribute "request".
                This is however not the default as django also stores other types of objects under
                this attribute name.)
        """
        self.include_keys = include_keys
        self.exclude_keys = exclude_keys
        self.attr_name = attr_name
        super().__init__()

    def filter(self, record):
        if not hasattr(record, self.attr_name):
            return True

        self._jsonify_request(record)

        return True

    def _jsonify_request(self, record):
        orig_request = getattr(record, self.attr_name)
        if isinstance(orig_request, HttpRequest) and hasattr(orig_request, '__dict__'):
            request = self._jsonify_dict(self.attr_name, orig_request.__dict__)
            if self._add_key(self.attr_name + '.headers', 'headers'):
                # HttpRequest has a special headers property that is cached and is not always in
                # record.http_request.__dict__
                request['headers'] = self._jsonify_dict(
                    self.attr_name + '.headers', orig_request.headers
                )
            setattr(record, self.attr_name, request)

    def _jsonify_dict(self, prefix, dct):
        json_obj = dictionary()
        if sys.version_info.major < 3 and sys.version_info.minor < 7:
            dct = OrderedDict(sorted(dct.items(), key=lambda t: t[0]))
        for key, value in dct.items():
            dotted_key = '{}.{}'.format(prefix, key)
            if not self._add_key(dotted_key, key):
                continue
            if hasattr(value, '__dict__'):
                json_obj[key] = self._jsonify_dict(dotted_key, value.__dict__)
            elif isinstance(value, dict):
                json_obj[key] = self._jsonify_dict(dotted_key, value)
            elif isinstance(value, (str, int, float, type(None), bool, tuple, list)):
                json_obj[key] = value
            elif isinstance(value, (bytes)):
                json_obj[key] = str(value)
            else:
                warnings.warn(
                    "Cannot jsonify key {} with value {}: unsupported type={}".format(
                        dotted_key, value, type(value)
                    )
                )
                json_obj[key] = str(value)
        return json_obj

    def _add_key(self, dotted_key, key):
        return self._include_key(dotted_key, key) and not self._exclude_key(dotted_key, key)

    def _include_key(self, dotted_key, key):
        if self.include_keys is None:
            # if no include_keys is configured add all keys except for private
            if key.startswith('_'):
                return False
            return True

        def match(item):
            return (
                re.match(_pattern(dotted_key), item) or
                (re.match(_pattern(item), dotted_key) and not key.startswith('_'))
            )

        return any(map(match, self.include_keys))

    def _exclude_key(self, dotted_key, key):
        if self.exclude_keys is None:
            # if no exclude_keys is configured only exclude private key
            if key.startswith('_'):
                return True
            return False

        def match(item):
            return re.match(_pattern(item), dotted_key)

        return any(map(match, self.exclude_keys))
