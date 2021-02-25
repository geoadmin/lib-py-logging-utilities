# Python logging utilities

[![Build Status](https://travis-ci.org/geoadmin/lib-py-logging-utilities.svg?branch=master)](https://travis-ci.org/geoadmin/lib-py-logging-utilities)
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

## Table of content

- [Installation](#installation)
- [Release and Publish](#release-and-publish)
- [Contribution](#contribution)
- [JSON Formatter](#json-formatter)
- [Extra Formatter](#extra-formatter)
- [Flask Request Context](#flask-request-context)
- [Jsonify Django Request](#jsonify-django-request)
- [ISO Time with Timezone](#iso-time-with-timezone)
- [Constant Record Attribute](#constant-record-attribute)
- [Logger Level Filter](#logger-level-filter)
- [Basic Usage](#basic-usage)
  - [Case 1. Simple JSON Output](#case-1-simple-json-output)
  - [Case 2. JSON Output Configured within Python Code](#case-2-json-output-configured-within-python-code)
  - [Case 3. JSON Output Configured with a YAML File](#case-3-json-output-configured-with-a-yaml-file)
  - [Case 4. Add Flask Request Context Attributes to JSON Output](#case-4-add-flask-request-context-attributes-to-json-output)
  - [Case 5. Add Django Request to JSON Output](#case-5-add-django-request-to-json-output)
  - [Case 6. Add all Log Extra as Dictionary to the Standard Formatter](#case-6-add-all-log-extra-as-dictionary-to-the-standard-formatter-including-django-log-extra)
  - [Case 7. Add Specific Log Extra to the Standard Formatter](#case-7-add-specific-log-extra-to-the-standard-formatter)
- [Credits](#credits)

## Installation

__logging_utilities__ is available on PyPI.

Use pip to install:

```shell
pip install logging-utilities
```

## Release and Publish

Only owners are allowed to publish a new version to PyPI. To publish a new version follow the procedure below:

1. Increase the `VERSION` in `logging_utilities/__init__.py`
    - Major version for outbreak changes in the user interface (no backward compatibility)
    - Minor version for new features
    - Patch version for bug fixes
    - For alpha version append `alpha1` to `VERSION`
1. Commit and push the changes to `develop` branch
1. Merge `develop` to  `master`
1. From `master` branch enter

    ```shell
    summon -p gopass --up make publish
    ```

**NOTE**: this requires to have `summon`, `gopass` and the correct `secrets.yml` file in a parent folder.

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

## JSON Formatter

**JsonFormatter** is a python logging formatter that transform the log output into a json object.

JSON log format is quite useful especially when the logs are sent to **LogStash**.

This formatter supports embedded object as well as array.

### Configure JSON Format

The format can be configured either using the `format` config parameter or the `fmt` constructor parameter. This parameter should be a dictionary (for Python version below 3.7, it is better to use `OrderedDict` to keep the attribute order). Each _key_ is taken as such as _key_ for the output JSON object, while each value is transformed as follow in the output:

| Value        | Type   | Transformation        | Example        |
---------------|--------|-----------------------|----------------|
| attribute    | string | The string is a _LogRecord_ attribute name,<br/>then the value of this attribute is used as output. | `"message"` |
| str format   | string | The string contains named string format,<br/>each named format are replaced by the corresponding <br/>_LogRecord_ attribute value. | `"%(asctime)s.%(msecs)s"` |
| object | dict | The object is embedded in the output with its value<br/>following the same rules as defined in this table. | `{"lineno": "lineno", "file": "filename"}` |
| array | list | The list is embedded as an _array_ in the output.<br>Each value is processed using the rules from this table | `["created", "asctime"]` |

You can find the _LogRecord_ attributes list in [Python Doc](https://docs.python.org/3.7/library/logging.html#logrecord-attributes)

### JSON Formatter Options

You can change some behavior using the `JsonFormatter` constructor:

| Parameter | Type | Default | Description                                       |
|-----------|------|---------|---------------------------------------------------|
| `fmt`       | dict | `None`  | Define the output format, see [Configure JSON Format](#configure-json-format) |
| `datefmt`   | string | `None`  | Date format for `asctime`, see [time.strftime()](https://docs.python.org/3.7/library/time.html#time.strftime) |
| `style`     | string | `%`     | String formatting style, see [logging.Formatter](https://docs.python.org/3.7/library/logging.html#logging.Formatter) |
| `add_always_extra` | bool |`False` | When `True`, logging extra (`logging.log('message', extra={'my-extra': 'some value'})`) are always added to the output. Otherwise they are only added if present in `fmt`. |
| `filter_attributes` | list | `None` | When the formatter is used with a _Logging.Filter_ that adds _LogRecord_ attributes, they can be listed here to avoid to be treated as logging _extra_. |
| `remove_empty` | bool | `False` | When `True`, empty values (empty list, dict, None or empty string) are removed from output. |

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

When using logging within a [Flask](https://flask.palletsprojects.com/en/1.1.x/) application, you can use this _Filter_ to add some context attributes to all _LogRecord_.

All _Flask Request_ attributes are supported and they are added as _LogRecord_ with the `flask_request_` prefix.

### Flask Request Context Filter Constructor

| Parameter  | Type | Default | Description                                    |
|------------|------|---------|------------------------------------------------|
| attributes | list | None    | List of Flask Request attributes name to add to the _LogRecord_ |

### Flask Request Context Config Example

```yaml
filters:
  flask:
    (): logging_utilities.filters.flask_attribute.FlaskRequestAttribute
    attributes:
      - url
      - method
      - headers
      - remote_addr
      - json
```

**NOTE**: `FlaskRequestAttribute` only support the special key `'()'` factory in the configuration file (it doesn't work with the normal `'class'` key).

## Jsonify Django Request

If you want to log the [Django](https://www.djangoproject.com/) [HttpRequest](https://docs.djangoproject.com/en/3.1/ref/request-response/#httprequest-objects) object using the [JSON Formatter](#json-formatter), this filter is for made for you. It converts the `record.request` attribute to a valid json object or a string if the attribute is not an `HttpRequest` instance. It is also useful when using Django with the JSON Formatter because Django adds in some of its logs either an HttpRequest object to the log extra or a socket object.

The `HttpRequest` attributes that are converted can be configured using the `include_keys` and/or `exclude_keys` filter parameters. This can be useful if you want to limit the log data, for example if you don't want to log Authentication headers.

### Usage

Add the filter to the log handler and then add simply the `HttpRequest` to the log extra as follow:

```python
logger.info('My message', extra={'request': request})
```

### Django Request Filter Constructor

| Parameter      | Type | Default | Description                                    |
|----------------|------|---------|------------------------------------------------|
| `include_keys` | list | None    | All request attributes that match any of the dotted keys of the list will be jsonify in the `record.request`. When `None` then all attributes are added (default behavior). |
| `exclude_keys` | list | None    | All request attributes that match any of the dotted keys of the list will not be added to the jsonify of the `record.request`. **NOTE** this has precedence to `include_keys` which means that if a key is in both list, then it is not added. |

### Django Request Config Example

```yaml
filters:
  django:
    (): logging_utilities.filters.django_request.JsonDjangoRequest
    include_keys:
      - request.META.REQUEST_METHOD
      - request.META.SERVER_NAME
      - request.environ
    exclude_keys:
      - request.META.SERVER_NAME
      - request.environ.wsgi
```

**NOTE**: `JsonDjangoRequest` only support the special key `'()'` factory in the configuration file (it doesn't work with the normal `'class'` key).

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
{"Name": "root", "Levelno": 20, "Levelname": "INFO", "Pathname": "test.py", "Filename": "test.py", "Module": "test", "Lineno": 75, "FuncName": "test", "Created": 1588185267.3198836, "Asctime": "2020-04-30 02:34:27,319", "Msecs": 319.8835849761963, "RelativeCreated": 88.2880687713623, "Thread": 16468, "ThreadName": "MainThread", "Process": 16828, "Message": "test string format"}
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
{"function": "<module>", "level": "INFO", "logger": "root", "message": "Test file config", "module": "<stdin>", "process": 12264, "thread": 139815989413696, "time": "asctime"}
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
        url: flask_request_url
        method: flask_request_method
        headers: flask_request_headers
        data: flask_request_json
        remote: flask_request_remote_addr
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


config = {}
with open('example-config.yaml', 'r') as fd:
    config = yaml.safe_load(fd.read())

logging.config.dictConfig(config)

root = logging.getLogger()
root.info('Test file config')
```

output:

```shell
{"function": "<module>", "level": "INFO", "logger": "root", "message": "Test file config", "module": "<stdin>", "process": 24190, "request": {"url": "", "method": "", "headers": "", "data": "", "remote": ""}, "thread": 140163374577472, "time": "isotime"}
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
      - request.path
      - request.method
      - request.headers
    exclude_keys:
      - request.headers.Authorization
      - request.headers.Proxy-Authorization

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
      request: request
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
{"function": "my_page", "level": "INFO", "logger": "your_logger", "message": "My page requested", "module": "<stdin>", "process": 20421, "request": {"method": "GET", "path": "/my_page", "headers": {"Cookie": ""}}, "response": {"success": true}, "thread": 140433370822464, "time": "2020-10-12T16:44:45.374508+02:00"}
```

### Case 6. Add all Log Extra as Dictionary to the Standard Formatter (including Django log extra)

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

### Case 7. Add Specific Log Extra to the Standard Formatter

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

## Credits

The JSON Formatter implementation has been inspired by [MyColorfulDays/jsonformatter](https://github.com/MyColorfulDays/jsonformatter)
