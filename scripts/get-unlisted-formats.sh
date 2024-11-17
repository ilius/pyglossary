#!/usr/bin/env bash
set -e

rootDir=$(dirname $(dirname "$0"))

mkdir -p "$HOME/.cache/pyglossary/tmp"
cd "$HOME/.cache/pyglossary/tmp"
grep -oP 'doc/p/.*?\.md' "$rootDir/README.md" | sed 's|.*/||' | sort | uniq >formats-1

grep -oP '/.*?\.md' "$rootDir/doc/p/__index__.md" | sed 's|.*/||' | sort >formats-2

diff formats-1 formats-2 || true

rm formats-1 formats-2
