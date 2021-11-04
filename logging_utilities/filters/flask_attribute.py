import logging

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
            rec_attribute = 'flask_request_' + attribute
            value = ''
            if has_request_context():
                try:
                    value = getattr(request, attribute, '')
                except HTTPException:
                    # accessing the request.json might raise an HTTPException if the request
                    # is malformed for json data. In this case we don't want the filter to crash
                    # but simply set an empty value
                    if attribute == 'json':
                        value = str(request.data)
                    else:
                        value = ''
            if value is None or isinstance(value, (str, int, float, dict)):
                setattr(record, rec_attribute, value)
            elif isinstance(value, bytes):
                setattr(record, rec_attribute, value.decode('utf-8'))
            elif attribute == 'headers':
                setattr(record, rec_attribute, dict(value.items()))
            else:
                ValueError('Attribute %s=%s unsupported type' % (attribute, value))
        return True
