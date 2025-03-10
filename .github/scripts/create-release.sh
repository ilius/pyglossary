VERSION=$(./scripts/version-core)
if pip index versions pyglossary --pre --ignore-requires-python | grep "$VERSION,"; then
	echo "Package version $VERSION already exists on pypi"
	echo "skipnext=true" >>$GITHUB_OUTPUT
	exit 0
fi
sudo rm -rf dist/* build/* || true
python3 setup.py sdist bdist_wheel
