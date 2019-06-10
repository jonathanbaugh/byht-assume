#!/usr/bin/env sh

PYTHON_PATH=~/.byht/cache/assume/venv/bin/python3

if [[ $@ == *"--help"* ]]; then
  $PYTHON_PATH $BYHT_DIR_CACHE/assume/assume.py $@
else
  $($PYTHON_PATH $BYHT_DIR_CACHE/assume/assume.py $@)
fi
