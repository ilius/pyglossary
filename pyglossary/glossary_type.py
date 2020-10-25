# -*- coding: utf-8 -*-

from .entry_base import BaseEntry
from .entry import Entry, DataEntry
from .langs import Lang


class GlossaryType(object):
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

	def getAuthor(self) -> str:
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

	def getConfig(self, name: str, default: "Optional[str]") -> "Optional[str]":
		raise NotImplementedError

	def addEntryObj(self, entry: "Entry") -> None:
		raise NotImplementedError

	def newEntry(self, word: str, defi: str, defiFormat: str = "") -> "Entry":
		raise NotImplementedError

	def newDataEntry(self, fname: str, data: bytes) -> DataEntry:
		raise NotImplementedError

	def writeTxt(
		self,
		entryFmt: str = "",  # contain {word} and {defi}
		filename: str = "",
		fileObj: "Optional[file]" = None,
		writeInfo: bool = True,
		wordEscapeFunc: "Optional[Callable]" = None,
		defiEscapeFunc: "Optional[Callable]" = None,
		ext: str = ".txt",
		head: str = "",
		tail: str = "",
		outInfoKeysAliasDict: "Optional[Dict[str, str]]" = None,
		encoding: str = "utf-8",
		newline: str = "\n",
		resources: bool = True,
	) -> "Generator[None, BaseEntry, None]":
		raise NotImplementedError

	def writeTabfile(
		self,
		filename: str = "",
		fileObj: "Optional[file]" = None,
		**kwargs,
	) -> "Generator[None, BaseEntry, None]":
		raise NotImplementedError
