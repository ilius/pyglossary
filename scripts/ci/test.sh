set -x
set +e

export NO_CLEANUP=1
export TEST_REDOWNLOAD_OUTDATED_CACHE=1

# rm -rf $HOME/.cache/pyglossary/test || true

export TEST_VERBOSE=1

set -o pipefail
bash ./scripts/test.sh 2>&1 | tee test.out
STATUS=$?
bash ./scripts/test-ui.sh 2>&1 | tee -a test.out
UI_STATUS=$?
set +o pipefail

mkdir artifacts
cp test.out artifacts
grep -v FileNotFoundError test.out | grep -o "'/tmp/pyglossary/[^']*'" | sed "s/'//g" | xargs '-I{}' cp '{}' artifacts
ls -l artifacts
set -e
if [ "$STATUS" -ne 0 ] || [ "$UI_STATUS" -ne 0 ]; then
	exit 1
fi
exit 0
