import logging
import logging.config
import re
import sys
from pprint import pformat

from logging_utilities.formatters import RECORD_DFT_ATTR

if sys.version_info < (3, 2):
    raise ImportError('Only python 3.2 and above are supported')

# parse the format to retrieve all key e.g. "%(message)s %(module)s" => ['message', 'module']
KEYS_PATTERN = r'%\((\w+)\)[#0\- \+]?(?:\d+|\*)?(?:\.\d+|\.\*)?\d*[diouxXeEfFgGcrsa]'


class ExtraFormatter(logging.Formatter):
    """Logging Extra Formatter

    This formatter enhance the python standard formatter to allow working with the log `extra`.
    The python standard formatter will raise a ValueError() when adding extra keyword in the format
    when this keyword is then missing from log record. This means that if you want to display a log
    extra, you have to make sure that every log message contains this extra.

    This formatter allow you to provide an `extra_fmt` parameter that will add record extra to the
    log message when available. You can either add the entire extra dictionary: `extra_fmt='%s'` or
    only some extras: `extra_fmt='%(extra1)s:%(extra2)s'`. In the latest case, when a key is missing
    in extra, the value is replaced by `extra_default`.
    When using the whole `extra` dictionary, you can use `extra_pretty_print` to improve the
    formatting, note that in this case the log might be on multiline (this use pprint.pformat).
    """

    def __init__(
        self,
        fmt=None,
        datefmt=None,
        style='%',
        validate=True,
        extra_fmt=None,
        extra_default='',
        extra_pretty_print=False,
        pretty_print_kwargs=None
    ):
        '''
        Initialize the formatter with specified format strings.

        Initialize the formatter either with the specified format string, or a default as described
        in logging.Formatter.

        Args:
            extra_fmt: string
                String format (old percent style only) for log extras. This can be used for instance
                to automatically add all extras, e.g: `extra_fmt='extras=%s'` or to add only some
                extra: `extra_fmt='%(extra1)s:%(extra2)s'`
            extra_default: any
                Default value to use for missing extra in record
            extra_pretty_print: boolean
                Set to true to use pprint.pformat on the extra dictionary
        '''
        super().__init__(fmt=fmt, datefmt=datefmt, style=style)
        self._fmt_keys = re.findall(KEYS_PATTERN, fmt)
        self.extra_fmt = extra_fmt
        self._extras_keys = re.findall(KEYS_PATTERN, self.extra_fmt if self.extra_fmt else '')
        self._default = extra_default
        self._extra_pretty_print = extra_pretty_print
        self._pretty_print_kwargs = pretty_print_kwargs if pretty_print_kwargs is not None else {}

    def formatMessage(self, record):
        message = self._style.format(record)
        if self.extra_fmt:
            extra_keys = set(record.__dict__.keys()) - RECORD_DFT_ATTR - set(self._fmt_keys)
            extras = {key: getattr(record, key) for key in extra_keys}
            if extras:
                missing_keys = set(self._extras_keys) - set(extras.keys())
                extras.update({key: self._default for key in missing_keys})
                if self._extra_pretty_print:
                    try:
                        message = '%s%s' % (
                            message, self.extra_fmt % pformat(extras, **self._pretty_print_kwargs)
                        )
                    except TypeError as err:
                        if err.args[0] == 'format requires a mapping':
                            raise ValueError(
                                'Cannot use extra_pretty_print with named placeholder'
                            ) from err
                        raise err
                else:
                    message = '%s%s' % (message, self.extra_fmt % extras)
        return message
