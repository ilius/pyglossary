#!/usr/bin/env bash
# Self-contained build script for the macOS Slint-UI build of PyGlossary.
#
# Usage: build.sh [stage]
#   stage: uv | venv | deps-brew | deps-python | patch | nuitka-build |
#          copy-assets | dmg | all (default)
#
# Unlike scripts/ci/mac/ (tk build, split across 5 files), this keeps every
# stage in one script and computes its own brew/compiler env vars per-stage,
# so it does not depend on a prior GitHub Actions step exporting them into
# $GITHUB_ENV -- it also runs standalone locally via `make -C scripts/ci/mac-slint`.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
cd "$REPO_ROOT"

APPNAME="${APPNAME:-PyGlossarySlint}"
DIST_DIR="${DIST_DIR:-dist.nuitka.slint}"
MAIN_SCRIPT="${MAIN_SCRIPT:-main.py}"
SLINT_VERSION="${SLINT_VERSION:-1.17.0b2}"
PYTHON_VERSION="${PYTHON_VERSION:-3.13}"

ARCH="$(uname -m)"
OS_TAG="macos-${ARCH}-$(sw_vers -productVersion)"
VERSION="$(git describe --abbrev=1)"
VERSION_WITH_HASH="$(git describe)"

log() { echo "[mac-slint] $*"; }

# Exports compiler/linker flags for the brew-installed native deps
# (icu4c, lzo, libffi) needed to build PyICU / python-lzo from source
# and to link them into the nuitka standalone binary.
resolve_brew_env() {
	BREW_PREFIX="$(brew --prefix)"
	PREFIX_ICU4C="$(brew --prefix icu4c)"
	PREFIX_LZO="$(brew --prefix lzo)"
	PREFIX_LIBFFI="$(brew --prefix libffi)"

	export PKG_CONFIG_PATH="${BREW_PREFIX}/lib/pkgconfig:${PREFIX_ICU4C}/lib/pkgconfig:${PREFIX_LZO}/lib/pkgconfig:${PREFIX_LIBFFI}/lib/pkgconfig"
	export LDFLAGS="-L${PREFIX_LIBFFI}/lib -L${PREFIX_ICU4C}/lib -L${PREFIX_LZO}/lib -L${BREW_PREFIX}/lib"
	export CPPFLAGS="-I${PREFIX_ICU4C}/include -I${PREFIX_LIBFFI}/include -I${PREFIX_LZO}/include"
	export DYLD_LIBRARY_PATH="${PREFIX_ICU4C}/lib:${PREFIX_LIBFFI}/lib:${PREFIX_LZO}/lib:${BREW_PREFIX}/lib"
	export CC=clang
	export CXX=clang++
}

step_uv() {
	command -v uv >/dev/null 2>&1 || {
		log "Installing uv..."
		curl -LsSf https://astral.sh/uv/install.sh | sh
	}
}

step_venv() {
	step_uv
	[ -d .venv ] || uv venv .venv --python "$PYTHON_VERSION"
}

# Only the native-toolchain deps required to build PyICU/python-lzo from
# source. No GUI toolkit (tk/qt/gtk/wx) packages -- the Slint build ships
# its own self-contained native widget renderer.
step_deps_brew() {
	log "Installing brew dependencies..."
	brew install libffi icu4c lzo pkg-config
}

step_deps_python() {
	step_uv
	resolve_brew_env
	# shellcheck disable=SC1091
	source .venv/bin/activate

	uv pip install -U nuitka
	uv pip install "slint==${SLINT_VERSION}"

	# Compiled plugin dependencies: static-link so the nuitka standalone
	# binary doesn't depend on brew's dylibs at runtime.
	STATIC_DEPS=true uv pip install --no-binary PyICU PyICU
	STATIC_DEPS=true uv pip install --no-binary python-lzo python-lzo

	uv pip install -r requirements.txt
}

step_patch() {
	log "Patching sources for nuitka build..."
	[ -n "$MAIN_SCRIPT" ]
	[ -n "$APPNAME" ]
	cp "$MAIN_SCRIPT" "${APPNAME}.py"
	rm -f __init__.py
	sed -i '' 's/default="auto"/default="slint"/' pyglossary/ui/argparse_main.py
}

