#!/usr/bin/env bash
set -e

pluginLname="$1"
if [ -z "$pluginLname" ]; then
	echo 'Must give plugins l_name as argument, for example "stardict" or "octopus_mdict"'
	exit 1
fi

rootDir=$(dirname $(realpath $(dirname "$0")))
echo $rootDir

cd "$rootDir/tests"
coverage run -m unittest "g_${pluginLname}_test.py"
coverage html \
	--include="$rootDir/pyglossary/plugins/${pluginLname}.py" \
	--include="$rootDir/pyglossary/plugins/${pluginLname}/*.py" ||
	echo "'coverage html' failed with $?"

echo "file://$rootDir/tests/htmlcov/index.html"
