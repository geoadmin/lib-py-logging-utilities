# Python logging utilities

![Build Status](https://codebuild.eu-central-1.amazonaws.com/badges?uuid=eyJlbmNyeXB0ZWREYXRhIjoiTGJzNVpFWUdESWd3c2VWUyt0M1NoYmY4MzVBTEtLZkFKa0FxRFhFa2lwS2JobEhkamR4T2E0ZlZ0OG1hekZrQjlhOWd4QmtydXZ4eHBmblJ3VDBKd3F3PSIsIml2UGFyYW1ldGVyU3BlYyI6ImZEQzE0Rzd6andXYUEyQy8iLCJtYXRlcmlhbFNldFNlcmlhbCI6MX0%3D&branch=master)
[![PyPI version](https://badge.fury.io/py/logging-utilities.svg)](https://badge.fury.io/py/logging-utilities)

This package implements some useful logging utilities. Here below are the main features of the package:

- JSON formatter
- Text formatter with `extra`
- Flask request context record attributes
- Jsonify Django request record attribute
- ISO Time in format `YYYY-MM-DDThh:mm:ss.sss±hh:mm`
- Add constant record attributes
- Logger Level Filter

All features can be fully configured from the configuration file.

**NOTE:** only python 3 is supported

:warning: **Version 3.x.x BREAKING CHANGES** see [Breaking Changes](#version-3xx-breaking-changes)

## Table of content

- [Table of content](#table-of-content)
- [Installation](#installation)
- [Release and Publish](#release-and-publish)
- [Contribution](#contribution)
  - [Developer](#developer)
- [Ignore missing log record attribute in formatter](#ignore-missing-log-record-attribute-in-formatter)
  - [LogRecordIgnoreMissing](#logrecordignoremissing)
- [Logging Context](#logging-context)
  - [Logging Context example with Pyramid](#logging-context-example-with-pyramid)
- [JSON Formatter](#json-formatter)
  - [Configure JSON Format](#configure-json-format)
  - [JSON Formatter Options](#json-formatter-options)
  - [JSON Output - Type Consistency](#json-output---type-consistency)
- [Extra Formatter](#extra-formatter)
  - [Extra Formatter Constructor](#extra-formatter-constructor)
  - [Extra Formatter Config Example](#extra-formatter-config-example)
- [Flask Request Context](#flask-request-context)
  - [Flask Request Context Filter Constructor](#flask-request-context-filter-constructor)
  - [Flask Request Context Config Example](#flask-request-context-config-example)
- [Jsonify Django Request](#jsonify-django-request)
  - [Usage](#usage)
  - [Django Request Filter Constructor](#django-request-filter-constructor)
  - [Django Request Config Example](#django-request-config-example)
- [Filter out LogRecord attributes based on their types](#filter-out-logrecord-attributes-based-on-their-types)
  - [Attribute Type Filter Constructor](#attribute-type-filter-constructor)
  - [Attribute Type Filter Config Example](#attribute-type-filter-config-example)
- [ISO Time with Timezone](#iso-time-with-timezone)
  - [ISO Time Filter Constructor](#iso-time-filter-constructor)
  - [ISO Time Config Example](#iso-time-config-example)
- [Constant Record Attribute](#constant-record-attribute)
  - [Constant Record Attribute Config Example](#constant-record-attribute-config-example)
- [Logger Level Filter](#logger-level-filter)
  - [Logger Level Filter Constructor](#logger-level-filter-constructor)
  - [Logger Level Filter Config Example](#logger-level-filter-config-example)
- [Django middleware request context](#django-middleware-request-context)
- [Log thread context](#log-thread-context)
- [Basic Usage](#basic-usage)
  - [Case 1. Simple JSON Output](#case-1-simple-json-output)
  - [Case 2. JSON Output Configured within Python Code](#case-2-json-output-configured-within-python-code)
  - [Case 3. JSON Output Configured with a YAML File](#case-3-json-output-configured-with-a-yaml-file)
  - [Case 4. Add Flask Request Context Attributes to JSON Output](#case-4-add-flask-request-context-attributes-to-json-output)
  - [Case 5. Add Django Request to JSON Output](#case-5-add-django-request-to-json-output)
  - [Case 6. Add parts of Django Request to JSON Output](#case-6-add-parts-of-django-request-to-json-output)
  - [Case 7. Add all Log Extra as Dictionary to the Standard Formatter (including Django log extra)](#case-7-add-all-log-extra-as-dictionary-to-the-standard-formatter-including-django-log-extra)
  - [Case 8. Add Specific Log Extra to the Standard Formatter](#case-8-add-specific-log-extra-to-the-standard-formatter)
  - [Case 9. Django add request info to all log records](#case-9-django-add-request-info-to-all-log-records)
- [Breaking Changes](#breaking-changes)
  - [Version 4.x.x Breaking Changes](#version-4xx-breaking-changes)
  - [Version 3.x.x Breaking Changes](#version-3xx-breaking-changes)
  - [Version 2.x.x Breaking Changes](#version-2xx-breaking-changes)
- [Credits](#credits)

## Installation

**logging_utilities** is available on PyPI.

Use pip to install:

```shell
pip install logging-utilities
```

## Release and Publish

New release and publish on PyPI is done automatically upon PR merge into `master` branch. For bug fixes and small new features,
PR can be directly open on `master`. Then the PR title define the version bump as follow:

- PR title and/or commit message contains `#major` => major version is bumped
- PR title and/or commit message contains `#patch` or head branch name starts with `bug-|hotfix-|bugfix-` => patch version is bumped
- Otherwise by default the minor version is bumped

## Contribution

Every contribution to this library is welcome ! So if you find a bug or want to add a new feature everyone is welcome to open an [issue](https://github.com/geoadmin/lib-py-logging-utilities/issues) or created a [Pull Request](https://github.com/geoadmin/lib-py-logging-utilities/pulls).

Any contribution must follow the [git-flow](https://nvie.com/posts/a-successful-git-branching-model/#the-main-branches).

### Developer

You can quickly setup your environment with the makefile:

```bash
make setup
```

This will create a virtual python environment with all packages required for the development.

Note that for pull request, the code **MUST BE** with `yapf` formatted and it also **MUST PASS** the linter. For this you can use the make targets:

```bash
make format
make lint
#or
make format-lint
```

Any new feature should have its unittest class in order to be tested.

## Ignore missing log record attribute in formatter

When configuring a log formatter you can provide via print style any log record attribute including extra attributes. However when using extra attribute, if this attribute is then missing (e.g. because the logger did not add that extra)
then the logging would raise a `ValueError: Formatting field not found in record: ...`.

For the standard Formatter you could use the [Extra Formatter](#extra-formatter), but if you have any other Formatter you
can use the global `logging_utilities.log_record.set_log_record_ignore_missing_factory()` method.

### LogRecordIgnoreMissing

The `LogRecordIgnoreMissing` factory can be used to avoid `ValueError` exception when formatting a log message from
a log record that don't have the extra required by the formatter.

For example:

```python
import logging

logging.basicConfig(format="%(message)s - %(extra_param)s", level=logging.INFO, force=True)

logger = logging.getLogger('my-logger')

logger.info('My message', extra={'extra_param': 20})
My message - 20

logger.info('My second message')
--- Logging error ---
Traceback (most recent call last):
  File "/usr/lib/python3.8/logging/__init__.py", line 440, in format
    return self._format(record)
  File "/usr/lib/python3.8/logging/__init__.py", line 436, in _format
    return self._fmt % record.__dict__
KeyError: 'extra_param'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/usr/lib/python3.8/logging/__init__.py", line 1085, in emit
    msg = self.format(record)
  File "/usr/lib/python3.8/logging/__init__.py", line 929, in format
    return fmt.format(record)
  File "/usr/lib/python3.8/logging/__init__.py", line 671, in format
    s = self.formatMessage(record)
  File "/usr/lib/python3.8/logging/__init__.py", line 640, in formatMessage
    return self._style.format(record)
  File "/usr/lib/python3.8/logging/__init__.py", line 442, in format
    raise ValueError('Formatting field not found in record: %s' % e)
ValueError: Formatting field not found in record: 'extra_param'
...
```

To avoid such crash you can use `LogRecordIgnoreMissing` that will replace missing extra attributes by an empty string in the message.

```python
import logging
from logging_utilities.log_record import LogRecordIgnoreMissing

logging.setLogRecordFactory(LogRecordIgnoreMissing)

logging.basicConfig(format="%(message)s - %(extra_param)s", level=logging.INFO, force=True)

logger = logging.getLogger('my-logger')

logger.info('My message', extra={'extra_param': 20})
My message - 20

logger.info('My second message')
My second message -
```

You can also change the default value by using the helper `set_log_record_ignore_missing_factory()`

```python
import logging
from logging_utilities.log_record import set_log_record_ignore_missing_factory

set_log_record_ignore_missing_factory('my-default')

logging.basicConfig(format="%(message)s - %(extra_param)s", level=logging.INFO, force=True)

logger = logging.getLogger('my-logger')

logger.info('My message', extra={'extra_param': 20})
My message - 20

logger.info('My second message')
My second message - my-default
```

:warning: **NOTE that setting the log record factory is a global action that affects every logger and formatter**

## Logging Context

With `set_logging_context()` you can add a thread based context to every log record. This can be quite usefull if
you want to globally set a context to every log record, for example a Request context in a Pyramid/Django application.

### Logging Context example with Pyramid

In a [Pyramid](https://docs.pylonsproject.org/projects/pyramid/en/2.0-branch/index.html) application it is quite usefull to
add to every log record the Request context. This can be done as follow:

```python
# module my_app.logging_tweens
from logging_utilities.context import set_logging_context


def logging_context_tween(handler, registry):

    def _logging_context_tween(request):
        set_logging_context({
            "request": {
                "method": request.method,
                "path": request.path,
                "headers": dict(request.headers)
            }
        })
        return handler(request)

    return _logging_context_tween

# MAIN
import logging
from wsgiref.simple_server import make_server
from pyramid.config import Configurator
from pyramid.response import Response

logging.basicConfig(format="%(message)s - %(context)s")

logger = logging.getLogger(__name__)

def hello_world(request):
    logger.debug('Request for hello world')
    return Response('Hello World!')

if __name__ == '__main__':
    with Configurator() as config:
        # Register the tween
        config.add_tween('my_app.logging_tweens.logging_context_tween')

        # Configure the route and view
        config.add_route('hello', '/')
        config.add_view(hello_world, route_name='hello')
        app = config.make_wsgi_app()
    server = make_server('0.0.0.0', 6543, app)
    server.serve_forever()

# A GET / request would produce the following log
'Request for hello world - {"request": {"method": "GET", "path": "/", "headers": {}}}'
```

For more information on Pyramid Tweens see [Registering Tween](https://docs.pylonsproject.org/projects/pyramid/en/2.0-branch/narr/hooks.html#registering-tweens)

## JSON Formatter

**JsonFormatter** is a python logging formatter that transform the log output into a json object.

JSON log format is quite useful especially when the logs are sent to **LogStash**.

This formatter supports embedded object as well as array.

### Configure JSON Format

The format can be configured either using the `format` config parameter or the `fmt` constructor parameter. This parameter should be a dictionary (for Python version below 3.7, it is better to use `OrderedDict` to keep the attribute order). Each _key_ is taken as such as _key_ for the output JSON object, while each value is transformed as follow in the output:

| Value        | Type   | Transformation        | Example        |
---------------|--------|-----------------------|----------------|
| `LogRecord` attribute  | string | The string is a `LogRecord` attribute name,<br/>then the value of this attribute is used as output. See also [Type Consistency](#json-output---type-consistency). | `"message"` |
| `LogRecord` attribute dotted key | string | The string is a dotted key to access a sub key of a `LogRecord` dictionary attribute.<br/>For example if the `LogRecord` contains a dictionary attribute added via an `extra`, you can use the dotted notation to access only a sub object/value of this dictionary. Note if the dotted key attribute doesn't exists it will raise a `ValueError` unless you set `ignore_missing=True` in the Formatter config. In the latest case missing attribute will be replaced by `''` unless the dotted key has a trailing `.` then the default value will be `{}` instead of `''`.<br/>See also [Type Consistency](#json-output---type-consistency). | `"request.path"` |
| Named string format   | string | The string contains named string format,<br/>each named format are replaced by the corresponding <br/>_LogRecord_ attribute value.<br/>When using the `%` string formatting style, you can also used dotted notation to access dictionary sub-key; `%(request.headers)s`. NOTE that in string format the dictionary key must be a valid python attribute name (cannot contain spaces or special characters). | `"%(asctime)s.%(msecs)s"` |
| Object | dict | The object is embedded in the output with its value<br/>following the same rules as defined in this table. | `{"lineno": "lineno", "file": "filename", "id": "%(process)x/%(thread)x", "message": "message"}` |
| Array | list | The list is embedded as an _array_ in the output.<br>Each value is processed using the rules from this table | `["created", "asctime", "message", "%(process)x/%(thread)x"]` |

:warning: **If the value doesn't match any of the table above it will raise a `ValueError` unless you specify `ignore_missing=True` in the configuration**

You can find the _LogRecord_ attributes list in [Python Doc](https://docs.python.org/3.7/library/logging.html#logrecord-attributes)

See below the [Basic Usage](#basic-usage) for more examples.

### JSON Formatter Options

You can change some behavior using the `JsonFormatter` constructor:

| Parameter | Type | Default | Description                                       |
|-----------|------|---------|---------------------------------------------------|
| `fmt`       | dict | `{'levelname': 'levelname', 'name': 'name', 'message': 'message'}`  | Define the output format, see [Configure JSON Format](#configure-json-format) |
| `datefmt`   | string | `None`  | Date format for `asctime`, see [time.strftime()](https://docs.python.org/3.7/library/time.html#time.strftime) |
| `style`     | string | `%`     | String formatting style, see [logging.Formatter](https://docs.python.org/3.7/library/logging.html#logging.Formatter) |
| `add_always_extra` | bool |`False` | When `True`, logging extra (`logging.log('message', extra={'my-extra': 'some value'})`) are always added to the output. Otherwise they are only added if present in `fmt`. |
| `filter_attributes` | list | `None` | When the formatter is used with a _Logging.Filter_ that adds _LogRecord_ attributes, they can be listed here to avoid to be treated as logging _extra_. |
| `remove_empty` | bool | `False` | When `True`, empty values (empty list, dict, None or empty string) are removed from output. |
| `ignore_missing` | bool | `False` | If `True`, then all extra attributes from the log record that are missing (accessed by the `fmt` parameter) will be replaced by an empty string instead of raising a ValueError exception. **NOTE:** This has an impact on all formater not only on this one, see [LogRecordIgnoreMissing](#logrecordignoremissing). |

The constructor parameters can be also be specified in the log configuration file using the `()` class specifier instead of `class`:

```yaml
formatters:
  json:
    (): logging_utilities.formatters.json_formatter.JsonFormatter
    add_always_extra: True
    fmt:
      time: asctime
      level: levelname
      logger: name
      module: module
      message: message
```

**:warning: When using the INI file format like documented [here](https://docs.python.org/3.9/library/logging.config.html#logging-config-fileformat), you cannot use the JSON formatter options describe above and have to use the formatter using the `class`, `format`, `datefmt` and `style` attributes like below**

```ini
[formatters]
keys = my_json

[formatter_my_json]
class = logging_utilities.formatters.json_formatter.JsonFormatter
format: {
        "time": "asctime",
        "level": "levelname",
        "logger": "name",
        "module": "module",
        "function": "funcName",
        "pid_tid": "%(process)x/%(thread)x",
        "message": "message",
        "exc_info": "exc_info"
    } # OPTIONAL
datefmt = %Y-%m-%d %H:%M # OPTIONAL
style = % # OPTIONAL
```

### JSON Output - Type Consistency

When you use `ignore_missing=True`, all missing attributes from the log record will be replaced by an empty string. This can be an issue if you require type consistency accross JSON logs. To avoid this, you can use the trailing dot notation.

||||
|---|---|---|
| Single trailing dot | `attribute_name.`  | Default to `{}` when `attribute_name` is missing from log record |
| Double trailing dot | `attribute_name..` | Default to `[]` when `attribute_name` is missing from log record |

This is quite usefull if you want to add a list or an object in your JSON from a LogRecord that might be missing. For example when using the [Flask Request Context](#flask-request-context) and you want to add the headers dictionary as object, you can do as follow:

```python
fmt={"message": "message", "request": {"headers": "flask_request_headers."}}
```

This way if the log record is outside a Flask request, your log output would be

`{"message": "this is the message", "request": {"headers": {}}}`

instead of

`{"message": "this is the message", "request": {"headers": ""}}`

and when the record is within a Flask context you will have

`{"message": "this is the message", "request": {"headers": {"Host": "www.example.com", ...}}}`

## Extra Formatter

This formatter enhance the python standard formatter to allow working with the log `extra`.
When adding an `extra` keyword in the format, the python standard formatter raises a `ValueError()`
when this keyword is missing from log record. This means that if you want to display a log
`extra`, you have to make sure that every log message contains this `extra`.

This formatter allow you to provide an `extra_fmt` parameter that will add record `extra` to the
log message when available. You can either add the entire extra dictionary: `extra_fmt='%s'` or
only some extras: `extra_fmt='%(extra1)s:%(extra2)s'`. In the latest case, when a key is missing
in extra, the value is replaced by `extra_default`.

When using the whole `extra` dictionary, you can use `extra_pretty_print` to improve the
formatting, note that in this case the log might be on multiline (this use `pprint.pformat`).

See [logging.Logger.debug](https://docs.python.org/3.8/library/logging.html#logging.Logger.debug) for more infos on the logging `extra`

### Extra Formatter Constructor

Support the same arguments as the [logging.Formatter](https://docs.python.org/3.5/library/logging.html#logging.Formatter)
plus the followings:

| Parameter  | Type     | Default | Description                                    |
|------------|----------|---------|------------------------------------------------|
| extra_fmt  | None\|str | None    | When not `None`, adds the `extra` at the end of the log message. Either uses named placeholder with the extra keywords or add the whole `extra` directory using `%s`. |
| extra_default | None\|str | '' | When `extra_fmt` contains named placeholders and one or more of these placeholders are not found in the log record, then the formatter uses this default value instead. |
| extra_default | any | '' | When using `extra_fmt` with named placeholders and a keyword is missing in the log record, it is then replaced by this value. |
| extra_pretty_print | boolean | False | When `extra_fmt='%s'` you can set this flag to `True` to use `pprint.pformat` on the dictionary. |
| pretty_print_kwargs | None\|dict | None | kwargs as dictionary to pass to [pprint.pformat](https://docs.python.org/3.6/library/pprint.html#pprint.pformat) |

### Extra Formatter Config Example

```yaml
formatters:
  standard:
    (): logging_utilities.formatters.extra_formatter.ExtraFormatter
    format: "%(levelname)s - %(name)s - %(message)s"
    extra_fmt: " - extra:\n%s"
    extra_pretty_print: True
```

**NOTE**: `ExtraFormatter` only support the special key `'()'` factory in the configuration file (it doesn't work with the normal `'class'` key).

## Flask Request Context

When using logging within a [Flask](https://flask.palletsprojects.com/en/2.1.x/) application, you can use this _Filter_ to add some context attributes to all _LogRecord_.

All _Flask Request_ attributes are supported and they are added as _LogRecord_ with the `flask_request_` prefix. See [Flask Request](https://flask.palletsprojects.com/en/2.1.x/api/#flask.Request) for more details on available attributes.

### Flask Request Context Filter Constructor

| Parameter  | Type | Default | Description                                    |
|------------|------|---------|------------------------------------------------|
| attributes | list | None    | List of Flask Request attributes name to add to the _LogRecord_ |

### Flask Request Context Config Example

```yaml
version: 1

root:
  handlers:
    - console
  level: DEBUG
  propagate: True

filters:
  flask:
    (): logging_utilities.filters.flask_attribute.FlaskRequestAttribute
    attributes:
      - url
      - method
      - headers
      - json

formatters:
  console:
    format: "%(asctime)s - %(message)s - %(flask_request_url)s %(flask_request_method)s %(flask_request_headers)s: %(flask_request_json)s"

handlers:
  console:
    class: logging.StreamHandler
    formatter: console
    stream: ext://sys.stdout
    filters:
      - flask
```

**NOTE**: `FlaskRequestAttribute` only support the special key `'()'` factory in the configuration file (it doesn't work with the normal `'class'` key).

## Jsonify Django Request

If you want to log the [Django](https://www.djangoproject.com/) [HttpRequest](https://docs.djangoproject.com/en/3.1/ref/request-response/#httprequest-objects) object using the [JSON Formatter](#json-formatter), this filter is for made for you. It converts the `record.http_request` attribute (or the attribute specified by `attr_key` in the constructor) to a valid json object if it is of type `HttpRequest`.

The `HttpRequest` attributes that are converted can be configured using the `include_keys` and/or `exclude_keys` filter parameters. This can be useful if you want to limit the log data, for example if you don't want to log Authentication headers.

:warning: The django framework adds sometimes an HttpRequest or socket object under `record.request` when
logging. So if you decide to use the attribute name `request` for this filter, beware that you
will need to handle the case where the attribute is of type `socket` separately, for example by
filtering it out using the attribute type filter. (see example [Filter out LogRecord attributes based on their types](#filter-out-logrecord-attributes-based-on-their-types))

### Usage

Add the filter to the log handler and then add simply the `HttpRequest` to the log extra as follow:

```python
logger.info('My message', extra={'http_request': request})
```

### Django Request Filter Constructor

| Parameter      | Type | Default | Description                                    |
|----------------|------|---------|------------------------------------------------|
| `include_keys` | list | None    | All request attributes that match any of the dotted keys of the list will be added to the jsonifiable object. When `None` then all attributes are added (default behavior). |
| `exclude_keys` | list | None    | All request attributes that match any of the dotted keys of the list will not be added to the jsonifiable object. **NOTE** this has precedence to `include_keys` which means that if a key is in both lists, then it is not added. |
|  `attr_key`    | str  | `http_request` | The name of the attribute that stores the HttpRequest object. It will be replaced in place by a jsonifiable dict representing this object. (Note that django sometimes stores an `HttpRequest` under `attr_key: request`. This is however not the default as django also stores other types of objects under this attribute name.)

### Django Request Config Example

```yaml
filters:
  django:
    (): logging_utilities.filters.django_request.JsonDjangoRequest
    attr_key: 'http_request' # This is the default, so it can be omitted
    include_keys:
      - http_request.META.REQUEST_METHOD
      - http_request.META.SERVER_NAME
      - http_request.environ
    exclude_keys:
      - http_request.META.SERVER_NAME
      - http_request.environ.wsgi
```

**NOTE**: `JsonDjangoRequest` only support the special key `'()'` factory in the configuration file (it doesn't work with the normal `'class'` key).

## Filter out LogRecord attributes based on their types

If different libraries or different parts of your code log different object types under the same
logRecord extra attribute, you can use this filter to keep only some of them (whitelist mode) or filter out
some of them (blacklist mode).

### Attribute Type Filter Constructor

| Parameter       |             Type                    | Default | Description                 |
|-----------------|-------------------------------------|---------|-----------------------------|
|`typecheck_list` | dict(key, type\|list of types)| None   | A dictionary that maps keys to a type or a list of types. By default, it will only keep a parameter matching a key if the types match or if any of the types in the list match (white list). If in black list mode, it will only keep a parameter if the types don't match. Parameters not appearing in the dict will be ignored and passed though regardless of the mode (whitelist or blacklist).
| `is_blacklist`  | bool                                | false   | Whether the list passed should be a blacklist or a whitelist. To use both, simply include this filter two times, one time with this parameter set true and one time with this parameter set false.

### Attribute Type Filter Config Example

```yaml
filters:
  type_filter:
    (): logging_utilities.filters.attr_type_filter.AttrTypeFilter
    is_blacklist: False # Default value is false, so this could be left out
    typecheck_list:
      # For each attribute listed, one type or a list of types can be specified
      request: # can only be a toplevel attribute (no dotted keys allowed)
        - django.http.request.HttpRequest # Can be a class name only or the full dotted path
        - builtins.dict
      my_attr: myClass
```

## ISO Time with Timezone

The standard logging doesn't support the time as ISO with timezone; `YYYY-MM-DDThh:mm:ss.sss±hh:mm`. By default `asctime` uses a ISO like format; `YYYY-MM-DD hh:mm:ss.sss`, but without `T` separator (although this one could be configured by overriding a global variable, this can't be done by config file). You can use the `datefmt` option to specify another date format, however this one don't supports milliseconds, so you could achieve this format: `YYYY-MM-DDThh:mm:ss±hh:mm`.

This Filter can be used to achieve the full ISO 8601 Time format including timezone and milliseconds.

### ISO Time Filter Constructor

| Parameter   | Type | Default | Description                                    |
|-------------|------|---------|------------------------------------------------|
| `isotime`     | bool | True    | Add log local time as `isotime` attribute to _LogRecord_ with the `YYYY-MM-DDThh:mm:ss.sss±hh:mm` format. |
| `utc_isotime` | bool | False   | Add log UTC time as `utc_isotime` attribute to _LogRecord_ with the `YYYY-MM-DDThh:mm:ss.sss±hh:mm` format. |

### ISO Time Config Example

```yaml
filters:
  isotime:
    (): logging_utilities.filters.TimeAttribute
    utc_isotime: True
    isotime: False
```

**NOTE**: `TimeAttribute` only support the special key `'()'` factory in the configuration file (it doesn't work with the normal `'class'` key).

## Constant Record Attribute

Simple logging _Filter_ to add constant attribute to every _LogRecord_

### Constant Record Attribute Config Example

```yaml
filters:
  application:
    (): logging_utilities.filters.ConstAttribute
    application: my-application
```

**NOTE**: `ConstAttribute` only support the special key `'()'` factory in the configuration file (it doesn't work with the normal `'class'` key).

## Logger Level Filter

Sometimes you might want to have different log Level based on the logger and handler. The standard logging library allow to set a logger level or a handler level but not based on both. Let say you have a config with two loggers logging to two handlers, on the first handler you want all messages of both loggers and on the second handler you want all messages of the first logger but only the WARNING messages of the second logger. This is here were this filter come into play.

### Logger Level Filter Constructor

| Parameter   | Type | Default | Description                                    |
|-------------|------|---------|------------------------------------------------|
| level       | int \| string | `'DEBUG'` | All messages with a lower level than this one will be filtered out. |
| logger | string | `''` | When non empty, only message from this logger will be filtered out based on their level. |

### Logger Level Filter Config Example

```yaml
root:
  handlers:
    - "console"
    - "file"
  level: "DEBUG"
  propagate: "True"

filters:
  B_filter:
    (): logging_utilities.filters.LevelFilter
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
      - "B_filter"
```

**NOTE**: `LevelFilter` only support the special key `'()'` factory in the configuration file (it doesn't work with the normal `'class'` key).

## Django middleware request context

`AddToThreadContextMiddleware` is a [Middleware](https://docs.djangoproject.com/en/5.1/topics/http/middleware/) with which you can add the [Django](https://www.djangoproject.com/) [HttpRequest](https://docs.djangoproject.com/en/5.1/ref/request-response/#httprequest-objects) to thread local variables. The request object is added to a global variable in `logging_utilities.thread_context` and can be accessed in the following way:

```python
from logging_utilities.thread_context import thread_context

getattr(thread_context, 'request')
```

## Log thread context

`AddThreadContextFilter` provides a logging filter that will add data from the thread local store `logging_utilities.thread_context` to the log record. To set data on the thread store do the following:

```python
from logging_utilities.thread_context import thread_context

setattr(thread_context, 'key', data)
```

Configure the filter to decide which data should be added and how it should be named:

```yaml
filters:
  add_request:
    (): logging_utilities.filters.add_thread_context_filter.AddThreadContextFilter
    contexts:
    - logger_key: log_record_key
      context_key: key
```

| Parameter  | Type | Default | Description                                    |
|------------|------|---------|------------------------------------------------|
| `contexts` | list | empty   | List of values to add to the log record. Dictionary must contain value for 'context_key' to read value from thread local variable. Dictionary must also contain 'logger_key' to set the value on the log record. |

## Basic Usage

### Case 1. Simple JSON Output

```python
import logging

from logging_utilities.formatters.json_formatter import basic_config

# default keyword parameter `format`: """{"levelname": "levelname", "name": "name", "message": "message"}"""
basic_config(level=logging.INFO)
logging.info('hello, json_formatter')
```

output:

```shell
{"levelname": "INFO", "name": "root", "message": "hello, json_formatter"}
```

### Case 2. JSON Output Configured within Python Code

```python
import logging

from logging_utilities.formatters.json_formatter import JsonFormatter

# `FORMAT` can be `json`, `OrderedDict` or `dict`.
# If `FORMAT` is `dict` and python version < 3.7.0, the output order is sorted by keys, otherwise it will be the same
# as the defined order.
#
# KEY := string, can be whatever you like.
# VALUE := `LogRecord` attribute name, string, formatted string (e.g. "%(asctime)s.%(msecs)s"), list or dict
FORMAT = {
    "Name":            "name",
    "Levelno":         "levelno",
    "Levelname":       "levelname",
    "Pathname":        "pathname",
    "Filename":        "filename",
    "Module":          "module",
    "Lineno":          "lineno",
    "FuncName":        "funcName",
    "Created":         "created",
    "Asctime":         "asctime",
    "Msecs":           "msecs",
    "RelativeCreated": "relativeCreated",
    "Thread":          "thread",
    "ThreadName":      "threadName",
    "Process":         "process",
    "Message":         "message"
}

root = logging.getLogger()
root.setLevel(logging.INFO)

formatter = JsonFormatter(FORMAT)

sh = logging.StreamHandler()
sh.setFormatter(formatter)
sh.setLevel(logging.INFO)

root.addHandler(sh)

def test():
  root.info("test %s format", 'string')

test()
```

output:

```shell
{
  "Name": "root", 
  "Levelno": 20, 
  "Levelname": "INFO", 
  "Pathname": "test.py", 
  "Filename": "test.py", 
  "Module": "test", 
  "Lineno": 75, 
  "FuncName": "test", 
  "Created": 1588185267.3198836, 
  "Asctime": "2020-04-30 02:34:27,319", 
  "Msecs": 319.8835849761963, 
  "RelativeCreated": 88.2880687713623, 
  "Thread": 16468, 
  "ThreadName": "MainThread", 
  "Process": 16828, 
  "Message": "test string format"
}
```

### Case 3. JSON Output Configured with a YAML File

config.yaml:

```yaml
version: 1

root:
  handlers:
    - console
  level: DEBUG
  propagate: True

formatters:
  json:
    class: logging_utilities.formatters.json_formatter.JsonFormatter
    format:
      time: asctime
      level: levelname
      logger: name
      module: module
      function: funcName
      process: process
      thread: thread
      message: message

handlers:
  console:
    class: logging.StreamHandler
    formatter: json
    stream: ext://sys.stdout
```

Then in your python code use it as follow:

```python
import logging
import logging.config

import yaml


config = {}
with open('example-config.yaml', 'r') as fd:
    config = yaml.safe_load(fd.read())

logging.config.dictConfig(config)

root = logging.getLogger()
root.info('Test file config')
```

output:

```shell
{
  "function": "<module>", 
  "level": "INFO", 
  "logger": "root", 
  "message": "Test file config", 
  "module": "<stdin>", 
  "process": 12264, 
  "thread": 139815989413696, 
  "time": "asctime"
}
```

### Case 4. Add Flask Request Context Attributes to JSON Output

config.yaml

```yaml
version: 1

root:
  handlers:
    - console
  level: DEBUG
  propagate: True

filters:
  isotime:
    (): logging_utilities.filters.TimeAttribute
  flask:
    (): logging_utilities.filters.flask_attribute.FlaskRequestAttribute
    attributes:
      - url
      - method
      - headers
      - remote_addr
      - json

formatters:
  json:
    class: logging_utilities.formatters.json_formatter.JsonFormatter
    format:
      time: isotime
      level: levelname
      logger: name
      module: module
      function: funcName
      process: process
      thread: thread
      request:
        # We use the "%()s" notation here to ensure a string output and also if the LogRecord has
        # no flask context, meaning no `flask_request_url` attribute, the "%()s" notation ensure
        # to have an empty string instead of treating `flask_request_url` as a string constant.
        url: "%(flask_request_url)s"
        method: "%(flask_request_method)s"
        # We use a trailing dot here to ensure to have a dictionary output even if the LogRecord 
        # doesn't have a flask_request_headers attribute.
        headers: flask_request_headers.
        data: flask_request_json.
        remote: "%(flask_request_remote_addr)s"
      message: message

handlers:
  console:
    class: logging.StreamHandler
    formatter: json
    stream: ext://sys.stdout
    filters:
      - isotime
      - flask
```

**NOTE:** This require to have `flask` package installed otherwise it raises `ImportError`

Then in your python code use it as follow:

```python
import logging
import logging.config

import yaml
from flask import Flask


config = {}
with open('example-config.yaml', 'r') as fd:
    config = yaml.safe_load(fd.read())

logging.config.dictConfig(config)

app = Flask('test')

root = logging.getLogger()

with app.test_request_context("path/test", method='GET', headers={"Accept": "*/*"}):
  root.info('Test file config')
```

output:

```shell
{
  "time": "2022-07-20T10:09:10.765237+02:00", 
  "level": "INFO",
  "logger": "root", 
  "module": "<stdin>", 
  "function": "<module>", 
  "process": 58043, 
  "thread": 139717802334016, 
  "request": {
    "url": "http://localhost/path/test", 
    "method": "GET", 
    "headers": {
      "Host": "localhost", 
      "Accept": "*/*"
    }, 
    "data": null, 
    "remote": null
  }, 
  "message": "Test file config"
}
```

### Case 5. Add Django Request to JSON Output

config.yaml

```yaml
version: 1

root:
  handlers:
    - console
  level: DEBUG
  propagate: True

filters:
  isotime:
    (): logging_utilities.filters.TimeAttribute
  django:
    (): logging_utilities.filters.django_request.JsonDjangoRequest
    include_keys:
      - http_request.path
      - http_request.method
      - http_request.headers
    exclude_keys:
      - http_request.headers.Authorization
      - http_request.headers.Proxy-Authorization

formatters:
  json:
    class: logging_utilities.formatters.json_formatter.JsonFormatter
    format:
      time: isotime
      level: levelname
      logger: name
      module: module
      function: funcName
      process: process
      thread: thread
      request: http_request
      response: response
      message: message

handlers:
  console:
    class: logging.StreamHandler
    formatter: json
    stream: ext://sys.stdout
    filters:
      - isotime
      - django
```

**NOTE:** This require to have `django` package installed otherwise it raises `ImportError`

Then in your python code use it as follow:

```python
import logging
import logging.config

import yaml

from django.http import JsonResponse
from django.conf import settings
from django.test import RequestFactory


config = {}
with open('example-config.yaml', 'r') as fd:
    config = yaml.safe_load(fd.read())

logging.config.dictConfig(config)

logger = logging.getLogger('your_logger')

def my_page(request):
    answer = {'success': True}
    logger.info('My page requested', extra={'request': request, 'response': answer})
    return JsonResponse(answer)

settings.configure()
factory = RequestFactory()

my_page(factory.get('/my_page?test=true'))
```

output:

```shell
{
  "function": "my_page", 
  "level": "INFO", 
  "logger": "your_logger", 
  "message": "My page requested", 
  "module": "<stdin>", 
  "process": 20421, 
  "request": {
    "method": "GET", 
    "path": "/my_page", 
    "headers": {
      "Cookie": ""
    }
  }, 
  "response": {
    "success": true
  }, 
  "thread": 140433370822464, 
  "time": "2020-10-12T16:44:45.374508+02:00"
}
```

### Case 6. Add parts of Django Request to JSON Output

Let's say you want to log parts of the django `HttpRequest` in Json format. Django already logs it
sometimes under `record.request` so you can use the django request filter to transform it to a jsonisable
dictionary. However django sometimes also logs an object of type `socket.socket` that you may not
want to include in the logs. In this case you could use the following configuration. This will only
keep the request attribute if it is of type `HttpRequest`.

config.yaml

```yaml
version: 1

root:
  handlers:
    - console
  level: DEBUG
  propagate: True

filters:
  type_filter:
    (): logging_utilities.filters.attr_type_filter.AttrTypeFilter
    typecheck_list:
      request: django.http.request.HttpRequest
  isotime:
    (): logging_utilities.filters.TimeAttribute
  django:
    (): logging_utilities.filters.django_request.JsonDjangoRequest
    attr_name: request
    include_keys:
      - request.path
      - request.method
      - request.headers

formatters:
  json:
    class: logging_utilities.formatters.json_formatter.JsonFormatter
    format:
      time: isotime
      level: levelname
      logger: name
      module: module
      function: funcName
      process: process
      thread: thread
      request_path: request.path
      request_method: request.method
      request:
        # NOTE: django headers name are case sensitive
        header.accept: request.headers.Accept
        header.accept-encoding: request.headers.Accept-Encoding 
        header.accept_language: request.headers.Accept-Language 
      message: message

handlers:
  console:
    class: logging.StreamHandler
    formatter: json
    stream: ext://sys.stdout
    filters:
      - isotime
      # Typefilter must be before django filter, as the django filter
      # will modify the type of the "HttpRequest" object
      - type_filter
      - django
```

**NOTE:** This require to have `django` package installed otherwise it raises `ImportError`

Then in your python code use it as follow:

```python
import logging
import logging.config

import yaml

from django.http import JsonResponse
from django.conf import settings
from django.test import RequestFactory


config = {}
with open('example-config.yaml', 'r') as fd:
    config = yaml.safe_load(fd.read())

logging.config.dictConfig(config)

logger = logging.getLogger('your_logger')

def my_page(request):
    answer = {'success': True}
    logger.info('My page requested', extra={'request': request})
    return JsonResponse(answer)

settings.configure()
factory = RequestFactory()

my_page(factory.get(
    '/my_page?test=true', 
    HTTP_ACCEPT='*/*', 
    HTTP_ACCEPT_ENCODING='gzip', 
    HTTP_ACCEPT_LANGUAGE='en')
)
```

output:

```shell
{
  "time": "2022-07-20T12:29:19.536922+02:00",
  "level": "INFO",
  "logger": "your_logger",
  "module": "<stdin>",
  "function": "my_page",
  "process": 78479,
  "thread": 139751209555776,
  "request_path": "/my_page",
  "request_method": "GET",
  "request": {
    "header.accept": "*/*",
    "header.accept-encoding": "gzip",
    "header.accept_language": "en"
  },
  "message": "My page requested"
}
```

### Case 7. Add all Log Extra as Dictionary to the Standard Formatter (including Django log extra)

config.yaml

```yaml
version: 1

root:
  handlers:
    - console
  level: DEBUG
  propagate: True

filters:
  type_filter:
    (): logging_utilities.filters.attr_type_filter.AttrTypeFilter
    typecheck_list:
      request: django.http.request.HttpRequest
  isotime:
    (): logging_utilities.filters.TimeAttribute
  django:
    (): logging_utilities.filters.django_request.JsonDjangoRequest
    attr_name: request
    include_keys:
      - request.path
      - request.method
      - request.headers
    exclude_keys:
      - request.headers.Authorization
      - request.headers.Proxy-Authorization

formatters:
  standard_extra:
    (): logging_utilities.formatters.extra_formatter.ExtraFormatter
    # NOTE also in the constructor the parameter is `fmt` we need to use `format` here
    format: "%(isotime)s - %(levelname)s - %(name)s - %(message)s"
    extra_fmt: " - extra:\n%s"
    extra_pretty_print: True
    pretty_print_kwargs:
      indent: 2
      width: 60

handlers:
  console:
    class: logging.StreamHandler
    formatter: standard_extra
    stream: ext://sys.stdout
    filters:
      - isotime
      # Type filter must be before django filter
      - type_filter
      - django
```

**NOTE:** This require to have `django` package installed otherwise it raises `ImportError`

Then in your python code use it as follow:

```python
#!.venv/bin/python3
import logging
import logging.config

import yaml

from django.http import JsonResponse
from django.conf import settings
from django.test import RequestFactory


config = {}
with open('example-config.yaml', 'r') as fd:
    config = yaml.safe_load(fd.read())

logging.config.dictConfig(config)

logger = logging.getLogger('your_logger')

def my_page(request):
    answer = {'success': True}
    logger.info('My page requested', extra={'request': request, 'response': answer})
    return JsonResponse(answer)

settings.configure()
factory = RequestFactory()

my_page(factory.get('/my_page?test=true'))
```

output:

```shell
2020-11-19T13:32:58.942568+01:00 - INFO - your_logger - My page requested - extra:
{ 'request': { 'headers': {'Cookie': ''},
               'method': 'GET',
               'path': '/my_page'},
  'response': {'success': True}}
```

### Case 8. Add Specific Log Extra to the Standard Formatter

config.yaml

```yaml
version: 1

root:
  handlers:
    - console
  level: DEBUG
  propagate: True

formatters:
  standard_extra:
    (): logging_utilities.formatters.extra_formatter.ExtraFormatter
    # NOTE also in the constructor the parameter is `fmt` we need to use `format` here
    format: "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    extra_fmt: " - extra1=%(extra1)s"

handlers:
  console:
    class: logging.StreamHandler
    formatter: standard_extra
    stream: ext://sys.stdout
```

Then in your python code use it as follow:

```python
#!.venv/bin/python3
import logging
import logging.config

import yaml

config = {}
with open('example-config.yaml', 'r') as fd:
    config = yaml.safe_load(fd.read())

logging.config.dictConfig(config)

logger = logging.getLogger('your_logger')

logger.debug('My log with extras', extra={'extra1': 23, 'extra2': "don't add this"})
```

output:

```shell
2020-11-19 13:42:29,424 - DEBUG - your_logger - My log with extras - extra1=23
```

### Case 9. Django add request info to all log records

Combine the use of the middleware `AddToThreadContextMiddleware` with the filters `AddThreadContextFilter` and `JsonDjangoRequest`, as well as the `JsonFormatter` to add request context to each log entry.

Activate the [middleware](https://docs.djangoproject.com/en/5.1/topics/http/middleware/#activating-middleware):

```python
MIDDLEWARE = (
    ...,
    'logging_utilities.django_middlewares.add_request_context.AddToThreadContextMiddleware',
    ...,
)
```

Configure the filters `AddThreadContextFilter` and `JsonDjangoRequest` to add the request from the thread variable to the log record and make it json encodable. Use the `JsonFormatter` to format the request values

```yaml
filters:
  add_request:
    (): logging_utilities.filters.add_thread_context_filter.AddThreadContextFilter
    contexts:
    - context_key: request # Must be value 'request' as this is how the middleware adds the value.
      logger_key: request
  request_fields:
    (): logging_utilities.filters.django_request.JsonDjangoRequest
    attr_key: request # Must match the above logger_key
    include_keys:
      - request.path
      - request.method
formatters:
  json:
    (): logging_utilities.formatters.json_formatter.JsonFormatter
    fmt:
      time: asctime
      level: levelname
      logger: name
      module: module
      message: message
      request:
        path: request.path
        method: request.method
handlers:
  console:
    formatter: json
    filters:
      # Make sure to add the filters in the correct order.
      # These filters modify the record in-place, and as the record is passed serially to each handler.
      - add_request
      - request_fields
```

## Breaking Changes

### Version 4.x.x Breaking Changes

From version 3.x.x to version 4.x.x there is the following breaking change:

- The django request filter by default now reads the attribute `record.http_request` instead of
the attribute `record.request`. There is however a new option `attr_name` in the filters constructor
to manually specify the attribute name. See the example [Add parts of Django Request to JSON Output](#case-6-add-parts-of-django-request-to-json-output) for an example on how to use `attr_name` to be
backward-compatible with 3.x.x

### Version 3.x.x Breaking Changes

From version 2.x.x to version 3.x.x there is the following breaking change:

- JSON Formatter doesn't support anymore string constant in the `fmt` parameter. Now if you want to have a string constant in all of you JSON logs output, you need to use the [Constant Record Attribute Filter](#constant-record-attribute).

### Version 2.x.x Breaking Changes

From version 1.x.x to version 2.x.x there is the following breaking change:

- Flask Attribute filter do not set anymore missing Flask attribute to empty string ! So if you configure the Flask attribute you must make sure that all attribute specified in the attribute list, exists. Also if you use the filter on a logger outside of a Flask Request context, the logger will raise a `ValueError` exception due to the missing Flask Request attribute. To avoid this you can use the new [LogRecordIgnoreMissing](#logrecordignoremissing).

## Credits

The JSON Formatter implementation has been inspired by [MyColorfulDays/jsonformatter](https://github.com/MyColorfulDays/jsonformatter)

The Request Var middleware has been inspired by [kindlycat/django-request-vars](https://github.com/kindlycat/django-request-vars)
