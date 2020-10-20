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

from pyglossary.core import (
	rootConfJsonFile,
	confJsonFile,
	rootDir,
	dataDir,
	appResDir,
)
from pyglossary.json_utils import jsonToData

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
	prefKeys = (
		"log_time",
		"cleanup",
		"ui_autoSetFormat",
		"lower",
		"utf8Check",
		"remove_html",
		"remove_html_all",
		"normalize_html",
		"enable_alts",
		"save_info_json",
		## Reverse Options:
		"reverse_matchWord",
		"reverse_showRel",
		"reverse_saveStep",
		"reverse_minRel",
		"reverse_maxNum",
		"reverse_includeDefs",
	)
	def pref_load(self, **options):
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

		for key in self.prefKeys:
			try:
				self.pref[key] = data.pop(key)
			except KeyError:
				pass
		for key, value in data.items():
			log.warning(
				f"unknown config key {key!r}, you may edit {confJsonFile}"
				" file and remove this key"
			)

		for key, value in options.items():
			if key in self.prefKeys:
				self.pref[key] = value

		log.setTimeEnable(self.pref["log_time"])

		return True

	def progressEnd(self):
		self.progress(1.0)




