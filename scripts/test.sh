#!/usr/bin/env bash
set -e

myPath=$(realpath "$0")
myDir1=$(dirname "$myPath")
rootDir=$(dirname "$myDir1")

echo "$rootDir/tests"
cd "$rootDir/tests"
# python -m unittest *_test.py
for F in *_test.py ; do
	echo "$F"
    python -m unittest "$F"
done
