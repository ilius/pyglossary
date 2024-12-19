#!/usr/bin/env bash
set -e

pluginLookup="$1"
if [ -z "$pluginLookup" ]; then
	echo 'Must give plugins l_name as argument, for example "stardict" or "octopus_mdict"'
	exit 1
fi

rootDir=$(dirname $(realpath $(dirname "$0")))
echo $rootDir

cd $rootDir/pyglossary/plugins/
pluginLname=$(ls -1d $pluginLookup* | grep -v 'cover' | sort | head -n1 | sed 's/\.py$//')
if [ -z "$pluginLname" ]; then
	echo "Did not find a plugin matching '$pluginLookup'"
	exit 1
fi

if [ -f "$rootDir/pyglossary/plugins/${pluginLname}.py" ]; then
	filePaths="$rootDir/pyglossary/plugins/${pluginLname}.py"
elif [ -d "$rootDir/pyglossary/plugins/${pluginLname}" ]; then
	filePaths="$rootDir/pyglossary/plugins/${pluginLname}/*.py"
else
	echo "Did not find a plugin matching '$pluginLookup'"
	exit 1
fi

echo "Using plugin name '$pluginLname'"

dataFile="$rootDir/pyglossary/plugins/${pluginLname}.cover"

outDir="$rootDir/pyglossary/plugins/${pluginLname}.coverhtml"
mkdir -p $outDir
# echo "file://$outDir/index.html"

cd "$rootDir/tests"

set -x
coverage run --data-file="$dataFile" -m unittest "g_${pluginLname}_test.py"
coverage html --data-file="$dataFile" \
	--include="$filePaths" \
	--directory=$outDir ||
	echo "'coverage html' failed with $?"
set +x

if [ -f "$outDir/index.html" ]; then
	echo "file://$outDir/index.html"
fi
