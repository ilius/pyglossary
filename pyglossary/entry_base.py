
import typing

# -*- coding: utf-8 -*-
from typing import TYPE_CHECKING

from .glossary_types import EntryType

if TYPE_CHECKING:
	from typing import TypeAlias


MultiStr: "TypeAlias" = "str | list[str]"


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
