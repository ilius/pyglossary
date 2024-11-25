#!/bin/bash
set -e
set -x

function yes_or_no {
	while true; do
		read -p "$* [y/n]: " yn
		case $yn in
		[Yy]*) return 0 ;;
		[Nn]*)
			echo "Aborted"
			return 1
			;;
		esac
	done
}

VERSION=$1
if [ -z $VERSION ]; then
	echo "Usage: $0 VERSION"
	exit 1
fi

$(dirname $0)/version-set.py $VERSION

sudo rm -rf dist build
mkdir dist build
python3 setup.py sdist bdist_wheel
pip3 install ./dist/*.whl -U --user --force-reinstall
du -k dist/*

echo "-------------- Check version in GUI: --------------"

~/.local/bin/pyglossary

yes_or_no "Continue creating the release?" || exit 1

git add setup.py pyglossary/core.py pyproject.toml
git commit -m "version $VERSION" || echo "------ Already committed"
git -p show || true
git -p log || true

echo "Pushing to origin..."
git push

echo "Creating tag $VERSION"
git tag -a -m "version $VERSION" $VERSION

echo "Pushing tag to origin..."
git push origin $VERSION

echo "Publishing to pypi"
python3 -m twine upload --repository pypi dist/* --verbose
