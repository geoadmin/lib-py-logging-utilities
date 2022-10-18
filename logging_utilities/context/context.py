import logging
from functools import wraps

from .thread_context import ThreadMappingContext

__record_factory_wrapped = None  # pylint: disable=invalid-name
__initial_record_factory = logging.getLogRecordFactory()
__context = None  # pylint: disable=invalid-name


def set_logging_context(context=None):
    '''Set a logging context

    The context is set per thread (each thread can have different context) and is set to every
    log record in the `context` attribute.

    Args:
        context: (dict, None)
            Context to set, by default `None`. The context can be later retrieved and modified using
            `get_logging_context()`
    '''
    global __record_factory_wrapped  # pylint: disable=global-statement, invalid-name
    global __context  # pylint: disable=global-statement, invalid-name
    current_factory = logging.getLogRecordFactory()
    if __context is None:
        __context = ThreadMappingContext()
    __context.init(context)
    if current_factory != __record_factory_wrapped:
        __initial_record_factory = logging.getLogRecordFactory()
        __record_factory_wrapped = __wrap_log_record_with_context(current_factory, __context)
        logging.setLogRecordFactory(__record_factory_wrapped)


def get_logging_context():
    '''Return the current logging context if set or `None` otherwise'''
    return __context


def remove_logging_context():
    '''Remove the logging context'''
    global __context  # pylint: disable=global-statement, invalid-name
    logging.setLogRecordFactory(__initial_record_factory)
    __context = None


def __wrap_log_record_with_context(record_factory, context):

    @wraps(record_factory)
    def wrapper(*args, **kwargs):
        record = record_factory(*args, **kwargs)
        record.context = context
        return record

    return wrapper
