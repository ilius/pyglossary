"""This module is used in plugins."""

from __future__ import annotations

from collections.abc import (
	Callable,
	Iterable,
	Iterator,
	Sequence,
)
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
	from .langs import Lang
	from .sort_keys import NamedSortKey

__all__ = [
	"Callable",
	"EntryListType",
	"EntryType",
	"GlossaryInfoCommonType",
	"RawEntryType",
	"ReaderGlossaryType",
	"WriterGlossaryType",
]

type MultiStr = str | list[str]

# str(rawEntry[0]): defiFormat or ""
# rawEntry[1]: b_defi
# rawEntry[2:]: b_term_list
type RawEntryType = Sequence[bytes]


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
	def s_term(self) -> str: ...

	@property
	def l_term(self) -> list[str]: ...

	@property
	def lb_term(self) -> list[bytes]: ...

	@property
	def defi(self) -> str: ...

	@property
	def b_term(self) -> bytes: ...

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

	def editFuncTerm(
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

	def removeEmptyAndDuplicateAltTerms(self) -> None: ...

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
	def __getitem__(self, key: str) -> str: ...

	def __setitem__(self, key: str, value: object) -> None: ...

	def __sub__(self, exclude_keys: Iterable[str]) -> dict[str, str]: ...

	def getInfo(self, key: str) -> str: ...

	def setInfo(self, key: str, value: object) -> None: ...

	def iterInfo(self) -> Iterator[tuple[str, str]]: ...

	def getExtraInfos(self, excludeKeys: list[str]) -> dict[str, str]: ...

	def infoKeys(self) -> list[str]: ...

	def titleTag(self, sample: str) -> str: ...

	def detectLangsFromName(self) -> None: ...

	@property
	def name(self) -> str: ...

	@name.setter
	def name(self, value: object) -> None: ...

	@property
	def copyright(self) -> str: ...

	@copyright.setter  # noqa: A003
	def copyright(self, value: object) -> None: ...

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

	@author.setter
	def author(self, value: object) -> None: ...

	@property
	def creationTime(self) -> str: ...

	@creationTime.setter
	def creationTime(self, value: object) -> None: ...


class ReaderGlossaryType(Protocol):
	@property
	def info(self) -> GlossaryInfoCommonType: ...

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

	@property
	def alts(self) -> bool: ...

	@property
	def tmpDataDir(self) -> str: ...

	def getConfig(self, name: str, default: Any) -> Any: ...


class WriterGlossaryType(Protocol):
	@property
	def info(self) -> GlossaryInfoCommonType: ...

	@property
	def filename(self) -> str: ...

	def __iter__(self) -> Iterator[EntryType]: ...

	def collectDefiFormat(
		self,
		maxCount: int,
	) -> dict[str, float] | None: ...

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
	def readOptions(self) -> dict[str, Any] | None: ...

	@property
	def sqlite(self) -> bool: ...

	def stripFullHtml(
		self,
		errorHandler: Callable[[EntryType, str], None] | None = None,
	) -> None: ...

	def preventDuplicateWords(self) -> None: ...

	def mergeEntriesWithSameHeadwordPlaintext(self) -> None: ...

	def removeHtmlTagsAll(self) -> None: ...

	def getConfig(self, name: str, default: Any) -> Any: ...
