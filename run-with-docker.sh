#!/bin/bash
set -e

function shouldBuild() {
	imageName=$1
	if [ "$REBUILD" = 1 ] ; then
		return 0
	fi
	imageCreated=$(docker inspect -f '{{ .Created }}' "$imageName" 2>/dev/null)
	if [ -z "$imageCreated" ] ; then
		return 0
	fi
	imageAge=$(($(/bin/date +%s) - $(/bin/date +%s -d "$imageCreated")))
	if [ -z "$imageAge" ] ; then
		return 0
	fi
	echo "Existing $imageName image is $imageAge seconds old"
	if [[ "$imageAge" -gt 604800 ]] ; then
		# more than a week old
		return 0
	fi
	return 1
}

myPath=$(realpath "$0")
myDir=$(dirname "$myPath")
cd "$myDir"

if [ -n "$1" ] ; then
	version="$1"
else
	version=$(./scripts/version)
fi
echo "PyGlossary version: $version"

set -x

#./scripts/create-conf-dir.py

if shouldBuild "pyglossary:$version" ; then
	docker build . -f Dockerfile -t "pyglossary:$version" -t pyglossary:latest
fi

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
    --user "$(id -u):$(id -g)" \
	--volume "$HOME:/home/$USER" \
	--env "HOME=/home/$USER" \
    --workdir "/home/$USER" \
	"pyglossary:$version"
