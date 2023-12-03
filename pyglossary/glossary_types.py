
import typing
from collections.abc import Iterator  # noqa: TCH003

# -*- coding: utf-8 -*-
from typing import (
	TYPE_CHECKING,
	Any,
	Callable,
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
	def __init__(self) -> None:
		...

	def isData(self) -> bool:
		...

	def getFileName(self) -> str:
		...

	@property
	def data(self) -> bytes:
		...

	def size(self) -> int:
		...

	def save(self, directory: str) -> str:
		...

	@property
	def s_word(self) -> str:
		...

	@property
	def l_word(self) -> "list[str]":
		...

	@property
	def defi(self) -> str:
		...

	@property
	def b_word(self) -> bytes:
		...

	@property
	def b_defi(self) -> bytes:
		...

	@property
	def defiFormat(self) -> str:
		# TODO: type: Literal["m", "h", "x", "b"]
		...

	@defiFormat.setter
	def defiFormat(self, defiFormat: str) -> None:
		# TODO: type: Literal["m", "h", "x", "b"]
		...

	def detectDefiFormat(self) -> None:
		...

	def addAlt(self, alt: str) -> None:
		...

	def editFuncWord(self, func: "Callable[[str], str]") -> None:
		...

	def editFuncDefi(self, func: "Callable[[str], str]") -> None:
		...

	def strip(self) -> None:
		...

	def replaceInWord(self, source: str, target: str) -> None:
		...

	def replaceInDefi(self, source: str, target: str) -> None:
		...

	def replace(self, source: str, target: str) -> None:
		...

	def byteProgress(self) -> "tuple[int, int] | None":
		...

	def removeEmptyAndDuplicateAltWords(self) -> None:
		...

	def stripFullHtml(self) -> "str | None":
		...


class EntryListType(typing.Protocol):
	def __init__(
		self,
		entryToRaw: "Callable[[EntryType], RawEntryType]",
		entryFromRaw: "Callable[[RawEntryType], EntryType]",
	) -> None:
		...

	@property
	def rawEntryCompress(self) -> bool:
		...

	@rawEntryCompress.setter
	def rawEntryCompress(self, enable: bool) -> None:
		...

	def append(self, entry: "EntryType") -> None:
		...

	def clear(self) -> None:
		...

	def __len__(self) -> int:
		...

	def __iter__(self) -> "Iterator[EntryType]":
		...

	def setSortKey(
		self,
		namedSortKey: "NamedSortKey",
		sortEncoding: "str | None",
		writeOptions: "dict[str, Any]",
	) -> None:
		...

	def sort(self) -> None:
		...

	def close(self) -> None:
		...


class GlossaryType(typing.Protocol):

	"""
	an abstract type class for Glossary class in plugins. it only
	contains methods and properties that might be used in plugins.
	"""

	def __iter__(self) -> "Iterator[EntryType]":
		...

	def __len__(self) -> int:
		...

	def setDefaultDefiFormat(self, defiFormat: str) -> None:
		...

	def getDefaultDefiFormat(self) -> str:
		...

	def collectDefiFormat(
		self,
		maxCount: int,
	) -> "dict[str, float] | None":
		...

	def iterInfo(self) -> "Iterator[tuple[str, str]]":
		...

	def getInfo(self, key: str) -> str:
		...

	def setInfo(self, key: str, value: str) -> None:
		...

	def getExtraInfos(self, excludeKeys: "list[str]") -> "OrderedDict":
		...

	@property
	def author(self) -> str:
		...

	@property
	def alts(self) -> bool:
		...

	@property
	def filename(self) -> str:
		...

	@property
	def tmpDataDir(self) -> str:
		...

	@property
	def sourceLang(self) -> "Lang | None":
		...

	@property
	def targetLang(self) -> "Lang | None":
		...

	@property
	def sourceLangName(self) -> str:
		...

	@sourceLangName.setter
	def sourceLangName(self, langName: str) -> None:
		...

	@property
	def targetLangName(self) -> str:
		...

	@targetLangName.setter
	def targetLangName(self, langName: str) -> None:
		...

	def titleTag(self, sample: str) -> str:
		...

	def wordTitleStr(
		self,
		word: str,
		sample: str = "",
		_class: str = "",
	) -> str:
		...

	def getConfig(self, name: str, default: "str | None") -> "str | None":
		...

	def addEntry(self, entry: EntryType) -> None:
		...

	def newEntry(
		self,
		word: "MultiStr",
		defi: str,
		defiFormat: str = "",
		byteProgress: "tuple[int, int] | None" = None,
	) -> EntryType:
		...

	def newDataEntry(self, fname: str, data: bytes) -> EntryType:
		...

	@property
	def rawEntryCompress(self) -> bool:
		...

	def stripFullHtml(
		self,
		errorHandler: "Callable[[EntryType, str], None] | None" = None,
	) -> None:
		...

	def preventDuplicateWords(self) -> None:
		...

	def removeHtmlTagsAll(self) -> None:
		...


class GlossaryExtendedType(GlossaryType, typing.Protocol):
	def progressInit(
		self,
		*args,
	) -> None:
		...

	def progress(self, pos: int, total: int, unit: str = "entries") -> None:
		...

	def progressEnd(self) -> None:
		...

	@property
	def progressbar(self) -> bool:
		...

	@progressbar.setter
	def progressbar(self, enabled: bool) -> None:
		...
