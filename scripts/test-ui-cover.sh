#!/usr/bin/env bash
set -e

rootDir=$(dirname $(realpath $(dirname "$0")))
uiTestsDir="$rootDir/pyglossary/ui/tests"
uiTestsOmit="*/pyglossary/ui/tests/*"
wcwidthOmit="*/pyglossary/ui/wcwidth/*"

cd "$rootDir"
coverage run --source=pyglossary.ui \
	--omit="$uiTestsOmit" \
	--omit="$wcwidthOmit" \
	-m unittest discover -s pyglossary/ui/tests -p '*_test.py'
coverage report --show-missing \
	--omit="$uiTestsOmit" \
	--omit="$wcwidthOmit"
coverage html \
	--omit="$uiTestsOmit" \
	--omit="$wcwidthOmit" \
	-d "$uiTestsDir/htmlcov" || echo "'coverage html' failed with $?"

echo "file://$uiTestsDir/htmlcov/index.html"
