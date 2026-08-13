from logging import LogRecord
from logging import getLogRecordFactory
from logging import setLogRecordFactory

_dict_ignore_missing_types = {}


class _DictIgnoreMissing(dict):
    _dft_value = ''

    def __getitem__(self, __k):
        try:
            return super().__getitem__(__k)
        except KeyError:
            return self._dft_value


def get_or_create_dict_ignore_missing_type(dft_value):
    '''Get or the _DictIgnoreMissing type with the given default value. Create a new one if not
    already existing.

    '''
    dft_value_hash = str(dft_value)
    if dft_value_hash not in _dict_ignore_missing_types:
        _dict_ignore_missing_type_name = '_DictIgnoreMissing_{}'.format(
            len(_dict_ignore_missing_types)
        )
        _dict_ignore_missing_types[dft_value_hash] = type(
            _dict_ignore_missing_type_name, (_DictIgnoreMissing,), {"_dft_value": dft_value}
        )

    return _dict_ignore_missing_types[dft_value_hash]


class LogRecordIgnoreMissing(LogRecord):
    '''LogRecord that don't raise ValueError exception when trying to access missing extra attribute

    Missing/unknown extra attribute will returns `''` when accessed via the `__dict__` attribute.

    This is particularly usefull when using a style formatter with attribute that might be missing
    from the log record; e.g. `"%(message)s - %(extra_attribute)s"`

    The default value for missing attribute can be changed via `__dft_value` parameter.
    '''

    def __init__(self, *args, **kwargs):
        __dft_value = kwargs.pop('__dft_value', '')
        super().__init__(*args, **kwargs)
        self.__dict__ = get_or_create_dict_ignore_missing_type(__dft_value)(self.__dict__)


def set_log_record_ignore_missing_factory(dft_value=''):
    '''Change the log record factory to not raise exception on unknown/missing attribute access, but
    rather to return the `dft_value` instead.
    '''
    original_factory = getLogRecordFactory()

    def record_factory(*args, **kwargs):
        record = original_factory(*args, **kwargs)
        record.__dict__ = get_or_create_dict_ignore_missing_type(dft_value)(record.__dict__)
        return record

    setLogRecordFactory(record_factory)


def reset_log_record_factory():
    '''Reset the log record factory to the original one LogRecord.

    Use this with caution! A common python logging pattern is to chain different factories together.
    By resetting the factory to the one before set_log_record_ignore_missing_factory, you might
    break the chain of factories by cutting off all factories that have been added after
    set_log_record_ignore_missing_factory.
    '''
    setLogRecordFactory(LogRecord)  # pragma: no cover
