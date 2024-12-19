from __future__ import annotations

import typing
from collections.abc import (
	Callable,
	Iterator,
	Sequence,
)

# -*- coding: utf-8 -*-
from typing import (
	TYPE_CHECKING,
	Any,
)

if TYPE_CHECKING:
	from typing import TypeAlias

	from .langs import Lang
	from .sort_keys import NamedSortKey

__all__ = [
	"Callable",
	"EntryListType",
	"EntryType",
	"GlossaryExtendedType",
	"GlossaryType",
	"RawEntryType",
]

MultiStr: TypeAlias = "str | list[str]"

# str(rawEntry[0]): defiFormat or ""
# rawEntry[1]: b_defi
# rawEntry[2:]: b_word_list
RawEntryType: TypeAlias = Sequence[bytes]


class EntryType(typing.Protocol):  # noqa: PLR0904
	# def __init__(self) -> None: ...

	def isData(self) -> bool: ...

	def getFileName(self) -> str: ...

	@property
	def data(self) -> bytes: ...

	def size(self) -> int: ...

	def save(self, directory: str) -> str: ...

	@property
	def s_word(self) -> str: ...

	@property
	def l_word(self) -> list[str]: ...

	@property
	def lb_word(self) -> list[bytes]: ...

	@property
	def defi(self) -> str: ...

	@property
	def b_word(self) -> bytes: ...

	@property
	def b_defi(self) -> bytes: ...

	@property
	def defiFormat(self) -> str:
		# TODO: type: Literal["m", "h", "x", "b"]
		...

	@defiFormat.setter
	def defiFormat(self, defiFormat: str) -> None:
		# TODO: type: Literal["m", "h", "x", "b"]
		...

	def detectDefiFormat(self, default: str = "") -> str: ...

	def addAlt(self, alt: str) -> None: ...

	def editFuncWord(self, func: Callable[[str], str]) -> None: ...

	def editFuncDefi(self, func: Callable[[str], str]) -> None: ...

	def strip(self) -> None: ...

	def replaceInWord(self, source: str, target: str) -> None: ...

	def replaceInDefi(self, source: str, target: str) -> None: ...

	def replace(self, source: str, target: str) -> None: ...

	def byteProgress(self) -> tuple[int, int] | None: ...

	def removeEmptyAndDuplicateAltWords(self) -> None: ...

	def stripFullHtml(self) -> str | None: ...


class EntryListType(typing.Protocol):
	def __init__(
		self,
		entryToRaw: Callable[[EntryType], RawEntryType],
		entryFromRaw: Callable[[RawEntryType], EntryType],
	) -> None: ...

	def append(self, entry: EntryType) -> None: ...

	def clear(self) -> None: ...

	def __len__(self) -> int: ...

	def __iter__(self) -> Iterator[EntryType]: ...

	def hasSortKey(self) -> bool: ...

	def setSortKey(
		self,
		namedSortKey: NamedSortKey,
		sortEncoding: str | None,
		writeOptions: dict[str, Any],
	) -> None: ...

	def sort(self) -> None: ...

	def close(self) -> None: ...


class GlossaryType(typing.Protocol):  # noqa: PLR0904

	"""
	an abstract type class for Glossary class in plugins. it only
	contains methods and properties that might be used in plugins.
	"""

	def __iter__(self) -> Iterator[EntryType]: ...

	def __len__(self) -> int: ...

	def setDefaultDefiFormat(self, defiFormat: str) -> None: ...

	def getDefaultDefiFormat(self) -> str: ...

	def collectDefiFormat(
		self,
		maxCount: int,
	) -> dict[str, float] | None: ...

	def iterInfo(self) -> Iterator[tuple[str, str]]: ...

	def getInfo(self, key: str) -> str: ...

	def setInfo(self, key: str, value: str) -> None: ...

	def getExtraInfos(self, excludeKeys: list[str]) -> dict[str, str]: ...

	@property
	def author(self) -> str: ...

	@property
	def alts(self) -> bool: ...

	@property
	def filename(self) -> str: ...

	@property
	def tmpDataDir(self) -> str: ...

	@property
	def readOptions(self) -> dict | None: ...

	@property
	def sqlite(self) -> bool: ...

	@property
	def sourceLang(self) -> Lang | None: ...

	@property
	def targetLang(self) -> Lang | None: ...

	@property
	def sourceLangName(self) -> str: ...

	@sourceLangName.setter
	def sourceLangName(self, langName: str) -> None: ...

	@property
	def targetLangName(self) -> str: ...

	@targetLangName.setter
	def targetLangName(self, langName: str) -> None: ...

	def titleTag(self, sample: str) -> str: ...

	def wordTitleStr(
		self,
		word: str,
		sample: str = "",
		class_: str = "",
	) -> str: ...

	def getConfig(self, name: str, default: str | None) -> str | None: ...

	def addEntry(self, entry: EntryType) -> None: ...

	def newEntry(
		self,
		word: MultiStr,
		defi: str,
		defiFormat: str = "",
		byteProgress: tuple[int, int] | None = None,
	) -> EntryType: ...

	def newDataEntry(self, fname: str, data: bytes) -> EntryType: ...

	def stripFullHtml(
		self,
		errorHandler: Callable[[EntryType, str], None] | None = None,
	) -> None: ...

	def preventDuplicateWords(self) -> None: ...

	def mergeEntriesWithSameHeadwordPlaintext(self) -> None: ...

	def removeHtmlTagsAll(self) -> None: ...

	def addCleanupPath(self, path: str) -> None: ...

	@property
	def progressbar(self) -> bool: ...


class GlossaryExtendedType(GlossaryType, typing.Protocol):
	def progressInit(
		self,
		*args,  # noqa: ANN002
	) -> None: ...

	def progress(self, pos: int, total: int, unit: str = "entries") -> None: ...

	def progressEnd(self) -> None: ...

	@property
	def progressbar(self) -> bool: ...

	@progressbar.setter
	def progressbar(self, enabled: bool) -> None: ...
