#!/usr/bin/env bash
set -e

# args: macos-14

OS="$1"

[ -n "$APPNAME" ]
[ -n "$DIST_DIR" ]
[ -n "$VERSION" ]
[ -n "$VERSION_WITH_HASH" ]


# NOTE: using create-dmg might make smaller size DMGs
# create-dmg --no-internet-enable --volname "${APPNAME}-${VERSION}" --volicon res/pyglossary.icns --eula LICENSE  --app-drop-link 50 50 "$APPNAME-${OS}-${VERSION_WITH_HASH}.dmg" "${DIST_DIR}/${APPNAME}.app"
hdiutil create -verbose -volname "$APPNAME-$VERSION_WITH_HASH" -srcfolder "$DIST_DIR/$APPNAME.app" -ov -format UDZO -fs HFS+J "$APPNAME-$VERSION-$OS.dmg"
