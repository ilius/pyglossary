#!/usr/bin/env bash
set -e

pluginLname="$1"
if [ -z "$pluginLname" ]; then
	echo 'Must give plugins l_name as argument, for example "stardict" or "octopus_mdict"'
	exit 1
fi

rootDir=$(dirname $(realpath $(dirname "$0")))
echo $rootDir

dataFile="$rootDir/pyglossary/plugins/${pluginLname}.coverage"

outDir="$rootDir/pyglossary/plugins/${pluginLname}.htmlcov"
mkdir -p $outDir
# echo "file://$outDir/index.html"

cd "$rootDir/tests"

set -x
coverage run --data-file="$dataFile" -m unittest "g_${pluginLname}_test.py"
coverage html --data-file="$dataFile" \
	--include="$rootDir/pyglossary/plugins/${pluginLname}*" \
	--directory=$outDir ||
	echo "'coverage html' failed with $?"
set +x

if [ -f "$outDir/index.html" ]; then
	echo "file://$outDir/index.html"
fi
