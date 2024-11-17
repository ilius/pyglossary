#!/usr/bin/env bash
set -e

rootDir=$(dirname $(dirname "$0"))

echo "$rootDir/tests/glossary_test.py"
python3 "$rootDir/tests/glossary_test.py"

find "$rootDir/tests" -name "g_*_test.py" -print -exec python3 '{}' \;
