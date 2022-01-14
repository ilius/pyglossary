#!/usr/bin/env bash
set -e

myPath=$(realpath "$0")
myDir1=$(dirname "$myPath")
rootDir=$(dirname "$myDir1")

find "$rootDir/tests" -name "*_test.py" -print -exec python3 '{}' \;

find "$rootDir/pyglossary/plugin_lib" -name "*_test.py" -print -exec python3 '{}' \;
