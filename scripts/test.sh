#!/usr/bin/env bash
set -e

rootDir=$(dirname $(dirname "$0"))
rootDirAbs=$(realpath $rootDir)

echo "$rootDir/tests"
cd "$rootDir/tests"
# python -m unittest *_test.py
for F in *_test.py; do
	echo "$F"
	python -m unittest "$F"
done

echo "$rootDirAbs/tests/deprecated/"
cd "$rootDirAbs/tests/deprecated/"
for F in *_test.py; do
	echo "$F"
	python -W ignore::DeprecationWarning -m unittest "$F"
done
