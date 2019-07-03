# -*- coding: utf-8 -*-

from typing import (
	Dict,
	Tuple,
	List,
	Optional,
	Iterator,
	Callable,
)

from collections import OrderedDict as odict

from .entry_base import BaseEntry
from .entry import Entry, DataEntry

class GlossaryType(object):
	def addEntryObj(self, entry: Entry) -> None:
		raise NotImplementedError

	def newEntry(self, word: str, defi: str, defiFormat: str = "") -> Entry:
		raise NotImplementedError

	def addEntry(self, word: str, defi: str, defiFormat: str = "") -> None:
		raise NotImplementedError

	def iterEntryBuckets(self, size: int) -> Iterator[BaseEntry]:
		raise NotImplementedError

	def setDefaultDefiFormat(self, defiFormat: str) -> None:
		raise NotImplementedError

	def getMostUsedDefiFormats(self, count: int = None) -> List[Tuple[str, int]]:
		raise NotImplementedError

	def iterInfo(self) -> Iterator[Tuple[str, str]]:
		raise NotImplementedError

	def getInfo(self, key: str) -> str:
		raise NotImplementedError

	def setInfo(self, key: str, value: str) -> None:
		raise NotImplementedError

	def getExtraInfos(self, excludeKeys: List[str]) -> odict:
		raise NotImplementedError

	def getPref(self, name: str, default: Optional[str]) -> Optional[str]:
		raise NotImplementedError

	def newDataEntry(self, fname: str, data: bytes) -> DataEntry:
		raise NotImplementedError

	def writeTxt(
		self,
		sep1: str,
		sep2: str,
		filename: str = "",
		writeInfo: bool = True,
		rplList: Optional[List[Tuple[str, str]]] = None,
		ext: str = ".txt",
		head: str = "",
		iterEntries: Optional[Iterator[BaseEntry]] = None,
		entryFilterFunc: Optional[Callable[[BaseEntry], Optional[BaseEntry]]] = None,
		outInfoKeysAliasDict: Optional[Dict[str, str]] = None,
		encoding: str = "utf-8",
		newline: str = "\n",
		resources: bool = True,
	) -> bool:
		raise NotImplementedError

	def writeTabfile(self, filename: str = "", **kwargs) -> None:
		raise NotImplementedError

	def iterSqlLines(
		self,
		filename: str = "",
		infoKeys: Optional[List] = None,
		addExtraInfo: bool = True,
		newline: str = "\\n",
		transaction: bool = False,
	) -> Iterator[str]:
		raise NotImplementedError


