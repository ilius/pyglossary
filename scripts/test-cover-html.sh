#!/usr/bin/env bash
set -e

myPath=$(realpath "$0")
myDir1=$(dirname "$myPath")
rootDir=$(dirname "$myDir1")

cd "$rootDir/tests"
coverage run -m unittest ./*_test.py
coverage html --include="$rootDir/pyglossary/*" --omit="$rootDir/pyglossary/plugin_lib/*"

echo "file://$rootDir/tests/htmlcov/index.html"
