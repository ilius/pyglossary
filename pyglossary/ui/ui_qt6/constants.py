# mypy: ignore-errors
#
# Copyright © 2026 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
#
# This program is a free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.

from __future__ import annotations

from pyglossary.glossary_v2 import Glossary

__all__ = [
	"INPUT_FILE_DIALOG_USE_NON_NATIVE_QT",
	"OUTPUT_DIR_CUSTOM",
	"PATH_BTN_EMPTY",
	"PLUGIN_BY_DESC",
	"READ_DESC",
	"WRITE_DESC",
]

OUTPUT_DIR_CUSTOM = "Custom directory…"
PATH_BTN_EMPTY = "[Select...]"
PLUGIN_BY_DESC = {p.description: p for p in Glossary.plugins.values()}
READ_DESC = [p.description for p in Glossary.plugins.values() if p.canRead]
WRITE_DESC = [p.description for p in Glossary.plugins.values() if p.canWrite]

# When True (default): input browsing uses Qt's non-native dialog so the current path
# can be pre-selected (macOS NSSavePanel/Qt native often ignores QFileDialog.selectFile).
# When False: use the platform native file panel; opens in the right folder only.
INPUT_FILE_DIALOG_USE_NON_NATIVE_QT = True
