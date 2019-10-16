# -*- coding: utf-8 -*-
##
## Copyright © 2012 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
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

from pyglossary.core import (
	rootConfJsonFile,
	confJsonFile,
	rootDir,
	dataDir,
	appResDir,
)
from pyglossary.glossary import *
from pyglossary.json_utils import jsonToData

def fread(path):
	with open(path, encoding="utf-8") as fp:
		return fp.read()

logo = join(appResDir, "pyglossary.png")
aboutText = fread(join(dataDir, "about"))
licenseText = fread(join(dataDir, "license-dialog"))
authors = fread(join(dataDir, "AUTHORS")).split("\n")


class UIBase(object):
	prefKeys = (
		"noProgressBar",## command line
		"ui_autoSetFormat",
		"ui_autoSetOutputFileName",
		"lower",
		"utf8Check",
		"remove_html",
		"remove_html_all",
		"enable_alts",
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
				log.exception("error while loading user config file \"%s\"", confJsonFile)
			else:
				data.update(userData)

		for key in self.prefKeys:
			try:
				self.pref[key] = data.pop(key)
			except KeyError:
				pass
		for key, value in data.items():
			log.warning("unkown config key \"%s\"", key)

		for key, value in options.items():
			if key in self.prefKeys:
				self.pref[key] = value
		
		return True

	def progressEnd(self):
		self.progress(1.0)




