# -*- coding: utf-8 -*-

from typing import (
	TYPE_CHECKING,
	Any,
	Callable,
	Dict,
	Iterator,
	Optional,
	Tuple,
	TypeAlias,
	Union,
)

if TYPE_CHECKING:
	from collections import OrderedDict

	import lxml

from .langs import Lang

RawEntryType: TypeAlias = Union[
	bytes,  # compressed
	"Tuple[list[str], bytes]",  # uncompressed, without defiFormat
	"Tuple[list[str], bytes, str]",  # uncompressed, with defiFormat
]


class EntryType(object):
	def __init__(self):
		self._word: "Union[str, list[str]]"

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
	def l_word(self) -> "list[str]":
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
		key: "Callable[[bytes], Any]",
	) -> "Callable[[Tuple], Any]":
		raise NotImplementedError

	def byteProgress(self) -> "Optional[Tuple[int, int]]":
		raise NotImplementedError

	def removeEmptyAndDuplicateAltWords(self) -> None:
		raise NotImplementedError


class GlossaryType(object):
	"""
	an abstract type class for Glossary class in plugins. it only
	contains methods and properties that might be used in plugins
	"""

	def __iter__(self) -> "Iterator[EntryType]":
		raise NotImplementedError

	def __len__(self) -> int:
		raise NotImplementedError

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

	def getExtraInfos(self, excludeKeys: "list[str]") -> "OrderedDict":
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

	@property
	def rawEntryCompress(self) -> bool:
		raise NotImplementedError


class GlossaryExtendedType(GlossaryType):
	def progressInit(
		self,
		*args,  # noqa: ANN
	) -> None:
		raise NotImplementedError

	def progress(self, pos: int, total: int, unit: str = "entries") -> None:
		raise NotImplementedError

	def progressEnd(self) -> None:
		raise NotImplementedError

	@property
	def progressbar(self) -> bool:
		raise NotImplementedError

	@progressbar.setter
	def progressbar(self, enabled: bool) -> None:
		raise NotImplementedError
