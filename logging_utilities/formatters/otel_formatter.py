import json

from logging_utilities.formatters.json_formatter import JsonFormatter
from logging_utilities.formatters.json_formatter import deep_merge
from logging_utilities.formatters.json_formatter import dictionary

# OTel log severity number mapping
# https://opentelemetry.io/docs/specs/otel/logs/data-model/#field-severitynumber
OTEL_SEVERITY_MAP = {
    "DEBUG": 5,
    "INFO": 9,
    "WARNING": 13,
    "ERROR": 17,
    "CRITICAL": 21,
}

DEFAULT_OTEL_FORMAT = dictionary([
    # OTEL semantic conventions (semconv) v1.40.0
    # https://opentelemetry.io/docs/specs/semconv/
    ("code.file.path", "pathname"),
    ("code.line.number", "lineno"),
    ("code.function.name", "funcName"),
    ("process.pid", "process"),
    ("thread.id", "thread"),
    # Custom attributes fields - not following OTEL semantic conventions
    ("event.category", "web"),
    ("event.duration", "duration"),
    ("event.kind", "event"),
    ("log.logger", "name"),
    ("service.type", "service_type"),
    # OTEL Log fields
    # https://opentelemetry.io/docs/specs/otel/logs/data-model/#log-and-event-record-definition
    ("body.string", "message"),
    ("otelSpanID", "otelSpanID"),
    ("otelTraceID", "otelTraceID"),
    ("severity_text", "levelname"),
    ("Timestamp", "utc_isotime"),
])


class OtelFormatter(JsonFormatter):
    """Logging formatter that emits JSON conforming to the OpenTelemetry log data model.

    Extends JsonFormatter with OTel-specific fields: Timestamp in nanoseconds,
    SeverityNumber mapping, TraceId/SpanId injection, and a Resource block.
    """

    def __init__(
        self,
        fmt=None,
        fmtFile=None,
        datefmt=None,
        style="%",
        add_always_extra=False,
        filter_attributes=None,
        remove_empty=True,
        ignore_missing=True,
        service_name=None,
        **kwargs,
    ):
        """OTel Formatter constructor

        Args:
            service_name: (string)
                Value for the Resource 'service.name' attribute. If None, falls back to
                whatever the fmt provides.
            All other args are forwarded to JsonFormatter.
        """
        if filter_attributes is None:
            filter_attributes = ["utc_isotime", "service_type"]

        # Merge order (later wins): DEFAULT_OTEL_FORMAT < fmtFile < fmt
        if fmtFile is not None:
            with open(fmtFile, "r", encoding="utf-8") as f:
                fmt_from_file = json.load(f, object_pairs_hook=dictionary)
            base = deep_merge(DEFAULT_OTEL_FORMAT, fmt_from_file)
        else:
            base = DEFAULT_OTEL_FORMAT

        fmt = deep_merge(base, fmt) if fmt is not None else base

        super().__init__(
            fmt=fmt,
            fmtFile=None,
            datefmt=datefmt,
            style=style,
            add_always_extra=add_always_extra,
            filter_attributes=filter_attributes,
            remove_empty=remove_empty,
            ignore_missing=ignore_missing,
            **kwargs,
        )

        self.service_name = service_name

    def format(self, record):
        # Enrich the record with computed OTel fields before JsonFormatter processes it
        if self.service_name is not None:
            record.service_name = self.service_name

        json_str = super().format(record)

        return json_str
