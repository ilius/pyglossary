
import typing

# -*- coding: utf-8 -*-
from typing import (
	TYPE_CHECKING,
	Any,
	Callable,
	Iterator,
)

if TYPE_CHECKING:
	from collections import OrderedDict
	from typing import TypeAlias


from .interfaces import Interface
from .langs import Lang
from .sort_keys import NamedSortKey

MultiStr: "TypeAlias" = "str | list[str]"

# 3 different types in order:
# - compressed
# - uncompressed, without defiFormat
# - uncompressed, with defiFormat
RawEntryType: "TypeAlias" = (
	"bytes |"
	"tuple[list[str], bytes] |"
	"tuple[list[str], bytes, str]"
)


class EntryType(metaclass=Interface):
	def __init__(self: "typing.Self") -> None:
		self._word: "str | list[str]"

	def isData(self: "typing.Self") -> bool:
		raise NotImplementedError

	def getFileName(self: "typing.Self") -> str:
		raise NotImplementedError

	@property
	def data(self: "typing.Self") -> bytes:
		raise NotImplementedError

	def size(self: "typing.Self") -> int:
		raise NotImplementedError

	def save(self: "typing.Self", directory: str) -> str:
		raise NotImplementedError

	@property
	def s_word(self: "typing.Self") -> str:
		raise NotImplementedError

	@property
	def l_word(self: "typing.Self") -> "list[str]":
		raise NotImplementedError

	@property
	def defi(self: "typing.Self") -> str:
		raise NotImplementedError

	@property
	def b_word(self: "typing.Self") -> bytes:
		raise NotImplementedError

	@property
	def b_defi(self: "typing.Self") -> bytes:
		raise NotImplementedError

	@property
	def defiFormat(self: "typing.Self") -> str:
		# TODO: type: Literal["m", "h", "x", "b"]
		raise NotImplementedError

	@defiFormat.setter
	def defiFormat(self: "typing.Self", defiFormat: str) -> None:
		# TODO: type: Literal["m", "h", "x", "b"]
		raise NotImplementedError

	def detectDefiFormat(self: "typing.Self") -> None:
		raise NotImplementedError

	def addAlt(self: "typing.Self", alt: str) -> None:
		raise NotImplementedError

	def editFuncWord(self: "typing.Self", func: "Callable[[str], str]") -> None:
		raise NotImplementedError

	def editFuncDefi(self: "typing.Self", func: "Callable[[str], str]") -> None:
		raise NotImplementedError

	def strip(self: "typing.Self") -> None:
		raise NotImplementedError

	def replaceInWord(self: "typing.Self", source: str, target: str) -> None:
		raise NotImplementedError

	def replaceInDefi(self: "typing.Self", source: str, target: str) -> None:
		raise NotImplementedError

	def replace(self: "typing.Self", source: str, target: str) -> None:
		raise NotImplementedError

	def getRaw(self: "typing.Self", glos: "GlossaryType") -> RawEntryType:
		raise NotImplementedError

	@staticmethod
	def getRawEntrySortKey(
		glos: "GlossaryType",
		key: "Callable[[bytes], Any]",
	) -> "Callable[[RawEntryType], Any]":
		raise NotImplementedError

	def byteProgress(self: "typing.Self") -> "tuple[int, int] | None":
		raise NotImplementedError

	def removeEmptyAndDuplicateAltWords(self: "typing.Self") -> None:
		raise NotImplementedError

	def stripFullHtml(self: "typing.Self") -> "str | None":
		raise NotImplementedError


class EntryListType(metaclass=Interface):
	def __init__(
		self: "typing.Self",
		entryToRaw: "Callable[[EntryType], RawEntryType]",
		entryFromRaw: "Callable[[RawEntryType], EntryType]",
	) -> None:
		raise NotImplementedError

	@property
	def rawEntryCompress(self: "typing.Self") -> bool:
		raise NotImplementedError

	@rawEntryCompress.setter
	def rawEntryCompress(self: "typing.Self", enable: bool) -> None:
		raise NotImplementedError

	def append(self: "typing.Self", entry: "EntryType") -> None:
		raise NotImplementedError	

	def clear(self: "typing.Self") -> None:
		raise NotImplementedError

	def __len__(self: "typing.Self") -> int:
		raise NotImplementedError

	def __iter__(self: "typing.Self") -> "Iterator[EntryType]":
		raise NotImplementedError

	def setSortKey(
		self: "typing.Self",
		namedSortKey: "NamedSortKey",
		sortEncoding: "str | None",
		writeOptions: "dict[str, Any]",
	) -> None:
		raise NotImplementedError

	def sort(self: "typing.Self") -> None:
		raise NotImplementedError

	def close(self: "typing.Self") -> None:
		raise NotImplementedError