step_nuitka_build() {
	resolve_brew_env
	# shellcheck disable=SC1091
	source .venv/bin/activate

	log "Env vars:"
	log "LDFLAGS: $LDFLAGS"
	log "CPPFLAGS: $CPPFLAGS"
	log "DYLD_LIBRARY_PATH: $DYLD_LIBRARY_PATH"

	python -m nuitka \
		--standalone \
		--assume-yes-for-downloads \
		--follow-imports \
		--macos-create-app-bundle \
		--macos-app-icon=res/pyglossary.icns \
		--macos-signed-app-name="$APPNAME" \
		--macos-app-name="$APPNAME" \
		--macos-app-mode=gui \
		--include-package=pyglossary \
		--include-package=slint \
		--include-package-data=slint \
		--nofollow-import-to=pyglossary.ui.ui_gtk \
		--nofollow-import-to=pyglossary.ui.ui_gtk4 \
		--nofollow-import-to=pyglossary.ui.ui_qt \
		--nofollow-import-to=pyglossary.ui.ui_qt6 \
		--nofollow-import-to=pyglossary.ui.ui_tk \
		--nofollow-import-to=pyglossary.ui.ui_tk_wizard \
		--nofollow-import-to=pyglossary.ui.ui_wx \
		--nofollow-import-to=tkinter \
		--nofollow-import-to=gi \
		--nofollow-import-to=gtk \
		--nofollow-import-to=wx \
		--nofollow-import-to=pyqt4 \
		--nofollow-import-to=pyqt5 \
		--nofollow-import-to=pyqt6 \
		--nofollow-import-to=PySide6 \
		--nofollow-import-to=*.tests \
		--noinclude-pytest-mode=nofollow \
		--noinclude-setuptools-mode=nofollow \
		--plugin-disable=pyqt5 \
		--include-module=pymorphy3 \
		--include-module=lxml \
		--include-module=polib \
		--include-module=yaml \
		--include-module=bs4 \
		--include-module=html5lib \
		--include-module=icu \
		--include-module=colorize_pinyin \
		--include-package-data=pyglossary \
		--include-data-files=about=about \
		--include-module=_json \
		--include-module=_bisect \
		--include-data-files=_license-dialog=_license-dialog \
		--include-data-dir=res=. \
		--include-data-files=_license-dialog=license-dialog \
		--nofollow-import-to=unittest \
		--output-dir="$DIST_DIR" \
		--output-filename="$APPNAME" \
		"${APPNAME}.py"
}

step_copy_assets() {
	log "Copying runtime assets into app bundle..."
	local target="${DIST_DIR}/${APPNAME}.app/Contents/MacOS"
	if [ ! -d "$target" ]; then
		echo "target_path not found: $target" >&2
		exit 1
	fi
	for src in about AUTHORS _license-dialog config.json plugins-meta help res pyglossary; do
		if [ ! -e "$src" ]; then
			echo "source not found: $src" >&2
			continue
		fi
		cp -R "$src" "$target/"
	done
}

step_dmg() {
	log "Creating DMG..."
	hdiutil create -verbose \
		-volname "${APPNAME}-${VERSION_WITH_HASH}" \
		-srcfolder "${DIST_DIR}/${APPNAME}.app" \
		-ov -format UDZO -fs HFS+J \
		"${APPNAME}-${VERSION}-${OS_TAG}.dmg"
}

step_all() {
	step_uv
	step_venv
	step_deps_brew
	step_deps_python
	step_patch
	step_nuitka_build
	step_copy_assets
	step_dmg
}

case "${1:-all}" in
	uv) step_uv ;;
	venv) step_venv ;;
	deps-brew) step_deps_brew ;;
	deps-python) step_deps_python ;;
	patch) step_patch ;;
	nuitka-build) step_nuitka_build ;;
	copy-assets) step_copy_assets ;;
	dmg) step_dmg ;;
	all) step_all ;;
	*)
		echo "Unknown stage: $1" >&2
		echo "Usage: $0 [uv|venv|deps-brew|deps-python|patch|nuitka-build|copy-assets|dmg|all]" >&2
		exit 1
		;;
esac
