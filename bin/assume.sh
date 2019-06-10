#!/usr/bin/env sh

BASEDIR=$(dirname $0)
PYTHON_PATH=$BASEDIR/../venv/bin/python3

$($PYTHON_PATH $BASEDIR/../assume.py $@)
