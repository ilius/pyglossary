# -*- coding: utf-8 -*-

from __future__ import annotations

import typing
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from collections.abc import Callable

__all__ = ["BaseEntry", "MultiStr"]

MultiStr: typing.TypeAlias = "str | list[str]"


class BaseEntry:  # noqa: PLR0904
	__slots__: list[str] = [
		"_word",
	]

	def __init__(self) -> None:
		self._word: str | list[str]

		def isData(self) -> bool: ...

	def getFileName(self) -> str:
		raise NotImplementedError

	@property
	def data(self) -> bytes:
		raise NotImplementedError

	def size(self) -> int:
		raise NotImplementedError

	def save(self, directory: str) -> str:
		raise NotImplementedError

	@property
	def s_word(self) -> str:
		raise NotImplementedError

	@property
	def l_word(self) -> list[str]:
		raise NotImplementedError

	@property
	def lb_word(self) -> list[bytes]:
		raise NotImplementedError

	@property
	def defi(self) -> str:
		raise NotImplementedError

	@property
	def b_word(self) -> bytes:
		"""Returns bytes of word and all the alternate words separated by b"|"."""
		return self.s_word.encode("utf-8")

	@property
	def b_defi(self) -> bytes:
		"""Returns definition in bytes."""
		return self.defi.encode("utf-8")

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
