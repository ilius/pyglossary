#!/usr/bin/env bash
set -e

# l_name of plugin, for example "stardict" or "octopus_mdict"
pluginLname="$1"

rootDir=$(dirname $(dirname "$0"))

cd "$rootDir/tests"
coverage run -m unittest "g_${pluginLname}_test.py"
coverage html --include="$rootDir/pyglossary/plugins/${pluginLname}*"
