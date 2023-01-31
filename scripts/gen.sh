#!/usr/bin/env bash
set -e

myPath=$(realpath "$0")
myDir1=$(dirname "$myPath")

set -x

python "$myDir1/plugin-index.py"
python "$myDir1/plugin-doc.py"

python "$myDir1/config-doc.py"
python "$myDir1/entry-filters-doc.py"
