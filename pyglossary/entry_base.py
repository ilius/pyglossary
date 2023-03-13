
import typing

# -*- coding: utf-8 -*-
from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
	from typing import TypeAlias

from .glossary_types import EntryType

MultiStr: "TypeAlias" = Union[str, list[str]]


class BaseEntry(EntryType):
	__slots__: "list[str]" = []

	@property
	def b_word(self: "typing.Self") -> bytes:
		"""
			returns bytes of word,
				and all the alternate words
				separated by b"|"
		"""
		return self.s_word.encode("utf-8")

	@property
	def b_defi(self: "typing.Self") -> bytes:
		"""
			returns bytes of definition,
				and all the alternate definitions
				separated by b"|"
		"""
		return self.defi.encode("utf-8")
