#!/usr/bin/env bash
set -e

# l_name of plugin, for example "stardict" or "octopus_mdict"
pluginLname="$1"


myPath=$(realpath "$0")
myDir1=$(dirname "$myPath")
rootDir=$(dirname "$myDir1")

cd "$rootDir/tests"
coverage run -m unittest "g_${pluginLname}_test.py"
coverage html --include="$rootDir/pyglossary/plugins/${pluginLname}*"
