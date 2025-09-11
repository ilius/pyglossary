#!/usr/bin/env bash
set -e

rootDir=$(dirname $(dirname "$0"))
rootDirAbs=$(realpath $rootDir)

echo "$rootDirAbs/tests/deprecated/"
cd "$rootDirAbs/tests/deprecated/"

if [ -z "$TEST_VERBOSE" ] ; then
	python -W ignore::DeprecationWarning -m unittest *_test.py
	exit 0
fi

for F in *_test.py; do
	echo "$F"
	python -W ignore::DeprecationWarning -m unittest "$F"
done
