SHELL = /bin/bash

.DEFAULT_GOAL := help


CURRENT_DIR := $(shell pwd)
VENV := $(CURRENT_DIR)/.venv
DEV_REQUIREMENTS = $(CURRENT_DIR)/dev_requirements.txt

# Test reports configuration
TEST_REPORT_DIR ?= $(CURRENT_DIR)/tests/report
TEST_REPORT_FILE ?= nose2-junit.xml

# PyPI credentials
PYPI_USER ?=
PYPI_PASSWORD ?=

# venv targets timestamps
VENV_TIMESTAMP = $(VENV)/.timestamp
DEV_REQUIREMENTS_TIMESTAMP = $(VENV)/.dev-requirements.timestamp

# general targets timestamps
TIMESTAMPS = .timestamps
PREP_PACKAGING_TIMESTAMP = $(TIMESTAMPS)/.prep-packaging.timestamp

# Find all python files that are not inside a hidden directory (directory starting with .)
PYTHON_FILES := $(shell find ./* -type d \( -path ./build -o -path ./dist \) -prune -false -o -type f -name "*.py" -print)

PYTHON_VERSION ?= 3
SYSTEM_PYTHON := python$(PYTHON_VERSION)

# Commands
PYTHON := $(VENV)/bin/python3
PIP := $(VENV)/bin/pip3
YAPF := $(VENV)/bin/yapf
ISORT := $(VENV)/bin/isort
NOSE := $(VENV)/bin/nose2
PYLINT := $(VENV)/bin/pylint

PACKAGE_VERSION = $(shell awk '/^Version:/ {print $$2}' logging_utilities.egg-info/PKG-INFO)


all: help


.PHONY: help
help:
	@echo "Usage: make <target>"
	@echo
	@echo "Possible targets:"
	@echo -e " \033[1mSetup TARGETS\033[0m "
	@echo "- setup              Create the python virtual environment with developper tools"
	@echo -e " \033[1mFORMATING, LINTING AND TESTING TOOLS TARGETS\033[0m "
	@echo "- format             Format the python source code"
	@echo "- lint               Lint the python source code"
	@echo "- format-lint        Format and lint the python source code"
	@echo "- test               Run the tests"
	@echo -e " \033[1mPACKAGING TARGETS\033[0m "
	@echo "- package            Create package"
	@echo "- publish            Tag and publish package to PyPI"
	@echo -e " \033[1mCLEANING TARGETS\033[0m "
	@echo "- clean              Clean genereated files"
	@echo "- clean-venv         Clean python venv"
	@echo "- clean-all          Clean everything"


# Build targets. Calling setup is all that is needed for the local files to be installed as needed.

.PHONY: setup
setup: $(DEV_REQUIREMENTS_TIMESTAMP)


# linting target, calls upon yapf to make sure your code is easier to read and respects some conventions.

.PHONY: format
format: $(DEV_REQUIREMENTS_TIMESTAMP)
	$(YAPF) -p -i --style .style.yapf $(PYTHON_FILES)
	$(ISORT) $(PYTHON_FILES)


.PHONY: ci-check-format
ci-check-format: format
	@if [[ -n `git status --porcelain` ]]; then \
	 	>&2 echo "ERROR: the following files are not formatted correctly:"; \
		>&2 git status --porcelain; \
		exit 1; \
	fi


.PHONY: lint
lint: $(DEV_REQUIREMENTS_TIMESTAMP)
	$(PYLINT) $(PYTHON_FILES)


.PHONY: format-lint
format-lint: format lint


# Test target

.PHONY: test
test: $(DEV_REQUIREMENTS_TIMESTAMP)
	mkdir -p $(TEST_REPORT_DIR)
	$(NOSE) -v -c tests/unittest.cfg --junit-xml-path $(TEST_REPORT_DIR)/$(TEST_REPORT_FILE) -s tests/


# Packaging target

.PHONY: package
package: $(PREP_PACKAGING_TIMESTAMP)
	$(PYTHON) -m build


.PHONY: publish
publish: clean-venv clean test package publish-check
	@echo "Tag and upload package version=$(PACKAGE_VERSION)"
	@# Check if we use interactive credentials or not
	@if [ -n "$(PYPI_PASSWORD)" ]; then \
	    python3 -m twine upload -u $(PYPI_USER) -p $(PYPI_PASSWORD) dist/*; \
	else \
	    python3 -m twine upload dist/*; \
	fi
	git tag -am $(PACKAGE_VERSION) $(PACKAGE_VERSION)
	git push origin $(PACKAGE_VERSION)


# Clean targets

.PHONY: clean-venv
clean-venv:
	if [ -e $(VENV)/bin/deactivate ]; then $(VENV)/deactivate; fi
	rm -rf $(VENV)


.PHONY: clean
clean:
	@# clean python cache files
	find . -name __pycache__ -type d -print0 | xargs -I {} -0 rm -rf "{}"
	rm -rf $(PYTHON_LOCAL_DIR)
	rm -rf $(TEST_REPORT_DIR)
	rm -rf $(TIMESTAMPS)
	rm -rf dist
	rm -rf build
	rm -rf *.egg-info
	rm -f .coverage


.PHONY: clean-all
clean-all: clean clean-venv


# Actual builds targets with dependencies

$(TIMESTAMPS):
	mkdir -p $(TIMESTAMPS)


$(VENV_TIMESTAMP):
	test -d $(VENV) || $(SYSTEM_PYTHON) -m venv $(VENV) && $(PIP) install --upgrade pip setuptools
	@touch $(VENV_TIMESTAMP)


$(DEV_REQUIREMENTS_TIMESTAMP): $(VENV_TIMESTAMP) $(DEV_REQUIREMENTS)
	$(PIP) install -r $(DEV_REQUIREMENTS)
	@touch $(DEV_REQUIREMENTS_TIMESTAMP)


$(PREP_PACKAGING_TIMESTAMP): $(TIMESTAMPS)
	python3 -m pip install --user --upgrade setuptools wheel twine
	@touch $(PREP_PACKAGING_TIMESTAMP)


publish-check:
	@echo "Check if publish is allowed"
	@if [ -n "`git status --porcelain`" ]; then echo "ERROR: Repo is dirty !" >&2; exit 1; fi
	@# "Check if TAG=${PACKAGE_VERSION} already exits"
	@if [ -n "`git ls-remote --tags --refs origin refs/tags/${PACKAGE_VERSION}`" ]; then \
		echo "ERROR: Tag ${PACKAGE_VERSION} already exists on remote" >&2;  \
		exit 1; \
	fi
