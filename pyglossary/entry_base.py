# -*- coding: utf-8 -*-

from .glossary_type import EntryType

MultiStr = "Union[str, List[str]]"


class BaseEntry(EntryType):
	__slots__ = []

	@property
	def b_word(self) -> bytes:
		"""
			returns bytes of word,
				and all the alternate words
				separated by b"|"
		"""
		return self.s_word.encode("utf-8")

	@property
	def b_defi(self) -> bytes:
		"""
			returns bytes of definition,
				and all the alternate definitions
				separated by b"|"
		"""
		return self.defi.encode("utf-8")
