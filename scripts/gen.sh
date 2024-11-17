#!/usr/bin/env bash
set -e

myDir1=$(dirname "$0")

set -x

python "$myDir1/plugin-index.py"
python "$myDir1/plugin-doc.py"

python "$myDir1/config-doc.py"
python "$myDir1/entry-filters-doc.py"
