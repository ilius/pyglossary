# -*- coding: utf-8 -*-

from __future__ import annotations

import typing
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from collections.abc import Callable

__all__ = ["BaseEntry", "MultiStr"]

MultiStr: typing.TypeAlias = "str | list[str]"


class BaseEntry(ABC):  # noqa: PLR0904
	__slots__: list[str] = [
		"_term",
	]

	def __init__(self) -> None:
		self._term: str | list[str]

	@classmethod
	@abstractmethod
	def isData(cls) -> bool:
		raise NotImplementedError

	@abstractmethod
	def getFileName(self) -> str:
		raise NotImplementedError

	@property
	@abstractmethod
	def s_word(self) -> str:
		raise NotImplementedError

	@property
	@abstractmethod
	def l_word(self) -> list[str]:
		raise NotImplementedError

	@property
	@abstractmethod
	def lb_word(self) -> list[bytes]:
		raise NotImplementedError

	@property
	@abstractmethod
	def defi(self) -> str:
		raise NotImplementedError

	@property
	@abstractmethod
	def defiFormat(self) -> str:
		# TODO: type: Literal["m", "h", "x", "b"]
		raise NotImplementedError

	@defiFormat.setter
	@abstractmethod
	def defiFormat(self, defiFormat: str) -> None:
		# TODO: type: Literal["m", "h", "x", "b"]
		raise NotImplementedError

	@abstractmethod
	def detectDefiFormat(self, default: str = "") -> str:
		raise NotImplementedError

	@abstractmethod
	def addAlt(self, alt: str) -> None:
		raise NotImplementedError

	@abstractmethod
	def editFuncWord(self, func: Callable[[str], str]) -> None:
		raise NotImplementedError

	@abstractmethod
	def editFuncDefi(self, func: Callable[[str], str]) -> None:
		raise NotImplementedError

	@abstractmethod
	def strip(self) -> None:
		raise NotImplementedError

	@abstractmethod
	def replaceInWord(self, source: str, target: str) -> None:
		raise NotImplementedError

	@abstractmethod
	def replaceInDefi(self, source: str, target: str) -> None:
		raise NotImplementedError

	@abstractmethod
	def replace(self, source: str, target: str) -> None:
		raise NotImplementedError

	@abstractmethod
	def byteProgress(self) -> tuple[int, int] | None:
		raise NotImplementedError

	@abstractmethod
	def removeEmptyAndDuplicateAltWords(self) -> None:
		raise NotImplementedError

	@abstractmethod
	def stripFullHtml(self) -> str | None:
		raise NotImplementedError

	# ________________________________________________________

	@property
	def data(self) -> bytes:
		raise NotImplementedError

	def size(self) -> int:
		raise NotImplementedError

	def save(self, directory: str) -> str:
		raise NotImplementedError

	@property
	def tmpPath(self) -> str | None:
		raise NotImplementedError

	@property
	def b_word(self) -> bytes:
		"""Returns bytes of word and all the alternate words separated by b"|"."""
		return self.s_word.encode("utf-8")

	@property
	def b_defi(self) -> bytes:
		"""Returns definition in bytes."""
		return self.defi.encode("utf-8")
