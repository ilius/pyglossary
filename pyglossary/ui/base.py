# -*- coding: utf-8 -*-
##
## Copyright © 2012-2020 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
## This file is part of PyGlossary project, https://github.com/ilius/pyglossary
##
## This program is a free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 3, or (at your option)
## any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License along
## with this program. Or on Debian systems, from /usr/share/common-licenses/GPL
## If not, see <http://www.gnu.org/licenses/gpl.txt>.

from os.path import join, isfile
import logging
from collections import OrderedDict

from pyglossary.json_utils import jsonToData
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
		("log_time", BoolOption()),
		("cleanup", BoolOption()),

		("ui_autoSetFormat", BoolOption()),

		("lower", BoolOption()),
		("utf8Check", BoolOption()),
		("enable_alts", BoolOption()),

		("remove_html", StrOption()),
		("remove_html_all", BoolOption()),
		("normalize_html", BoolOption()),
		("save_info_json", BoolOption()),

		("reverse_matchWord", BoolOption()),
		("reverse_showRel", StrOption()),
		("reverse_saveStep", IntOption()),
		("reverse_minRel", FloatOption()),
		("reverse_maxNum", IntOption()),
		("reverse_includeDefs", BoolOption()),
	])
	def loadConfig(self, **options):
		data = jsonToData(fread(rootConfJsonFile))
		if isfile(confJsonFile):
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

		return True

	def progressEnd(self):
		self.progress(1.0)




