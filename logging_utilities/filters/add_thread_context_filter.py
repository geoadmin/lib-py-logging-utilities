import logging
from logging import LogRecord
from typing import List

from logging_utilities.thread_context import thread_context


class AddThreadContextFilter(logging.Filter):
    """Add local thread attributes to the log record.
    """

    def __init__(self, contexts: List[dict] = None) -> None:
        """Initialize the filter

        Args:
            contexts (List[dict], optional):
                List of values to add to the log record. Dictionary must contain value for
                'context_key' to read value from thread local variable. Dictionary must also contain
                'logger_key' to set the value on the log record.
        """
        self.contexts: List[dict] = [] if contexts is None else contexts
        super().__init__()

    def filter(self, record: LogRecord) -> bool:
        for ctx in self.contexts:
            if getattr(thread_context, ctx['context_key'], None) is not None:
                setattr(record, ctx['logger_key'], getattr(thread_context, ctx['context_key']))
        return True
