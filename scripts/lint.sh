#!/usr/bin/env bash

# set -e
set -x

mypy wasanbon_webframework tests
pflake8 wasanbon_webframework tests
black wasanbon_webframework tests --check
isort wasanbon_webframework tests --check-only
