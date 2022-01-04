# -*- coding: utf-8 -*-

from .entry_base import BaseEntry
from .entry import Entry, DataEntry
from .langs import Lang


class GlossaryType(object):
	"""
	an abstract type class for Glossary class in plugins. it only
	contains methods and properties that might be used in plugins
	"""

	def setDefaultDefiFormat(self, defiFormat: str) -> None:
		raise NotImplementedError

	def getDefaultDefiFormat(self) -> str:
		raise NotImplementedError

	def collectDefiFormat(
		self,
		maxCount: int,
	) -> "Optional[Dict[str, float]]":
		raise NotImplementedError

	def iterInfo(self) -> "Iterator[Tuple[str, str]]":
		raise NotImplementedError

	def getInfo(self, key: str) -> str:
		raise NotImplementedError

	def setInfo(self, key: str, value: str) -> None:
		raise NotImplementedError

	def getExtraInfos(self, excludeKeys: "List[str]") -> "OrderedDict":
		raise NotImplementedError

	@property
	def author(self) -> str:
		raise NotImplementedError

	@property
	def alts(self) -> bool:
		raise NotImplementedError

	@property
	def filename(self):
		raise NotImplementedError

	@property
	def sourceLang(self) -> "Optional[Lang]":
		raise NotImplementedError

	@property
	def targetLang(self) -> "Optional[Lang]":
		raise NotImplementedError

	@property
	def sourceLangName(self) -> str:
		raise NotImplementedError

	@sourceLangName.setter
	def sourceLangName(self, langName: str) -> None:
		raise NotImplementedError

	@property
	def targetLangName(self) -> str:
		raise NotImplementedError

	@targetLangName.setter
	def targetLangName(self, langName: str) -> None:
		raise NotImplementedError

	def titleElement(
		self,
		hf: "lxml.etree.htmlfile",
		sample: str = "",
	) -> "lxml.etree._FileWriterElement":
		raise NotImplementedError

	def wordTitleStr(
		self,
		word: str,
		sample: str = "",
		_class: str = "",
	) -> str:
		raise NotImplementedError

	def getConfig(self, name: str, default: "Optional[str]") -> "Optional[str]":
		raise NotImplementedError

	def addEntryObj(self, entry: "Entry") -> None:
		raise NotImplementedError

	def newEntry(self, word: str, defi: str, defiFormat: str = "") -> "Entry":
		raise NotImplementedError

	def newDataEntry(self, fname: str, data: bytes) -> DataEntry:
		raise NotImplementedError
