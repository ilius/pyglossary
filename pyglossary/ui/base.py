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

from __future__ import annotations

import logging
from os.path import isfile, join

from pyglossary.core import (
	appResDir,
	confJsonFile,
	dataDir,
	rootConfJsonFile,
)
from pyglossary.ui.config import configDefDict

__all__ = ["UIBase", "aboutText", "authors", "fread", "licenseText", "logo"]


def fread(path: str) -> str:
	with open(path, encoding="utf-8") as fp:
		return fp.read()


log = logging.getLogger("pyglossary")
logo = join(appResDir, "pyglossary.png")
aboutText = fread(join(dataDir, "about"))
licenseText = fread(join(dataDir, "_license-dialog"))
authors = fread(join(dataDir, "AUTHORS")).split("\n")

summary = (
	"A tool for converting dictionary files aka glossaries with"
	" various formats for different dictionary applications"
)


class UIBase:
	conflictingParams = [
		("sqlite", "direct"),
		("remove_html", "remove_html_all"),
	]

	def __init__(self, **_kwargs) -> None:
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
		assert isinstance(data, dict)
		if user and isfile(confJsonFile):
			try:
				userData = jsonToData(fread(confJsonFile))
			except Exception:
				log.exception(
					f"error while loading user config file {confJsonFile!r}",
				)
			else:
				data.update(userData)

		for key in configDefDict:
			try:
				self.config[key] = data.pop(key)
			except KeyError:  # noqa: PERF203
				pass
		for key in data:
			log.warning(
				f"unknown config key {key!r}, you may edit {confJsonFile}"
				" file and remove this key",
			)

		for key, value in options.items():
			if key in configDefDict:
				self.config[key] = value

		log.setTimeEnable(self.config["log_time"])

		log.debug(f"loaded config: {self.config}")

	def saveConfig(self) -> None:
		from pyglossary.json_utils import dataToPrettyJson

		config = {}
		for key, option in configDefDict.items():
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
