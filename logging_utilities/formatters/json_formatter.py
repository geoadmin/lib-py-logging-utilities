import json
import logging
import logging.config
import re
import sys
import warnings
from collections import OrderedDict
from collections.abc import Mapping
from collections.abc import MutableMapping
from functools import partial
from logging import BASIC_FORMAT
from logging import PercentStyle as _PercentStyle
from logging import StrFormatStyle as _StrFormatStyle
from logging import StringTemplateStyle as _StringTemplateStyle

from logging_utilities.formatters import RECORD_DFT_ATTR
from logging_utilities.log_record import _DictIgnoreMissing
from logging_utilities.log_record import set_log_record_ignore_missing_factory

if sys.version_info.major < 3:
    raise ImportError('Only python 3 is supported')  # pragma: no cover

# From python3.7, dict is ordered. Ordered dict are preferred in order to keep the json output
# in the same order as its definition
if sys.version_info.major >= 3 and sys.version_info.minor >= 7:
    dictionary = dict
else:
    dictionary = OrderedDict  # pragma: no cover

DEFAULT_FORMAT = dictionary([('levelname', 'levelname'), ('name', 'name'), ('message', 'message')])


def _flatten_dict_gen(dct, parent_key, sep):
    for key, value in dct.items():
        new_key = parent_key + sep + key if parent_key else key
        if isinstance(value, MutableMapping):
            yield from flatten_dict(value, new_key, sep=sep).items()
        else:
            yield new_key, value


def flatten_dict(dct, parent_key='', sep='.'):
    return dict(_flatten_dict_gen(dct, parent_key, sep))


def is_style_format_valid(style):
    try:
        style.validate()
        return True
    except ValueError:
        return False


if sys.version_info.major >= 3 and sys.version_info.minor > 7:
    StrFormatStyle = _StrFormatStyle
    StringTemplateStyle = _StringTemplateStyle
    PercentStyle = _PercentStyle
else:
    # pragma: no cover
    # Python version prior 3.8 don't have a validate() method on the Style class.
    class ValidateStyleMixin():

        def validate(self):
            if not self.validation_pattern.search(self._fmt):
                raise ValueError(
                    "Invalid format '%s' for '%s' style" % (self._fmt, self.default_format[0])
                )

    class PercentStyle(_PercentStyle, ValidateStyleMixin):
        validation_pattern = re.compile(
            r'%\(\w+\)[#0+ -]*(\*|\d+)?(\.(\*|\d+))?[diouxefgcrsa%]', re.I
        )

    class StrFormatStyle(_StrFormatStyle, ValidateStyleMixin):
        validation_pattern = re.compile(
            r'{[a-z_]\w*(![rsa])?(:[#0+ -]*(\*|\d+)?(\.(\*|\d+))?[diouxefgcrsa%])?}', re.I
        )

    class StringTemplateStyle(_StringTemplateStyle, ValidateStyleMixin):
        validation_pattern = re.compile(r'{[a-z_]\w*}', re.I)


class EnhancedPercentStyle(PercentStyle):
    validation_pattern = re.compile(
        r'%\([\w\.]+\)[#0+ -]*(\*|\d+)?(\.(\*|\d+))?[diouxefgcrsa%]', re.I
    )

    def __init__(self, fmt, ignore_missing=False):
        super().__init__(fmt)
        self.ignore_missing = ignore_missing

    def _format(self, record):
        dct = {**record.__dict__, **flatten_dict(record.__dict__)}
        if self.ignore_missing:
            return self._fmt % _DictIgnoreMissing(dct)
        return self._fmt % dct


_ENHANCED_STYLES = {
    '%': (EnhancedPercentStyle, BASIC_FORMAT),
    '{': (StrFormatStyle, '{levelname}:{name}:{message}'),
    '$': (StringTemplateStyle, '${levelname}:${name}:${message}'),
}


