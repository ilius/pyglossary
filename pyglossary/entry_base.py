# -*- coding: utf-8 -*-

from typing import (
	List,
	Tuple,
	Callable,
	Union,
	Any,
	Optional,
)

MultiStr = Union[str, List[str]]

RawEntryType = Union[
	Tuple[MultiStr, MultiStr],
	Tuple[MultiStr, MultiStr, str],
]


class BaseEntry(object):
	def isData(self) -> bool:
		raise NotImplementedError

	def getFileName(self) -> str:
		raise NotImplementedError

	def getData(self) -> bytes:
		raise NotImplementedError

	def save(self, directory: str) -> str:
		raise NotImplementedError

	def getWord(self) -> str:
		raise NotImplementedError

	def getWords(self) -> List[str]:
		raise NotImplementedError

	def getDefi(self) -> str:
		raise NotImplementedError

	def getDefis(self) -> List[str]:
		raise NotImplementedError

	def getDefiFormat(self) -> str:
		# TODO: type: Literal["m", "h", "x", "b"]
		raise NotImplementedError

	def setDefiFormat(self, defiFormat: str) -> None:
		# TODO: type: Literal["m", "h", "x", "b"]
		raise NotImplementedError

	def detectDefiFormat(self) -> None:
		raise NotImplementedError

	def addAlt(self, alt: str) -> None:
		raise NotImplementedError

	def editFuncWord(self, func: Callable[[str], str]) -> None:
		raise NotImplementedError

	def editFuncDefi(self, func: Callable[[str], str]) -> None:
		raise NotImplementedError

	def strip(self) -> None:
		raise NotImplementedError

	def replaceInWord(self, source: str, target: str) -> None:
		raise NotImplementedError

	def replaceInDefi(self, source: str, target: str) -> None:
		raise NotImplementedError

	def replace(self, source: str, target: str) -> None:
		raise NotImplementedError

	def getRaw(self) -> RawEntryType:
		raise NotImplementedError

	@staticmethod
	def getEntrySortKey(
		key: Optional[Callable[[str], Any]] = None,
	) -> Callable[["BaseEntry"], Any]:
		raise NotImplementedError

	@staticmethod
	def getRawEntrySortKey(
		key: Optional[Callable[[str], Any]] = None,
	) -> Callable[[Tuple], str]:
		raise NotImplementedError
