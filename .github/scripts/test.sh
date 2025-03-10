set -x
set +e

export NO_CLEANUP=1

set -o pipefail
bash ./scripts/test.sh 2>&1 | tee test.out
STATUS=$?
set +o pipefail

mkdir artifacts
cp test.out artifacts
grep -o "'/tmp/pyglossary/[^']*'" test.out | sed "s/'//g" | xargs '-I{}' cp '{}' artifacts
ls -l artifacts
set -e
exit $STATUS
