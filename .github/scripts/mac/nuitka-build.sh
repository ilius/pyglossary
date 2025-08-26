#!/usr/bin/env bash

source .venv/bin/activate

# Architecture-specific flags
if [ "$(uname -m)" = "arm64" ]; then
  ARCH_FLAGS="--target-arch=arm64"
else
  ARCH_FLAGS="--target-arch=x86_64"
fi

# Ensure library paths are set for nuitka - use properly formatted paths
export DYLD_LIBRARY_PATH="${PREFIX_ICU4C}/lib:${PREFIX_LIBFFI}/lib:${PREFIX_LZO}/lib:${BREW_PREFIX}/lib"
export LDFLAGS="-L${PREFIX_LIBFFI}/lib -L${PREFIX_ICU4C}/lib -L${PREFIX_LZO}/lib -L${BREW_PREFIX}/lib"
export CPPFLAGS="-I${PREFIX_ICU4C}/include -I${PREFIX_LIBFFI}/include -I${PREFIX_LZO}/include"
export PKG_CONFIG_PATH="${BREW_PREFIX}/lib/pkgconfig:${PREFIX_ICU4C}/lib/pkgconfig:${PREFIX_LZO}/lib/pkgconfig:${PREFIX_LIBFFI}/lib/pkgconfig"
export CC=clang
export CXX=clang++

echo "Env vars:"
echo "LDFLAGS: $LDFLAGS"
echo "CPPFLAGS: $CPPFLAGS"
echo "DYLD_LIBRARY_PATH: $DYLD_LIBRARY_PATH"

rm -rf "$DIST_DIR"

echo TODO FIXME DEBUG langs wtf
echo PWD: "$PWD"
find . -iname langs -exec ls -lahO {} \;


python -m nuitka \
  --standalone \
  --assume-yes-for-downloads \
  --follow-imports \
  --macos-create-app-bundle \
  --macos-app-icon=res/pyglossary.icns \
  --macos-signed-app-name="$APPNAME" \
  --macos-app-name="$APPNAME" \
  --macos-app-mode=gui \
  --enable-plugin=tk-inter \
  --include-package=pyglossary \
  --include-module=tkinter \
  --nofollow-import-to=pyglossary.ui.ui_gtk \
  --nofollow-import-to=pyglossary.ui.ui_gtk4 \
  --nofollow-import-to=pyglossary.ui.ui_qt \
  --nofollow-import-to=gi \
  --nofollow-import-to=gtk \
  --nofollow-import-to=pyqt4 \
  --nofollow-import-to=pyqt5 \
  --nofollow-import-to=pyqt6 \
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
  --noinclude-custom-mode=unittest:nofollow \
  --output-dir="$DIST_DIR" \
  --output-filename=$APPNAME \
  $APPNAME.py
