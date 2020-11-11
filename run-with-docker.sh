#!/bin/bash
set -e

myPath=$(realpath "$0")
myDir=$(dirname "$myPath")
cd "$myDir"

version=$(./scripts/version)
echo $version

aptCacheDir=$HOME/.minideb-apt
mkdir -p "$aptCacheDir"

docker build . \
	-f Dockerfile \
	-t pyglossary:$version \
	-t pyglossary:latest

docker run -it \
	--volume $HOME:/root/ \
	--volume $aptCacheDir:/var/cache/apt \
	pyglossary:$version
