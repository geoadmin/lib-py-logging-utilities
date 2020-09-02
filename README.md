# Python logging utilities

[![Build Status](https://travis-ci.org/geoadmin/lib-py-logging-utilities.svg?branch=master)](https://travis-ci.org/geoadmin/lib-py-logging-utilities)

This package implements some usefull logging utilities. Here below are the main features of the package:

- JSON formatter
- Flask request context record attributes
- ISO Time in format `YYYY-MM-DDThh:mm:ss.sss±hh:mm`
- Add constant record attributes
- Logger Level Filter

All features can be fully configured from the configuration file.

**NOTE:** only python 3 is supported

## Table of content

- [Installation](#installation)
- [Contribution](#contribution)
- [JSON Formatter](#json-formatter)
- [Flask Request Context](#flask-request-context)
- [ISO Time with Timezone](#iso-time-with-timezone)
- [Constant Record Attribute](#constant-record-attribute)
- [Logger Level Filter](#logger-level-filter)
- [Basic Usage](#basic-usage)
  - [Case 1. Simple JSON Output](#case-1-simple-json-output)
  - [Case 2. JSON Output Configured within Python Code](#case-2-json-output-configured-within-python-code)
  - [Case 3. JSON Output Configured with a YAML File](#case-3-json-output-configured-with-a-yaml-file)
  - [Case 4. Add Flask Request Context Attributes to JSON Output](#case-4-add-flask-request-context-attributes-to-json-output)
- [Credits](#credits)

## Installation

__logging_utilities__ is available on PyPI.

Use pip to install:

```shell
pip install logging-utilities
```

## Contribution

TODO

## JSON Formatter

**JsonFormatter** is a python logging formatter that transform the log output into a json object.

JSON log format is quite usefull especially when the logs are sent to **LogStash**.

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
| fmt       | dict | `None`  | Define the output format, see [Configure JSON Format](#configure-json-format) |
| datefmt   | string | `None`  | Date format for `asctime`, see [time.strftime()](https://docs.python.org/3.7/library/time.html#time.strftime) |
| style     | string | `%`     | String formatting style, see [logging.Formatter](https://docs.python.org/3.7/library/logging.html#logging.Formatter) |
| add_always_extra | bool |`False` | When `True`, logging extra (`logging.log('message', extra={'my-extra': 'some value'})`) are always added to the output. Otherwise they are only added if present in `fmt`. |
| filter_attributes | list | `None` | When the formatter is used with a _Logging.Filter_ that adds _LogRecord_ attributes, they can be listed here to avoid to be treated as logging _extra_. |
| remove_empty | bool | `False` | When `True`, empty values (empty list, dict, None or empty string) are removed from output. |

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

## ISO Time with Timezone

The standard logging doesn't support the time as ISO with timezone; `YYYY-MM-DDThh:mm:ss.sss±hh:mm`. By default `asctime` uses a ISO like format; `YYYY-MM-DD hh:mm:ss.sss`, but without `T` separator (although this one could be configured by overriding a global variable, this can't be done by config file). You can use the `datefmt` option to specify another date format, however this one don't supports milliseconds, so you could achieve this format: `YYYY-MM-DDThh:mm:ss±hh:mm`.

This Filter can be used to achieve the full ISO 8601 Time format including timezone and milliseconds.

### ISO Time Filter Constructor

| Parameter   | Type | Default | Description                                    |
|-------------|------|---------|------------------------------------------------|
| isotime     | bool | True    | Add log local time as `isotime` attribute to _LogRecord_ with the `YYYY-MM-DDThh:mm:ss.sss±hh:mm` format. |
| utc_isotime | bool | False   | Add log UTC time as `utc_isotime` attribute to _LogRecord_ with the `YYYY-MM-DDThh:mm:ss.sss±hh:mm` format. |

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
| logger | string | `''` | When non empty, only message from this logger will be fitlered out based on their level. |

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

from logging_utilites.formatters.json_formatter import basic_config

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

from logging_utilites.formatters.json_formatter import JsonFormatter

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

## Credits

The JSON Formatter implementation has been inspired by [MyColorfulDays/jsonformatter](https://github.com/MyColorfulDays/jsonformatter)
