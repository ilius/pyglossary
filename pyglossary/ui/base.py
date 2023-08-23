# -*- coding: utf-8 -*-
# mypy: ignore-errors
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

import logging
from collections import OrderedDict
from os.path import isfile, join

from pyglossary.core import (
	appResDir,
	confJsonFile,
	dataDir,
	rootConfJsonFile,
)
from pyglossary.entry_filters import entryFiltersRules
from pyglossary.option import (
	BoolOption,
	FloatOption,
	IntOption,
	Option,
	StrOption,
)


def fread(path: str) -> str:
	with open(path, encoding="utf-8") as fp:
		return fp.read()


log = logging.getLogger("pyglossary")
logo = join(appResDir, "pyglossary.png")
aboutText = fread(join(dataDir, "about"))
licenseText = fread(join(dataDir, "license-dialog"))
authors = fread(join(dataDir, "AUTHORS")).split("\n")

summary = (
	"A tool for converting dictionary files aka glossaries with"
	" various formats for different dictionary applications"
)

_entryFilterConfigDict = {
	configParam: (filterClass, default)
	for configParam, default, filterClass in entryFiltersRules
	if configParam
}


def getEntryFilterConfigPair(name: str) -> "tuple[str, Option]":
	filterClass, default = _entryFilterConfigDict[name]
	if isinstance(default, bool):
		optClass = BoolOption
	elif isinstance(default, str):
		optClass = StrOption
	else:
		raise TypeError(f"{default = }")
	return name, optClass(
		hasFlag=True,
		comment=filterClass.desc,
		falseComment=filterClass.falseComment,
	)


class UIBase:
	configDefDict = OrderedDict([
		("log_time", BoolOption(
			hasFlag=True,
			comment="Show date and time in logs",
			falseComment="Do not show date and time in logs",
		)),
		("cleanup", BoolOption(
			hasFlag=True,
			comment="Cleanup cache or temporary files after conversion",
			falseComment="Do not cleanup cache or temporary files after conversion",
		)),

		("auto_sqlite", BoolOption(
			hasFlag=False,
			comment=(
				"Auto-enable --sqlite to limit RAM usage when direct\n"
				"mode is not possible. Can override with --no-sqlite"
			),
		)),
		("optimize_memory", BoolOption(
			hasFlag=True,
			comment=(
				"Optimize memory usage (over speed) in --indirect mode"
			),
		)),

		("enable_alts", BoolOption(
			hasFlag=True,
			customFlag="alts",
			comment="Enable alternates",
			falseComment="Disable alternates",
		)),
		# FIXME: replace with "resources"
		# 	comment="Use resources (images, audio, etc)"
		("skip_resources", BoolOption(
			hasFlag=True,
			comment="Skip resources (images, audio, css, etc)",
		)),
		("save_info_json", BoolOption(
			hasFlag=True,
			customFlag="info",
			comment="Save .info file alongside output file(s)",
		)),

		getEntryFilterConfigPair("lower"),
		getEntryFilterConfigPair("utf8_check"),
		getEntryFilterConfigPair("rtl"),
		getEntryFilterConfigPair("remove_html"),
		getEntryFilterConfigPair("remove_html_all"),
		getEntryFilterConfigPair("normalize_html"),
		getEntryFilterConfigPair("skip_duplicate_headword"),
		getEntryFilterConfigPair("trim_arabic_diacritics"),
		getEntryFilterConfigPair("unescape_word_links"),

		("color.enable.cmd.unix", BoolOption(
			hasFlag=False,
			comment="Enable colors in Linux/Unix command line",
		)),
		("color.enable.cmd.windows", BoolOption(
			hasFlag=False,
			comment="Enable colors in Windows command line",
		)),

		("color.cmd.critical", IntOption(
			hasFlag=False,
			comment="Color code for critical errors in command line",
		)),
		("color.cmd.error", IntOption(
			hasFlag=False,
			comment="Color code for errors in command line",
		)),
		("color.cmd.warning", IntOption(
			hasFlag=False,
			comment="Color code for warnings in command line",
		)),


		# interactive command line interface
		("cmdi.prompt.indent.str", StrOption(hasFlag=False)),
		("cmdi.prompt.indent.color", IntOption(hasFlag=False)),
		("cmdi.prompt.msg.color", IntOption(hasFlag=False)),
		("cmdi.msg.color", IntOption(hasFlag=False)),


		("ui_autoSetFormat", BoolOption(hasFlag=False)),

		("reverse_matchWord", BoolOption(hasFlag=False)),
		("reverse_showRel", StrOption(hasFlag=False)),
		("reverse_saveStep", IntOption(hasFlag=False)),
		("reverse_minRel", FloatOption(hasFlag=False)),
		("reverse_maxNum", IntOption(hasFlag=False)),
		("reverse_includeDefs", BoolOption(hasFlag=False)),
	])

	conflictingParams = [
		("sqlite", "direct"),
		("remove_html", "remove_html_all"),
	]

	def __init__(self, **kwargs) -> None:
		self.config = {}

	def progressInit(self, title: str) -> None:
		pass

	def progress(self, ratio: float, text: str = "") -> None:
		pass

	def progressEnd(self) -> None:
		self.progress(1.0)

	def loadConfig(
		self,
		user: bool = True,
		**options,
	) -> None:
		from pyglossary.json_utils import jsonToData
		data = jsonToData(fread(rootConfJsonFile))
		if user and isfile(confJsonFile):
			try:
				userData = jsonToData(fread(confJsonFile))
			except Exception:
				log.exception(
					f"error while loading user config file {confJsonFile!r}",
				)
			else:
				data.update(userData)

		for key in self.configDefDict:
			try:
				self.config[key] = data.pop(key)
			except KeyError:
				pass
		for key in data:
			log.warning(
				f"unknown config key {key!r}, you may edit {confJsonFile}"
				" file and remove this key",
			)

		for key, value in options.items():
			if key in self.configDefDict:
				self.config[key] = value

		log.setTimeEnable(self.config["log_time"])

		log.debug(f"loaded config: {self.config}")

	def saveConfig(self) -> None:
		from pyglossary.json_utils import dataToPrettyJson
		config = OrderedDict()
		for key, option in self.configDefDict.items():
			if key not in self.config:
				log.warning(f"saveConfig: missing key {key!r}")
				continue
			value = self.config[key]
			if not option.validate(value):
				log.error(f"saveConfig: invalid {key}={value!r}")
				continue
			config[key] = value
		jsonStr = dataToPrettyJson(config)
		with open(confJsonFile, mode="w", encoding="utf-8") as _file:
			_file.write(jsonStr)
		log.info(f"saved {confJsonFile!r}")
