#!/usr/bin/env python

from setuptools import setup, find_packages

# Get description from README.md
LONG_DESCRIPTION = ''
with open('README.md', encoding='utf-8') as rd:
    LONG_DESCRIPTION = rd.read()

# Here we cannot import the version but need to read it otherwise we might have an ImportError
# during execution of the setup.py if the package contains other libaries.
VERSION_LINE = list(
    filter(lambda l: l.startswith('VERSION'), open('./logging_utilities/__init__.py'))
)[0]


def get_version(version_line):
    # pylint: disable=eval-used
    version_tuple = eval(version_line.split('=')[-1])
    return ".".join(map(str, version_tuple))


setup(
    name='logging-utilities',
    version=get_version(VERSION_LINE),
    description=(
        'A collection of useful logging formatters and filters. '
        'JSON Formatter, Extra Formatter, ISO Time Filter, Flask Filter, Django Filter, ...'
    ),
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    platforms=["all"],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Utilities',
        'Topic :: System :: Logging',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Framework :: Django',
        'Framework :: Flask'
    ],
    python_requires='>=3.0',
    author='ltshb',
    author_email='brice.schaffner@swisstopo.ch',
    url='https://github.com/geoadmin/lib-py-logging-utilities',
    license='BSD 3-Clause License',
    packages=find_packages()
)
