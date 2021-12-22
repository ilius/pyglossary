#!/usr/bin/env bash
set -e

myPath=$(realpath "$0")
myDir1=$(dirname "$myPath")
myDir2=$(dirname "$myDir1")
srcDir="$myDir2/pyglossary"

cd "$srcDir"
coverage run -m unittest *_test.py */*_test.py */*/*_test.py
coverage html
