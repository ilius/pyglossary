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
