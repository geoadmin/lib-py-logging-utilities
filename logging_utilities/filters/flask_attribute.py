import logging

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
                value = getattr(request, attribute, '')
            if value is None or isinstance(value, (str, int, float, dict)):
                setattr(record, rec_attribute, value)
            elif attribute == 'headers':
                setattr(record, rec_attribute, dict(value.items()))
            else:
                ValueError('Attribute %s=%s unsupported type' % (attribute, value))
        return True
