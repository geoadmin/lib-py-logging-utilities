from functools import partial
from logging import LogRecord
from logging import setLogRecordFactory

_dict_ignore_missing_types = {}


class _DictIgnoreMissing(dict):
    _dft_value = ''

    def __getitem__(self, __k):
        try:
            return super().__getitem__(__k)
        except KeyError:
            return self._dft_value


class LogRecordIgnoreMissing(LogRecord):
    '''LogRecord that don't raise ValueError exception when trying to access missing extra attribute

    Missing/unknown extra attribute will returns `''` when accessed via the `__dict__` attribute.

    This is particularly usefull when using a style formatter with attribute that might be missing
    from the log record; e.g. `"%(message)s - %(extra_attribute)s"`

    The default value for missing attribute can be changed via `__dft_value` parameter.
    '''

    def __init__(self, *args, **kwargs):
        __dft_value = kwargs.pop('__dft_value', '')
        __dft_value_hash = str(__dft_value)
        super().__init__(*args, **kwargs)
        if __dft_value_hash not in _dict_ignore_missing_types:
            _dict_ignore_missing_type_name = '_DictIgnoreMissing_{}'.format(
                len(_dict_ignore_missing_types)
            )
            _dict_ignore_missing_types[__dft_value_hash] = type(
                _dict_ignore_missing_type_name, (_DictIgnoreMissing,), {"_dft_value": __dft_value}
            )
        self.__dict__ = _dict_ignore_missing_types[__dft_value_hash](self.__dict__)


def set_log_record_ignore_missing_factory(dft_value=''):
    '''Globally change the log record factory to the LogRecordIgnoreMissing factory

    This new log record won't raise any exception on unknown/missing attribute access, but will
    return the `dft_value` instead.
    '''
    setLogRecordFactory(partial(LogRecordIgnoreMissing, __dft_value=dft_value))


def reset_log_record_factory():
    '''Reset the log record factory to the original one LogRecord.
    '''
    setLogRecordFactory(LogRecord)  # pragma: no cover
