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
	bytes,  # compressed
	Tuple[bytes, bytes],  # uncompressed, without defiFormat
	Tuple[bytes, bytes, str],  # uncompressed, with defiFormat
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

	@property
	def word(self) -> str:
		raise NotImplementedError

	@property
	def words(self) -> List[str]:
		raise NotImplementedError

	@property
	def defi(self) -> str:
		raise NotImplementedError

	@property
	def defis(self) -> List[str]:
		raise NotImplementedError

	@property
	def b_word(self):
		"""
			returns bytes of word,
				and all the alternate words
				seperated by b"|"
		"""
		return self.word.encode("utf-8")

	@property
	def b_defi(self):
		"""
			returns bytes of definition,
				and all the alternate definitions
				seperated by b"|"
		"""
		return self.defi.encode("utf-8")

	@property
	def defiFormat(self) -> str:
		# TODO: type: Literal["m", "h", "x", "b"]
		raise NotImplementedError

	@defiFormat.setter
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

	def getRaw(self, glos: "GlossaryType") -> RawEntryType:
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
