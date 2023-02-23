# -*- coding: utf-8 -*-
#
# Copyright © 2008-2022 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
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
from collections import OrderedDict as odict
from typing import TYPE_CHECKING, Iterator, List, Optional, Tuple

if TYPE_CHECKING:
	import lxml

from .info import (
	c_author,
	c_name,
	c_publisher,
	c_sourceLang,
	c_targetLang,
	infoKeysAliasDict,
)
from .langs import Lang, langDict
from .text_utils import (
	fixUtf8,
)

log = logging.getLogger("pyglossary")


class GlossaryInfo(object):
	def __init__(self) -> None:
		self._info = odict()

	def infoKeys(self) -> "List[str]":
		return list(self._info.keys())

	# def formatInfoKeys(self, format: str):# FIXME

	def iterInfo(self) -> "Iterator[Tuple[str, str]]":
		return iter(self._info.items())

	def getInfo(self, key: str) -> str:
		if not isinstance(key, str):
			raise TypeError(f"invalid {key=}, must be str")
		return self._info.get(
			infoKeysAliasDict.get(key.lower(), key),
			"",
		)

	def setInfo(self, key: str, value: "Optional[str]") -> None:
		if value is None:
			try:
				del self._info[key]
			except KeyError:
				pass
			return

		if not isinstance(key, str):
			raise TypeError(f"invalid {key=}, must be str")

		key = fixUtf8(key)
		value = fixUtf8(str(value))

		key = infoKeysAliasDict.get(key.lower(), key)
		self._info[key] = value

	def getExtraInfos(self, excludeKeys: "List[str]") -> "odict":
		"""
		excludeKeys: a list of (basic) info keys to be excluded
		returns an OrderedDict including the rest of info keys,
				with associated values
		"""
		excludeKeySet = set()
		for key in excludeKeys:
			excludeKeySet.add(key)
			key2 = infoKeysAliasDict.get(key.lower())
			if key2:
				excludeKeySet.add(key2)

		extra = odict()
		for key, value in self._info.items():
			if key in excludeKeySet:
				continue
			extra[key] = value

		return extra

	@property
	def author(self) -> str:
		for key in (c_author, c_publisher):
			value = self._info.get(key, "")
			if value:
				return value
		return ""

	def _getLangByStr(self, st: str) -> "Optional[Lang]":
		lang = langDict[st]
		if lang:
			return lang
		log.error(f"unknown language {st!r}")
		return None

	def _getLangByInfoKey(self, key: str) -> "Optional[Lang]":
		st = self._info.get(key, "")
		if not st:
			return None
		return self._getLangByStr(st)

	@property
	def sourceLang(self) -> "Optional[Lang]":
		return self._getLangByInfoKey(c_sourceLang)

	@property
	def targetLang(self) -> "Optional[Lang]":
		return self._getLangByInfoKey(c_targetLang)

	@sourceLang.setter
	def sourceLang(self, lang: Lang) -> None:
		if not isinstance(lang, Lang):
			raise TypeError(f"invalid {lang=}, must be a Lang object")
		self._info[c_sourceLang] = lang.name

	@targetLang.setter
	def targetLang(self, lang: Lang) -> None:
		if not isinstance(lang, Lang):
			raise TypeError(f"invalid {lang=}, must be a Lang object")
		self._info[c_targetLang] = lang.name

	@property
	def sourceLangName(self) -> str:
		lang = self.sourceLang
		if lang is None:
			return ""
		return lang.name

	@sourceLangName.setter
	def sourceLangName(self, langName: str) -> None:
		if not langName:
			self._info[c_sourceLang] = ""
			return
		lang = self._getLangByStr(langName)
		if lang is None:
			return
		self._info[c_sourceLang] = lang.name

	@property
	def targetLangName(self) -> str:
		lang = self.targetLang
		if lang is None:
			return ""
		return lang.name

	@targetLangName.setter
	def targetLangName(self, langName: str) -> None:
		if not langName:
			self._info[c_targetLang] = ""
			return
		lang = self._getLangByStr(langName)
		if lang is None:
			return
		self._info[c_targetLang] = lang.name

	def _getTitleTag(self, sample: str) -> str:
		from .langs.writing_system import getWritingSystemFromText
		ws = getWritingSystemFromText(sample)
		if ws and ws.name != "Latin":
			return ws.titleTag
		sourceLang = self.sourceLang
		if sourceLang:
			return sourceLang.titleTag
		return "b"

	def detectLangsFromName(self) -> None:
		"""
		extract sourceLang and targetLang from glossary name/title
		"""
		import re

		name = self._info.get(c_name)
		if not name:
			return
		if self._info.get(c_sourceLang):
			return

		langNames = []

		def checkPart(part: str) -> None:
			for match in re.findall(r"\w\w\w*", part):
				# print(f"{match = }")
				lang = langDict[match]
				if lang is None:
					continue
				langNames.append(lang.name)

		for part in re.split("-| to ", name):
			# print(f"{part = }")
			checkPart(part)
			if len(langNames) >= 2:
				break

		if len(langNames) < 2:
			log.info(
				f"Failed to detect sourceLang and targetLang"
				f" from glossary name {name!r}",
			)
			return

		if len(langNames) > 2:
			log.info(f"detectLangsFromName: {langNames = }")

		log.info(
			f"Detected sourceLang={langNames[0]!r}, "
			f"targetLang={langNames[1]!r} "
			f"from glossary name {name!r}",
		)
		self.sourceLangName = langNames[0]
		self.targetLangName = langNames[1]

	def titleElement(
		self,
		hf: "lxml.etree.htmlfile",
		sample: str = "",
	) -> "lxml.etree._FileWriterElement":
		return hf.element(self._getTitleTag(sample))
