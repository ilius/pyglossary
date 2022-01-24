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

from os.path import join, isfile
import logging
from collections import OrderedDict

from pyglossary.core import (
	rootConfJsonFile,
	confJsonFile,
	rootDir,
	dataDir,
	appResDir,
)
from pyglossary.option import (
	BoolOption,
	StrOption,
	IntOption,
	FloatOption,
)


def fread(path):
	with open(path, encoding="utf-8") as fp:
		return fp.read()


log = logging.getLogger("pyglossary")
logo = join(appResDir, "pyglossary.png")
aboutText = fread(join(dataDir, "about"))
licenseText = fread(join(dataDir, "license-dialog"))
authors = fread(join(dataDir, "AUTHORS")).split("\n")

summary = "A tool for converting dictionary files aka glossaries with" \
	" various formats for different dictionary applications"


class UIBase(object):
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

		("lower", BoolOption(
			hasFlag=True,
			comment="Lowercase words before writing",
			falseComment="Do not lowercase words before writing",
		)),
		("utf8_check", BoolOption(
			hasFlag=True,
			comment="Ensure entries contain valid UTF-8 strings",
			falseComment="Do not ensure entries contain valid UTF-8 strings",
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
			comment="Skip resources (images, audio, etc)",
		)),

		("rtl", BoolOption(
			hasFlag=True,
			comment=(
				"Mark all definitions as Right-To-Left\n"
				"(definitions must be HTML)"
			),
		)),
		("remove_html", StrOption(
			hasFlag=True,
			comment=(
				"Remove given html tags (comma-separated)\n"
				"from definitions"
			),
		)),
		("remove_html_all", BoolOption(
			hasFlag=True,
			comment="Remove all html tags from definitions",
		)),
		("normalize_html", BoolOption(
			hasFlag=True,
			comment="Lowercase and normalize html tags in definitions",
		)),
		("save_info_json", BoolOption(
			hasFlag=True,
			customFlag="info",
			comment="Save glossary info as json file with .info extension",
		)),

		("color.enable.cmd.unix", BoolOption(
			hasFlag=False,
			comment="Enable colors in Linux/Unix command line"
		)),
		("color.enable.cmd.windows", BoolOption(
			hasFlag=False,
			comment="Enable colors in Windows command line"
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

	def __init__(self, **kwargs):
		self.config = {}

	def progressInit(self, title):
		pass

	def progress(self, rat, text=""):
		pass

	def progressEnd(self):
		self.progress(1.0)

	def loadConfig(
		self,
		user: bool = True,
		**options
	):
		from pyglossary.json_utils import jsonToData
		data = jsonToData(fread(rootConfJsonFile))
		if user and isfile(confJsonFile):
			try:
				userData = jsonToData(fread(confJsonFile))
			except Exception:
				log.exception(
					f"error while loading user config file {confJsonFile!r}"
				)
			else:
				data.update(userData)

		for key in self.configDefDict:
			try:
				self.config[key] = data.pop(key)
			except KeyError:
				pass
		for key, value in data.items():
			log.warning(
				f"unknown config key {key!r}, you may edit {confJsonFile}"
				" file and remove this key"
			)

		for key, value in options.items():
			if key in self.configDefDict:
				self.config[key] = value

		log.setTimeEnable(self.config["log_time"])

		log.debug(f"loaded config: {self.config}")
		return True

	def saveConfig(self):
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
		with open(confJsonFile, mode="wt", encoding="utf-8") as _file:
			_file.write(jsonStr)
		log.info(f"saved {confJsonFile!r}")
