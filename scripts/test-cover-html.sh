#!/usr/bin/env bash
set -e

rootDir=$(dirname $(realpath $(dirname "$0")))
echo "file://$rootDir/tests/htmlcov/index.html"

cd "$rootDir/tests"
coverage run -m unittest ./*_test.py
coverage html --include="$rootDir/pyglossary/*" --omit="$rootDir/pyglossary/plugin_lib/*" || echo "'coverage html' failed with $?"

echo "file://$rootDir/tests/htmlcov/index.html"