class JsonFormatter(logging.Formatter):
    """Logging JSON Formatter

    This formatter transform the log message into a JSON object.
    """

    def __init__(
        self,
        fmt=None,
        datefmt=None,
        style='%',
        add_always_extra=False,
        filter_attributes=None,
        remove_empty=False,
        ignore_missing=False,
        **kwargs
    ):
        """JSON Formatter constructor

        Args:
            fmt: (dict)
                Format for the json output. It can be a string representing a json object or
                a dictionary. The object defines the JSON output:
                    KEY   := key to use in the json output
                    VALUE := value to use in the json output, this can be either a static string,
                             a record attribute name or a format string
            datefmt: (string)
                Format string for the date format
            style: (string)
                Use a style parameter of '%', '{' or '$' to specify that you want to use one of
                %-formatting, :meth:`str.format` (``{}``) formatting or :class:`string.Template`
                formatting in your format string.
            add_always_extra: (bool)
                If true the extra dictionary passed to the log function will be always
                added to the json output. Otherwise it is only added if the keys are in the
                fmt.
            filter_attributes: (list)
                List of record attributes added by a filter or log addapter.
                This list is used to differentiate record attributes from log extra
                attributes.
            remove_empty: (bool)
                If true the empty list, object or string in the output message are removed
            ignore_missing: (bool)
                If True, then all extra attributes from the log record that are missing (accessed
                by the fmt parameter) will be replaced by an empty string instead of raising a
                ValueError exception.
                NOTE: This has an impact on all formater not only on this one,
                see log_record.LogRecordIgnoreMissing.
            kwargs:
                Additional parameters passed to json.dumps().

        Raises:
            TypeError:  When the fmt parameter is in a wrong type
            json.decoder.JSONDecodeError: When fmt is a string that don't describe a json object
        """
        super().__init__(datefmt=datefmt, style=style)

        if fmt is None:
            fmt = DEFAULT_FORMAT
        if style == '%':
            self._style_constructor = partial(
                _ENHANCED_STYLES[style][0], ignore_missing=ignore_missing
            )
        else:
            self._style_constructor = _ENHANCED_STYLES[style][0]
        self._use_time = str(fmt).find('asctime') >= 0
        self.json_fmt = self._parse_fmt(fmt)
        self.add_always_extra = add_always_extra
        self.filter_attributes = filter_attributes
        self.remove_empty = remove_empty

        # support for `json.dumps` parameters
        self.kwargs = kwargs

        self.ignore_missing = ignore_missing
        if ignore_missing:
            set_log_record_ignore_missing_factory()

    @classmethod
    def _parse_fmt(cls, fmt):
        if isinstance(fmt, str):
            return json.loads(fmt, object_pairs_hook=dictionary)
        if isinstance(fmt, (dictionary, OrderedDict)):
            return fmt
        if isinstance(fmt, dict):  # pragma no cover
            warnings.warn(
                "Current python version is lower than 3.7.0, the key's order of dict may be "
                "different than the definition, please use `OrderedDict` instead.",
                UserWarning
            )
            return dictionary((k, fmt[k]) for k in sorted(fmt.keys()))

        raise TypeError(
            '`{}` type is not supported, `fmt` must be json `str`, `OrderedDict` or `dict` type.'.
            format(type(fmt))
        )  # pragma: no cover

    @classmethod
    def _add_extra_to_message(cls, extra, message):
        for key, value in extra.items():
            message[key] = value

    def _get_extra_attrs(self, record):

        def is_extra_attribute(attr):
            if attr not in RECORD_DFT_ATTR and (
                self.filter_attributes is None or attr not in self.filter_attributes
            ):
                return True
            return False

        extras = {key: record.__dict__[key] for key in record.__dict__ if is_extra_attribute(key)}
        if sys.version_info.major >= 3 and sys.version_info.minor >= 7:
            return extras
        return dictionary((key, extras[key]) for key in sorted(extras.keys()))  # pragma no cover

    def _add_list_to_message(self, record, lst, message):
        for value in lst:
            if isinstance(value, (dict, OrderedDict)):
                intermediate_msg = dictionary()
                self._add_object_to_message(record, value, intermediate_msg)
                if not self.remove_empty or len(intermediate_msg) > 0:
                    message.append(intermediate_msg)
            elif isinstance(value, list):
                intermediate_msg = list()
                self._add_list_to_message(record, value, intermediate_msg)
                if not self.remove_empty or len(intermediate_msg) > 0:
                    message.append(intermediate_msg)
            elif value == 'exc_info':
                # exc_info might be true or contain exception info. We add it here only a boolean to
                # know if the message has exception info or not. The info itself will be in
                # 'exc_text' and is always appended to the json output when not available
                message.append(bool(record.exc_info))
            elif value in record.__dict__:
                intermediate_msg = getattr(record, value, None)
                if not self.remove_empty or intermediate_msg is not None:
                    message.append(intermediate_msg)
            elif isinstance(value, str):
                intermediate_msg = self._get_string_key_value(record, value)
                if self.remove_empty and not intermediate_msg:
                    pass
                else:
                    message.append(intermediate_msg)
            else:
                raise ValueError(
                    'Invalid value type={} for value={} in fmt'.format(type(value), value)
                )  # pragma no cover

    def _add_object_to_message(self, record, obj, message):
        for key, value in obj.items():
            if isinstance(value, (dict, OrderedDict)):
                message[key] = dictionary()
                self._add_object_to_message(record, value, message[key])
                if self.remove_empty and len(message[key]) == 0:
                    del message[key]
            elif isinstance(value, list):
                message[key] = list()
                self._add_list_to_message(record, value, message[key])
                if self.remove_empty and len(message[key]) == 0:
                    del message[key]
            elif value == 'exc_info':
                # exc_info might be true or contain exception info. We add it here only a boolean to
                # know if the message has exception info or not. The info itself will be in
                # 'exc_text' and is always appended to the json output when not available
                message[key] = bool(record.exc_info)
            elif value in record.__dict__:
                message[key] = getattr(record, value, '')
                if self.remove_empty and message[key] == '':
                    del message[key]
            elif isinstance(value, str):
                message[key] = self._get_string_key_value(record, value)
                if self.remove_empty and not message[key]:
                    del message[key]
            else:
                raise ValueError(
                    'Invalid value type={} for value={} in fmt'.format(type(value), value)
                )  # pragma no cover

    def _get_dotted_key_value(self, record, str_value):
        default_value = ''
        if str_value.endswith('..'):
            # if the dotted key has two trailing dot, this means that the value must be a list
            # therefore set the default value to an empty list
            default_value = []
        elif str_value.endswith('.'):
            # if the dotted key has a trailing dot, this mean that the value must be a dict
            # therefore set the default value to an empty dictionary.
            default_value = dictionary()

        def get_dotted_key(dct, dotted_key):
            if not isinstance(dct, (Mapping)):
                raise ValueError(
                    'Cannot get dotted key "{}" from "{}": '.format(dotted_key, dct) +
                    'is not a record or dictionary'
                )  # pragma: no cover
            key = dotted_key
            next_dotted_key = None
            if '.' in dotted_key:
                key, next_dotted_key = dotted_key.split('.', maxsplit=1)
                if next_dotted_key not in ['', '.']:
                    return get_dotted_key(dct.get(key, dictionary()), next_dotted_key)
            if self.ignore_missing:
                return dct.get(key, default_value)
            try:
                return dct[key]
            except KeyError as error:
                raise ValueError('Key "{}" not found in log record'.format(key)) from error

        return get_dotted_key(record.__dict__, str_value)

    def _get_string_key_value(self, record, value):
        style = self._style_constructor(value)

        if is_style_format_valid(style):
            # The value contains a valid style formatting (e.g. %(asctime)s)
            # therefore use the style formatter.
            return style.format(record)

        # Otherwise try to get a dotted key from the record
        return self._get_dotted_key_value(record, value)

    def usesTime(self):
        """
        Check if the format uses the creation time of the record.
        """
        return self._use_time

    def formatMessage(self, record):
        message = dictionary()
        self._add_object_to_message(record, self.json_fmt, message)
        return message

    def format(self, record):
        record.message = record.getMessage()
        if self.usesTime():
            record.asctime = self.formatTime(record, self.datefmt)

        if self.add_always_extra:
            extra = self._get_extra_attrs(record)

        message = self.formatMessage(record)

        if self.add_always_extra:
            self._add_extra_to_message(extra, message)

        if record.exc_info:
            # Cache the traceback text to avoid converting it multiple times
            # (it's constant anyway)
            if not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            message['exc_text'] = record.exc_text

        if record.stack_info:
            message['stack_info'] = self.formatStack(record.stack_info)

        # When adding all extras, to avoid crash when a log message adds an extra with a non
        # serializable object, we add a default serializer.
        default = self.kwargs.pop('default', None)
        if self.add_always_extra and default is None:
            default = str

        return json.dumps(message, default=default, **self.kwargs)


