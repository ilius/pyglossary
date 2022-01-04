#!/usr/bin/env bash
set -e

myPath=$(realpath "$0")
myDir1=$(dirname "$myPath")

set -x
"$myDir1/config-doc.py"
"$myDir1/entry-filters-doc.py"
"$myDir1/plugin-doc.py"
"$myDir1/plugin-index.py"
