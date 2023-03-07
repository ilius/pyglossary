# -*- coding: utf-8 -*-

from typing import (
	TYPE_CHECKING,
	Any,
	Callable,
	Dict,
	Iterator,
	List,
	Optional,
	Tuple,
)

if TYPE_CHECKING:
	from collections import OrderedDict

from .langs import Lang

RawEntryType = """Union[
	bytes,  # compressed
	Tuple[List[str], bytes],  # uncompressed, without defiFormat
	Tuple[List[str], bytes, str],  # uncompressed, with defiFormat
]"""


class EntryType(object):
	def isData(self) -> bool:
		raise NotImplementedError

	def getFileName(self) -> str:
		raise NotImplementedError

	@property
	def data(self) -> bytes:
		raise NotImplementedError

	def size(self) -> int:
		raise NotImplementedError

	def save(self, directory: str) -> str:
		raise NotImplementedError

	@property
	def s_word(self) -> str:
		raise NotImplementedError

	@property
	def l_word(self) -> "List[str]":
		raise NotImplementedError

	@property
	def defi(self) -> str:
		raise NotImplementedError

	@property
	def b_word(self) -> bytes:
		raise NotImplementedError

	@property
	def b_defi(self) -> bytes:
		raise NotImplementedError

	@property
	def defiFormat(self) -> str:
		# TODO: type: Literal["m", "h", "x", "b"]
		raise NotImplementedError

	@defiFormat.setter
	def defiFormat(self, defiFormat: str) -> None:
		# TODO: type: Literal["m", "h", "x", "b"]
		raise NotImplementedError

	def detectDefiFormat(self) -> None:
		raise NotImplementedError

	def addAlt(self, alt: str) -> None:
		raise NotImplementedError

	def editFuncWord(self, func: "Callable[[str], str]") -> None:
		raise NotImplementedError

	def editFuncDefi(self, func: "Callable[[str], str]") -> None:
		raise NotImplementedError

	def strip(self) -> None:
		raise NotImplementedError

	def replaceInWord(self, source: str, target: str) -> None:
		raise NotImplementedError

	def replaceInDefi(self, source: str, target: str) -> None:
		raise NotImplementedError

	def replace(self, source: str, target: str) -> None:
		raise NotImplementedError

	def getRaw(self, glos: "GlossaryType") -> RawEntryType:
		raise NotImplementedError

	@staticmethod
	def getRawEntrySortKey(
		glos: "GlossaryType",
		key: "Callable[[str], Any]",
	) -> "Callable[[Tuple], str]":
		raise NotImplementedError


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
	def filename(self) -> str:
		raise NotImplementedError

	@property
	def tmpDataDir(self) -> str:
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
		hf: "lxml.etree.htmlfile",  # noqa: F821
		sample: str = "",
	) -> "lxml.etree._FileWriterElement":  # noqa: F821
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

	def addEntry(self, entry: EntryType) -> None:
		raise NotImplementedError

	def newEntry(self, word: str, defi: str, defiFormat: str = "") -> EntryType:
		raise NotImplementedError

	def newDataEntry(self, fname: str, data: bytes) -> EntryType:
		raise NotImplementedError