def basic_config(**kwargs):  # pragma: no cover
    """
    Do basic configuration for the logging system.

    This function does nothing if the root logger already has handlers
    configured. It is a convenience method intended for use by simple scripts
    to do one-shot configuration of the logging package.

    The default behavior is to create a StreamHandler which writes to
    sys.stderr, set a formatter using the BASIC_FORMAT format string, and
    add the handler to the root logger.

    A number of optional keyword arguments may be specified, which can alter
    the default behavior.

    Args:
        filename:
            Specifies that a FileHandler be created, using the specified filename,
            rather than a StreamHandler.
        filemode:
            Specifies the mode to open the file, if filename is specified
            (if filemode is unspecified, it defaults to 'a').
        format:
            Use the specified format string for the handler.
        datefmt:
            Use the specified date/time format.
        style:
            If a format string is specified, use this to specify the
            type of format string (possible values '%', '{', '$', for
            %-formatting, :meth:`str.format` and :class:`string.Template`
            - defaults to '%').
        level:
            Set the root logger level to the specified level.
        stream:
            Use the specified stream to initialize the StreamHandler. Note
            that this argument is incompatible with 'filename' - if both
            are present, 'stream' is ignored.
        handlers:
            If specified, this should be an iterable of already created
            handlers, which will be added to the root handler. Any handler
            in the list which does not have a formatter assigned will be
            assigned the formatter created in this function.

    Note that you could specify a stream created using open(filename, mode)
    rather than passing the filename and mode in. However, it should be
    remembered that StreamHandler does not close its stream (since it may be
    using sys.stdout or sys.stderr), whereas FileHandler closes its stream
    when the handler is closed.
    """
    # Add thread safety in case someone mistakenly calls
    # basic_config() from multiple threads
    # pylint: disable=protected-access
    logging._acquireLock()
    try:
        if len(logging.root.handlers) > 0:
            return

        handlers = kwargs.pop("handlers", None)
        if handlers is None:
            if "stream" in kwargs and "filename" in kwargs:
                raise ValueError("'stream' and 'filename' should not be specified together")
        else:
            if "stream" in kwargs or "filename" in kwargs:
                raise ValueError(
                    "'stream' or 'filename' should not be specified together with 'handlers'"
                )
        if handlers is None:
            filename = kwargs.pop("filename", None)
            mode = kwargs.pop("filemode", 'a')
            if filename:
                handler = logging.FileHandler(filename, mode)
            else:
                stream = kwargs.pop("stream", None)
                handler = logging.StreamHandler(stream)
            handlers = [handler]
        dfs = kwargs.pop("datefmt", None)
        style = kwargs.pop("style", '%')
        if style not in logging._STYLES:
            raise ValueError('Style must be one of: %s' % ','.join(logging._STYLES.keys()))
        fmt = kwargs.pop("format", DEFAULT_FORMAT)
        formatter = JsonFormatter(fmt, dfs, style)
        for handler in handlers:
            if handler.formatter is None:
                handler.setFormatter(formatter)
            logging.root.addHandler(handler)
        level = kwargs.pop("level", None)
        if level is not None:
            logging.root.setLevel(level)
        if kwargs:
            keys = ', '.join(kwargs.keys())
            raise ValueError('Unrecognized argument(s): %s' % keys)
    finally:
        logging._releaseLock()
