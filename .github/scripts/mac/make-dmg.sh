#!/usr/bin/env bash
APPNAME="$1"
DIST_DIR="$2"
OS="$3"
VERSION="$4"
VERSION_WITH_HASH="$5"
# NOTE: using create-dmg might make smaller size DMGs
# create-dmg --no-internet-enable --volname "${APPNAME}-${VERSION}" --volicon res/pyglossary.icns --eula LICENSE  --app-drop-link 50 50 "$APPNAME-${OS}-${VERSION_WITH_HASH}.dmg" "${DIST_DIR}/${APPNAME}.app"
hdiutil create -verbose -volname "$APPNAME-$VERSION_WITH_HASH" -srcfolder "$DIST_DIR/$APPNAME.app" -ov -format UDZO -fs HFS+J "$APPNAME-$VERSION-$OS.dmg"
