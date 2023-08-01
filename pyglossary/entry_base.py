# -*- coding: utf-8 -*-

import typing

# from typing import TYPE_CHECKING


MultiStr: "typing.TypeAlias" = "str | list[str]"


class BaseEntry:
	__slots__: "list[str]" = [
		"_word",
	]

	def __init__(self) -> None:
		self._word: "str | list[str]"

	@property
	def s_word(self) -> str:
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
