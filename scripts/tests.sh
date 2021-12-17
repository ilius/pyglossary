#!/usr/bin/env bash
set -e

myPath=$(realpath "$0")
myDir1=$(dirname "$myPath")
myDir2=$(dirname "$myDir1")
srcDir="$myDir2/pyglossary"

find "$srcDir" -name "*_test.py" -exec python3 '{}' \;