class GlossaryType(metaclass=Interface):
	"""
	an abstract type class for Glossary class in plugins. it only
	contains methods and properties that might be used in plugins
	"""

	def __iter__(self: "typing.Self") -> "Iterator[EntryType]":
		raise NotImplementedError

	def __len__(self: "typing.Self") -> int:
		raise NotImplementedError

	def setDefaultDefiFormat(self: "typing.Self", defiFormat: str) -> None:
		raise NotImplementedError

	def getDefaultDefiFormat(self: "typing.Self") -> str:
		raise NotImplementedError

	def collectDefiFormat(
		self: "typing.Self",
		maxCount: int,
	) -> "dict[str, float] | None":
		raise NotImplementedError

	def iterInfo(self: "typing.Self") -> "Iterator[tuple[str, str]]":
		raise NotImplementedError

	def getInfo(self: "typing.Self", key: str) -> str:
		raise NotImplementedError

	def setInfo(self: "typing.Self", key: str, value: str) -> None:
		raise NotImplementedError

	def getExtraInfos(self: "typing.Self", excludeKeys: "list[str]") -> "OrderedDict":
		raise NotImplementedError

	@property
	def author(self: "typing.Self") -> str:
		raise NotImplementedError

	@property
	def alts(self: "typing.Self") -> bool:
		raise NotImplementedError

	@property
	def filename(self: "typing.Self") -> str:
		raise NotImplementedError

	@property
	def tmpDataDir(self: "typing.Self") -> str:
		raise NotImplementedError

	@property
	def sourceLang(self: "typing.Self") -> "Lang | None":
		raise NotImplementedError

	@property
	def targetLang(self: "typing.Self") -> "Lang | None":
		raise NotImplementedError

	@property
	def sourceLangName(self: "typing.Self") -> str:
		raise NotImplementedError

	@sourceLangName.setter
	def sourceLangName(self: "typing.Self", langName: str) -> None:
		raise NotImplementedError

	@property
	def targetLangName(self: "typing.Self") -> str:
		raise NotImplementedError

	@targetLangName.setter
	def targetLangName(self: "typing.Self", langName: str) -> None:
		raise NotImplementedError

	def titleTag(self: "typing.Self", sample: str) -> str:
		raise NotImplementedError

	def wordTitleStr(
		self: "typing.Self",
		word: str,
		sample: str = "",
		_class: str = "",
	) -> str:
		raise NotImplementedError

	def getConfig(self: "typing.Self", name: str, default: "str | None") -> "str | None":
		raise NotImplementedError

	def addEntry(self: "typing.Self", entry: EntryType) -> None:
		raise NotImplementedError

	def newEntry(
		self: "typing.Self",
		word: "MultiStr",
		defi: str,
		defiFormat: str = "",
		byteProgress: "tuple[int, int] | None" = None,
	) -> EntryType:
		raise NotImplementedError

	def newDataEntry(self: "typing.Self", fname: str, data: bytes) -> EntryType:
		raise NotImplementedError

	@property
	def rawEntryCompress(self: "typing.Self") -> bool:
		raise NotImplementedError

	def stripFullHtml(
		self: "typing.Self",
		errorHandler: "Callable[[EntryType, str], None] | None" = None,
	) -> None:
		raise NotImplementedError


class GlossaryExtendedType(GlossaryType, metaclass=Interface):
	def progressInit(
		self: "typing.Self",
		*args,  # noqa: ANN
	) -> None:
		raise NotImplementedError

	def progress(self: "typing.Self", pos: int, total: int, unit: str = "entries") -> None:
		raise NotImplementedError

	def progressEnd(self: "typing.Self") -> None:
		raise NotImplementedError

	@property
	def progressbar(self: "typing.Self") -> bool:
		raise NotImplementedError

	@progressbar.setter
	def progressbar(self: "typing.Self", enabled: bool) -> None:
		raise NotImplementedError
