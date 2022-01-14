#!/usr/bin/env bash
set -e

myPath=$(realpath "$0")
myDir1=$(dirname "$myPath")
rootDir=$(dirname "$myDir1")

echo "$rootDir/pyglossary/glossary_test.py"
python3 "$rootDir/pyglossary/glossary_test.py"

find "$rootDir/tests" -name "g_*_test.py" -print -exec python3 '{}' \;
