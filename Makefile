SHELL = /bin/bash

.DEFAULT_GOAL := help


CURRENT_DIR := $(shell pwd)

# Test reports configuration
TEST_REPORT_DIR ?= $(CURRENT_DIR)/tests/report
TEST_REPORT_FILE ?= nose2-junit.xml

# general targets timestamps
TIMESTAMPS = .timestamps
REQUIREMENTS := $(TIMESTAMPS) $(PIP_FILE) $(PIP_FILE_LOCK)

# Find all python files that are not inside a hidden directory (directory starting with .)
PYTHON_FILES := $(shell find ./* -type d \( -path ./build -o -path ./dist \) -prune -false -o -type f -name "*.py" -print)

# PIPENV files
PIP_FILE = Pipfile
PIP_FILE_LOCK = Pipfile.lock

# default configuration
ENV_FILE ?= .env.local

# Commands
PIPENV_RUN := pipenv run
PYTHON := $(PIPENV_RUN) python3
PIP := $(PIPENV_RUN) pip3
YAPF := $(PIPENV_RUN) yapf
ISORT := $(PIPENV_RUN) isort
NOSE := $(PIPENV_RUN) nose2
PYLINT := $(PIPENV_RUN) pylint

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
	@echo "- python-version     Show python version"


# Build targets. Calling setup is all that is needed for the local files to be installed as needed.

.PHONY: setup
setup: $(REQUIREMENTS)
		pipenv install --dev
		pipenv shell

# linting target, calls upon yapf to make sure your code is easier to read and respects some conventions.

.PHONY: format
format: $(REQUIREMENTS)
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
lint: $(REQUIREMENTS)
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
package: $(DEV_REQUIREMENTS_TIMESTAMP)
	$(PYTHON) -m build


.PHONY: publish
publish: clean-all publish-check package
	@echo "Upload package version=$(PACKAGE_VERSION)"
	$(PYTHON) -m twine upload dist/*


# Clean targets

.PHONY: clean-venv
clean-venv:
	pipenv --rm

.PHONY: clean
clean: clean-venv
	@# clean python cache files
	find . -name __pycache__ -type d -print0 | xargs -I {} -0 rm -rf "{}"
	rm -rf $(TEST_REPORT_DIR)
	rm -rf $(TIMESTAMPS)
	rm -rf dist
	rm -rf build
	rm -rf *.egg-info
	rm -f .coverage

.PHONY: clean-all
clean-all: clean

.PHONY: python-version
python-version:
	$(PYTHON) python --version



# Actual builds targets with dependencies

$(TIMESTAMPS):
	mkdir -p $(TIMESTAMPS)


$(VENV_TIMESTAMP):
	test -d $(VENV) || $(SYSTEM_PYTHON) -m venv $(VENV) && $(PIP) install --upgrade pip setuptools
	@touch $(VENV_TIMESTAMP)


$(DEV_REQUIREMENTS_TIMESTAMP): $(VENV_TIMESTAMP) $(DEV_REQUIREMENTS)
	$(PIP) install -r $(DEV_REQUIREMENTS)
	@touch $(DEV_REQUIREMENTS_TIMESTAMP)


publish-check:
	@echo "Check if publish is allowed"
	@if [ -n "`git status --porcelain`" ]; then echo "ERROR: Repo is dirty !" >&2; exit 1; fi
