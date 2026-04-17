#!/usr/bin/env bash
set -e

rootDir=$(dirname $(dirname "$0"))

uiTestsDir="$rootDir/pyglossary/ui/tests"
echo "$uiTestsDir"
cd "$uiTestsDir"
if [ -z "$TEST_VERBOSE" ] ; then
	python -m unittest *_test.py
	exit 0
fi
for F in *_test.py; do
	echo "$F"
	python -m unittest "$F"
done
