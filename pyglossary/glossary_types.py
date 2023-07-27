
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


class EntryType(typing.Protocol):
	def __init__(self: "typing.Self") -> None:
		...

	def isData(self: "typing.Self") -> bool:
		...

	def getFileName(self: "typing.Self") -> str:
		...

	@property
	def data(self: "typing.Self") -> bytes:
		...

	def size(self: "typing.Self") -> int:
		...

	def save(self: "typing.Self", directory: str) -> str:
		...

	@property
	def s_word(self: "typing.Self") -> str:
		...

	@property
	def l_word(self: "typing.Self") -> "list[str]":
		...

	@property
	def defi(self: "typing.Self") -> str:
		...

	@property
	def b_word(self: "typing.Self") -> bytes:
		...

	@property
	def b_defi(self: "typing.Self") -> bytes:
		...

	@property
	def defiFormat(self: "typing.Self") -> str:
		# TODO: type: Literal["m", "h", "x", "b"]
		...

	@defiFormat.setter
	def defiFormat(self: "typing.Self", defiFormat: str) -> None:
		# TODO: type: Literal["m", "h", "x", "b"]
		...

	def detectDefiFormat(self: "typing.Self") -> None:
		...

	def addAlt(self: "typing.Self", alt: str) -> None:
		...

	def editFuncWord(self: "typing.Self", func: "Callable[[str], str]") -> None:
		...

	def editFuncDefi(self: "typing.Self", func: "Callable[[str], str]") -> None:
		...

	def strip(self: "typing.Self") -> None:
		...

	def replaceInWord(self: "typing.Self", source: str, target: str) -> None:
		...

	def replaceInDefi(self: "typing.Self", source: str, target: str) -> None:
		...

	def replace(self: "typing.Self", source: str, target: str) -> None:
		...

	def byteProgress(self: "typing.Self") -> "tuple[int, int] | None":
		...

	def removeEmptyAndDuplicateAltWords(self: "typing.Self") -> None:
		...

	def stripFullHtml(self: "typing.Self") -> "str | None":
		...


class EntryListType(typing.Protocol):
	def __init__(
		self: "typing.Self",
		entryToRaw: "Callable[[EntryType], RawEntryType]",
		entryFromRaw: "Callable[[RawEntryType], EntryType]",
	) -> None:
		...

	@property
	def rawEntryCompress(self: "typing.Self") -> bool:
		...

	@rawEntryCompress.setter
	def rawEntryCompress(self: "typing.Self", enable: bool) -> None:
		...

	def append(self: "typing.Self", entry: "EntryType") -> None:
		...	

	def clear(self: "typing.Self") -> None:
		...

	def __len__(self: "typing.Self") -> int:
		...

	def __iter__(self: "typing.Self") -> "Iterator[EntryType]":
		...

	def setSortKey(
		self: "typing.Self",
		namedSortKey: "NamedSortKey",
		sortEncoding: "str | None",
		writeOptions: "dict[str, Any]",
	) -> None:
		...

	def sort(self: "typing.Self") -> None:
		...

	def close(self: "typing.Self") -> None:
		...


class GlossaryType(typing.Protocol):
	"""
	an abstract type class for Glossary class in plugins. it only
	contains methods and properties that might be used in plugins
	"""

	def __iter__(self: "typing.Self") -> "Iterator[EntryType]":
		...

	def __len__(self: "typing.Self") -> int:
		...

	def setDefaultDefiFormat(self: "typing.Self", defiFormat: str) -> None:
		...

	def getDefaultDefiFormat(self: "typing.Self") -> str:
		...

	def collectDefiFormat(
		self: "typing.Self",
		maxCount: int,
	) -> "dict[str, float] | None":
		...

	def iterInfo(self: "typing.Self") -> "Iterator[tuple[str, str]]":
		...

	def getInfo(self: "typing.Self", key: str) -> str:
		...

	def setInfo(self: "typing.Self", key: str, value: str) -> None:
		...

	def getExtraInfos(self: "typing.Self", excludeKeys: "list[str]") -> "OrderedDict":
		...

	@property
	def author(self: "typing.Self") -> str:
		...

	@property
	def alts(self: "typing.Self") -> bool:
		...

	@property
	def filename(self: "typing.Self") -> str:
		...

	@property
	def tmpDataDir(self: "typing.Self") -> str:
		...

	@property
	def sourceLang(self: "typing.Self") -> "Lang | None":
		...

	@property
	def targetLang(self: "typing.Self") -> "Lang | None":
		...

	@property
	def sourceLangName(self: "typing.Self") -> str:
		...

	@sourceLangName.setter
	def sourceLangName(self: "typing.Self", langName: str) -> None:
		...

	@property
	def targetLangName(self: "typing.Self") -> str:
		...

	@targetLangName.setter
	def targetLangName(self: "typing.Self", langName: str) -> None:
		...

	def titleTag(self: "typing.Self", sample: str) -> str:
		...

	def wordTitleStr(
		self: "typing.Self",
		word: str,
		sample: str = "",
		_class: str = "",
	) -> str:
		...

	def getConfig(self: "typing.Self", name: str, default: "str | None") -> "str | None":
		...

	def addEntry(self: "typing.Self", entry: EntryType) -> None:
		...

	def newEntry(
		self: "typing.Self",
		word: "MultiStr",
		defi: str,
		defiFormat: str = "",
		byteProgress: "tuple[int, int] | None" = None,
	) -> EntryType:
		...

	def newDataEntry(self: "typing.Self", fname: str, data: bytes) -> EntryType:
		...

	@property
	def rawEntryCompress(self: "typing.Self") -> bool:
		...

	def stripFullHtml(
		self: "typing.Self",
		errorHandler: "Callable[[EntryType, str], None] | None" = None,
	) -> None:
		...


class GlossaryExtendedType(GlossaryType, typing.Protocol):
	def progressInit(
		self: "typing.Self",
		*args,  # noqa: ANN
	) -> None:
		...

	def progress(self: "typing.Self", pos: int, total: int, unit: str = "entries") -> None:
		...

	def progressEnd(self: "typing.Self") -> None:
		...

	@property
	def progressbar(self: "typing.Self") -> bool:
		...

	@progressbar.setter
	def progressbar(self: "typing.Self", enabled: bool) -> None:
		...
