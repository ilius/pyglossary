# -*- coding: utf-8 -*-
#
# Copyright © 2012-2022 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
# This file is part of PyGlossary project, https://github.com/ilius/pyglossary
#
# This program is a free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. Or on Debian systems, from /usr/share/common-licenses/GPL
# If not, see <http://www.gnu.org/licenses/gpl.txt>.

from __future__ import annotations

from pyglossary.entry_filters import entryFiltersRules
from pyglossary.option import (
	BoolOption,
	FloatOption,
	IntOption,
	Option,
	StrOption,
)

_entryFilterConfigDict = {
	configParam: (filterClass, default)
	for configParam, default, filterClass in entryFiltersRules
	if configParam
}


def getEntryFilterOption(name: str) -> Option:
	filterClass, default = _entryFilterConfigDict[name]
	if isinstance(default, bool):
		optClass = BoolOption
	elif isinstance(default, str):
		optClass = StrOption
	else:
		raise TypeError(f"{default = }")
	return optClass(
		hasFlag=True,
		comment=filterClass.desc,
		falseComment=filterClass.falseComment,
	)


configDefDict: dict[str, Option] = {
	"log_time": BoolOption(
		hasFlag=True,
		comment="Show date and time in logs",
		falseComment="Do not show date and time in logs",
	),
	"cleanup": BoolOption(
		hasFlag=True,
		comment="Cleanup cache or temporary files after conversion",
		falseComment=("Do not cleanup cache or temporary files after conversion",),
	),
	"auto_sqlite": BoolOption(
		hasFlag=False,
		comment=(
			"Auto-enable --sqlite to limit RAM usage when direct\n"
			"mode is not possible. Can override with --no-sqlite"
		),
	),
	"enable_alts": BoolOption(
		hasFlag=True,
		customFlag="alts",
		comment="Enable alternates",
		falseComment="Disable alternates",
	),
	# TODO: version 6.0: replace with "resources"
	# 	comment="Use resources (images, audio, etc)"
	"skip_resources": BoolOption(
		hasFlag=True,
		comment="Skip resources (images, audio, css, etc)",
	),
	"save_info_json": BoolOption(
		hasFlag=True,
		customFlag="info",
		comment="Save .info file alongside output file(s)",
	),
	"lower": getEntryFilterOption("lower"),
	"utf8_check": getEntryFilterOption("utf8_check"),
	"rtl": getEntryFilterOption("rtl"),
	"remove_html": getEntryFilterOption("remove_html"),
	"remove_html_all": getEntryFilterOption("remove_html_all"),
	"normalize_html": getEntryFilterOption("normalize_html"),
	"skip_duplicate_headword": getEntryFilterOption("skip_duplicate_headword"),
	"trim_arabic_diacritics": getEntryFilterOption("trim_arabic_diacritics"),
	"unescape_word_links": getEntryFilterOption("unescape_word_links"),
	"color.enable.cmd.unix": BoolOption(
		hasFlag=False,
		comment="Enable colors in Linux/Unix command line",
	),
	"color.enable.cmd.windows": BoolOption(
		hasFlag=False,
		comment="Enable colors in Windows command line",
	),
	"color.cmd.critical": IntOption(
		hasFlag=False,
		comment="Color code for critical errors in command line",
	),
	"color.cmd.error": IntOption(
		hasFlag=False,
		comment="Color code for errors in command line",
	),
	"color.cmd.warning": IntOption(
		hasFlag=False,
		comment="Color code for warnings in command line",
	),
	# interactive command line interface:
	"cmdi.prompt.indent.str": StrOption(hasFlag=False),
	"cmdi.prompt.indent.color": IntOption(hasFlag=False),
	"cmdi.prompt.msg.color": IntOption(hasFlag=False),
	"cmdi.msg.color": IntOption(hasFlag=False),
	# general GUI options
	"ui_autoSetFormat": BoolOption(hasFlag=False),
	# Tkinter
	"tk.progressbar.color.fill": StrOption(
		hasFlag=False,
		comment="Tkinter: progressbar fill color",
	),
	"tk.progressbar.color.background": StrOption(
		hasFlag=False,
		comment="Tkinter: progressbar background color",
	),
	"tk.progressbar.color.text": StrOption(
		hasFlag=False,
		comment="Tkinter: progressbar text color",
	),
	"tk.progressbar.font": StrOption(
		hasFlag=False,
		comment='Tkinter: progressbar text font. Example: "Sans", "Sans 15"',
	),
	# Reverse
	"reverse_matchWord": BoolOption(hasFlag=False),
	"reverse_showRel": StrOption(hasFlag=False),
	"reverse_saveStep": IntOption(hasFlag=False),
	"reverse_minRel": FloatOption(hasFlag=False),
	"reverse_maxNum": IntOption(hasFlag=False),
	"reverse_includeDefs": BoolOption(hasFlag=False),
}
