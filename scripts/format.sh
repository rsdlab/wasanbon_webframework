#!/usr/bin/env bash

# set -e
set -x

black wasanbon_webframework tests
isort wasanbon_webframework tests
