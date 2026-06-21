#!/usr/bin/env bash
set -e

rootDir=$(git rev-parse --show-toplevel)
artifactDir="$rootDir/artifacts/coverage"
mkdir -p "$artifactDir"

dataMain="$rootDir/.coverage.main"
dataUi="$rootDir/.coverage.ui"
dataCombined="$rootDir/.coverage"
include="$rootDir/pyglossary/*"
omit="$rootDir/pyglossary/plugin_lib/*"
uiTestsOmit="*/pyglossary/ui/tests/*"
wcwidthOmit="*/pyglossary/ui/wcwidth/*"
reportOpts=(
	--include="$include"
	--omit="$omit"
	--omit="$uiTestsOmit"
	--omit="$wcwidthOmit"
)

rm -f "$dataMain" "$dataUi" "$dataCombined"

cd "$rootDir/tests"
coverage run --data-file="$dataMain" -m unittest ./*_test.py

cd "$rootDir"
coverage run --data-file="$dataUi" --source=pyglossary.ui \
	--omit="$uiTestsOmit" \
	--omit="$wcwidthOmit" \
	-m unittest discover -s pyglossary/ui/tests -p '*_test.py'

mainTotal=$(coverage report --data-file="$dataMain" --format=total "${reportOpts[@]}")
uiTotal=$(coverage report --data-file="$dataUi" --format=total \
	--omit="$uiTestsOmit" \
	--omit="$wcwidthOmit")
coverage combine --data-file="$dataCombined" "$dataMain" "$dataUi"
combinedTotal=$(coverage report --data-file="$dataCombined" --format=total "${reportOpts[@]}")

printf '{"main":%s,"ui":%s,"combined":%s}\n' \
	"$mainTotal" "$uiTotal" "$combinedTotal" > "$artifactDir/summary.json"

if [ -z "${COVERAGE_SKIP_HTML:-}" ]; then
	coverage report --data-file="$dataCombined" --show-missing "${reportOpts[@]}" \
		> "$artifactDir/coverage.txt"
	coverage html --data-file="$dataCombined" "${reportOpts[@]}" \
		-d "$artifactDir/htmlcov"
fi

ls -lR "$artifactDir"
