#!/usr/bin/env bash
set -e

rootDir=$(dirname $(dirname "$0"))

cd "$rootDir/tests"
coverage run -m unittest ./*_test.py
coverage html --include="$rootDir/pyglossary/*" --omit="$rootDir/pyglossary/plugin_lib/*"

echo "file://$rootDir/tests/htmlcov/index.html"
