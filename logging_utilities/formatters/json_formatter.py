import json
import logging
import logging.config
import sys
import warnings
from collections import OrderedDict

from logging_utilities.formatters import RECORD_DFT_ATTR

if sys.version_info < (3, 0):
    raise ImportError('Only python 3 is supported')

# From python3.7, dict is ordered. Ordered dict are preferred in order to keep the json output
# in the same order as its definition
if sys.version_info >= (3, 7):
    dictionary = dict
else:
    dictionary = OrderedDict

DEFAULT_FORMAT = dictionary([('levelname', 'levelname'), ('name', 'name'), ('message', 'message')])


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
            kwargs:
                Additional parameters passed to json.dumps()

        Raises:
            TypeError:  When the fmt parameter is in a wrong type
            json.decoder.JSONDecodeError: When fmt is a string that don't describe a json object
        """
        super().__init__(fmt='', datefmt=datefmt, style=style)

        self.json_fmt = self._parse_fmt(fmt)
        self.add_always_extra = add_always_extra
        self.filter_attributes = filter_attributes
        self.remove_empty = remove_empty

        # support for `json.dumps` parameters
        self.kwargs = kwargs

    @classmethod
    def _parse_fmt(cls, fmt):
        if isinstance(fmt, str):
            return json.loads(fmt, object_pairs_hook=dictionary)
        if isinstance(fmt, (dictionary, OrderedDict)):
            return fmt
        if isinstance(fmt, dict):
            warnings.warn(
                "Current python version is lower than 3.7.0, the key's order of dict may be "
                "different than the definition, please use `OrderedDict` instead.",
                UserWarning
            )
            return dictionary((k, fmt[k]) for k in sorted(fmt.keys()))
        if fmt is None:
            return DEFAULT_FORMAT

        raise TypeError(
            '`{}` type is not supported, `fmt` must be json `str`, `OrderedDict` or `dict` type.'.
            format(type(fmt))
        )

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
        if sys.version_info >= (3, 7):
            return extras
        return dictionary((key, extras[key]) for key in sorted(extras.keys()))

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
                # When the value is a string it can contain formatting strings (e.g. "%(asctime)s")
                # therefore try to format it.
                self._style._fmt = value  # pylint: disable=protected-access
                intermediate_msg = super().formatMessage(record)
                if not self.remove_empty or intermediate_msg != '':
                    message.append(intermediate_msg)

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
                # When the value is a string it can contain formatting strings (e.g. "%(asctime)s")
                # therefore try to format it.
                self._style._fmt = value  # pylint: disable=protected-access
                message[key] = super().formatMessage(record)
                if self.remove_empty and message[key] == '':
                    del message[key]

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


def basic_config(**kwargs):
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
