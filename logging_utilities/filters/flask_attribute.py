import logging

from werkzeug.datastructures import ImmutableDict
from werkzeug.datastructures import ImmutableMultiDict
from werkzeug.datastructures import MultiDict
from werkzeug.exceptions import HTTPException

from flask import has_request_context
from flask import request


class FlaskRequestAttribute(logging.Filter):
    """Logging Flask attributes record

    This filter adds Flask request context attributes to the log record.

    Flask request attributes are added as record attributes with the 'flask_request_' prefix.
    """

    def __init__(self, attributes=None):
        """Initialize the filter

        Args:
            attributes: (list)
                Flask request attribute names list to add to the log record
        """
        super().__init__()
        self.attributes = attributes if attributes else list()

    def filter(self, record):
        for attribute in self.attributes:
            if has_request_context():
                rec_attribute = 'flask_request_' + attribute
                try:
                    value = getattr(request, attribute)
                except HTTPException:
                    # accessing the request.json might raise an HTTPException if the request
                    # is malformed for json data. In this case we don't want the filter to crash
                    # but simply set an empty value
                    if attribute == 'json':
                        if isinstance(request.data, bytes):
                            value = request.data.decode('utf-8')
                        else:
                            value = str(request.data)
                    else:
                        raise
                # Accessing flask_request_view_args.<key> might rise an exception if
                # flask_request_view_args is Null. To safely access flask_request_view_args
                # None is replaced by an empty dict.
                if attribute == 'view_args' and value is None:
                    setattr(record, rec_attribute, {})
                elif isinstance(value, (ImmutableDict, ImmutableMultiDict, MultiDict)):
                    setattr(record, rec_attribute, dict(value))
                elif value is None or isinstance(value, (str, int, float, dict, list)):
                    setattr(record, rec_attribute, value)
                elif isinstance(value, bytes):
                    setattr(record, rec_attribute, value.decode('utf-8'))
                elif attribute == 'headers':
                    setattr(record, rec_attribute, dict(value.items()))
                else:
                    raise ValueError('Attribute %s=%s unsupported type' % (attribute, value))
        return True
