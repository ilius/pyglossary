# -*- coding: utf-8 -*-
from __future__ import annotations

from collections.abc import (
	Callable,
	Iterator,
	Sequence,
)
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
	from typing import TypeAlias

	from .langs import Lang
	from .sort_keys import NamedSortKey

__all__ = [
	"Callable",
	"EntryListType",
	"EntryType",
	"RawEntryType",
	"ReaderGlossaryType",
	"WriterGlossaryType",
]

MultiStr: TypeAlias = "str | list[str]"

# str(rawEntry[0]): defiFormat or ""
# rawEntry[1]: b_defi
# rawEntry[2:]: b_word_list
RawEntryType: TypeAlias = Sequence[bytes]


class EntryType(Protocol):  # noqa: PLR0904
	# def __init__(self) -> None: ...

	@classmethod
	def isData(cls) -> bool: ...

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

	def editFuncWord(
		self,
		func: Callable[[str], str],
	) -> None: ...

	def editFuncDefi(
		self,
		func: Callable[[str], str],
	) -> None: ...

	def strip(self) -> None: ...

	def replaceInWord(self, source: str, target: str) -> None: ...

	def replaceInDefi(self, source: str, target: str) -> None: ...

	def replace(self, source: str, target: str) -> None: ...

	def byteProgress(self) -> tuple[int, int] | None: ...

	def removeEmptyAndDuplicateAltWords(self) -> None: ...

	def stripFullHtml(self) -> str | None: ...

	@property
	def tmpPath(self) -> str | None: ...


class EntryListType(Protocol):
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


class GlossaryInfoCommonType(Protocol):
	def getInfo(self, key: str) -> str: ...

	def setInfo(self, key: str, value: str) -> None: ...

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

	@property
	def author(self) -> str: ...


class ReaderGlossaryType(GlossaryInfoCommonType, Protocol):
	def newEntry(
		self,
		word: MultiStr,
		defi: str,
		defiFormat: str = "",
		byteProgress: tuple[int, int] | None = None,
	) -> EntryType: ...

	def newDataEntry(self, fname: str, data: bytes) -> EntryType: ...

	@property
	def progressbar(self) -> bool: ...

	def setDefaultDefiFormat(self, defiFormat: str) -> None: ...

	def titleTag(self, sample: str) -> str: ...

	@property
	def alts(self) -> bool: ...

	def getConfig(self, name: str, default: str | None) -> str | None: ...


class WriterGlossaryType(GlossaryInfoCommonType, Protocol):
	# def __len__(self) -> int: ...

	# @property
	# def filename(self) -> str: ...

	def __iter__(self) -> Iterator[EntryType]: ...

	def collectDefiFormat(
		self,
		maxCount: int,
	) -> dict[str, float] | None: ...

	def iterInfo(self) -> Iterator[tuple[str, str]]: ...

	def getExtraInfos(self, excludeKeys: list[str]) -> dict[str, str]: ...

	def wordTitleStr(
		self,
		word: str,
		sample: str = "",
		class_: str = "",
	) -> str: ...

	@property
	def tmpDataDir(self) -> str: ...

	def addCleanupPath(self, path: str) -> None: ...

	@property
	def readOptions(self) -> dict | None: ...

	@property
	def sqlite(self) -> bool: ...

	def stripFullHtml(
		self,
		errorHandler: Callable[[EntryType, str], None] | None = None,
	) -> None: ...

	def preventDuplicateWords(self) -> None: ...

	def mergeEntriesWithSameHeadwordPlaintext(self) -> None: ...

	def removeHtmlTagsAll(self) -> None: ...

	def getConfig(self, name: str, default: str | None) -> str | None: ...
