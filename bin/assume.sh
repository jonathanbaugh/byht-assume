#!/usr/bin/env sh

PYTHON_PATH=~/.byht/cache/assume/venv/bin/python3

if [[ $@ == *"--help"* ]]; then
  $PYTHON_PATH ~/.byht/cache/assume/assume.py $@
else
  $($PYTHON_PATH ~/.byht/cache/assume/assume.py $@)
fi
