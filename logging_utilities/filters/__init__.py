import logging
from datetime import datetime, timezone


class ConstAttribute(logging.Filter):
    '''Logging constant record attribute

    This filter add a constant attribute to the log record.
    '''

    def __init__(self, **kwargs):
        '''Initialize filter

        Args:
            kwargs:
                All keyword arguments are added as LogRecord attributes
        '''
        self.kwargs = kwargs
        super().__init__()

    def filter(self, record):
        for key, value in self.kwargs.items():
            setattr(record, key, value)
        return True


class LevelFilter(logging.Filter):
    '''Logging level filter

    This filter can be used on a handler to filter logger message based on their level.

    For example if you have two DEBUG loggers; A and B, with both two handlers; console and file.
    On the file handler you want all message of A but only WARNING message of B. You can then use
    the following configuration:

    root:
        handlers:
            - "console"
            - "file"
        level: "DEBUG"
        propagate: "True"

    filters:
        BFilter:
            class: logging_utilities.filters.LevelFilter
            level: "WARNING"
            logger: 'B'

    loggers:
        A:
            level: "DEBUG"
        B:
            level: "DEBUG"

    handlers:
        console:
            class: "logging.StreamHandler"

        file:
            class: "logging.handlers.RotatingFileHandler"
            filters:
                - "BFilter"
    '''

    def __init__(self, level='DEBUG', logger=''):
        '''Initialize the filter

        Args:
            level: (str|int)
                Level to filter, all message with a lower level will be filtered
            logger: (str)
                Logger name on which to apply the level filtering, if empty then the filtering is
                applied to all loggers

        Raises:
            ValueError: when an invalid level is given
        '''
        if not isinstance(level, (str, int)):
            raise ValueError('Unsupported level type: must be int or string')
        self.level = level
        if isinstance(self.level, str):
            # translate level to int
            self.level = logging.getLevelName(self.level)
            if not isinstance(self.level, int):
                raise ValueError('Unsupported level string')
        elif isinstance(self.level, int) \
            and logging.getLevelName(self.level) == "Level %d" % (self.level):
            raise ValueError('Undefined level integer')

        self.logger = logger
        super().__init__()

    def filter(self, record):
        if self.logger == '' or record.name.startswith(self.logger):
            if record.levelno < self.level:
                return False
        return True


class TimeAttribute(logging.Filter):
    '''Logging time record attribute

    This filter can be used on a handler to add iso 8601 time attribute to the record.
    '''

    def __init__(self, isotime=True, utc_isotime=False):
        '''Initialize the filter

        Args:
            isotime: (bool)
                Add local time in `YYYY-MM-DDThh:mm:ss±hh:mm` format as `isotime`
                attribute to LogRecord
            utc_isotime: (bool)
                Add utc time in `YYYY-MM-DDThh:mm:ss±hh:mm` format as `utc_isotime`
                attribute to LogRecord
        '''
        self.isotime = isotime
        self.utc_isotime = utc_isotime
        super().__init__()

    def filter(self, record):
        if self.isotime:
            record.isotime = datetime.fromtimestamp(record.created).astimezone().isoformat()
        if self.utc_isotime:
            record.utc_isotime = datetime.fromtimestamp(record.created, tz=timezone.utc) \
                .isoformat().replace('+00:00', 'Z')
        return True
