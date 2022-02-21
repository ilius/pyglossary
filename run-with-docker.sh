#!/bin/bash
set -e

myPath=$(realpath "$0")
myDir=$(dirname "$myPath")
cd "$myDir"

version=$(./scripts/version)
echo "PyGlossary version: $version"

set -x

./scripts/create-conf-dir.py

docker build . -f Dockerfile -t pyglossary:$version

docker tag pyglossary:$version pyglossary:latest

#cacheDir="$HOME/.cache/minideb"
#mkdir -p "$cacheDir/var_cache"
#mkdir -p "$cacheDir/usr_local_lib"
#echo "Docker's cache is being stored in $cacheDir"

#docker run -it \
#	--volume $cacheDir/var_cache:/var/cache \
#	--volume $cacheDir/usr_local_lib:/usr/local/lib \
#	--volume $HOME:/root/ \
#	pyglossary:$version \
#	bash -c '/opt/pyglossary/scripts/docker-deb-setup.sh; python3 /opt/pyglossary/main.py --cmd'

#	/opt/pyglossary/scripts/docker-deb-setup.sh

#imageId=$(docker images -q pyglossary:$version)
#docker commit $imageId pyglossary:$version || true
# FIXME: gives error: container not found

docker run -it \
	--volume /root:/root/ \
	--volume $HOME:/root/home \
	pyglossary:$version
