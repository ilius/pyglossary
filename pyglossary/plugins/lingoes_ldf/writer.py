"""
Write Lingoes ``.ldf`` source dictionary files.

Serializes glossary entries to Lingoes LDF markup with headwords, translations,
and examples. Applies LDF escaping and optional compression for Lingoes import
tools.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pyglossary.compress import (
	# compressionOpen,
	stdCompressions,
)

if TYPE_CHECKING:
	from collections.abc import Generator

	from pyglossary.stubs.glossary_types import EntryType, WriterGlossaryType

__all__ = ["Writer"]


class Writer:
	"""Write glossary files in Lingoes LDF format."""

	compressions = stdCompressions

	_newline: str = "\n"
	_resources: bool = True

	def __init__(self, glos: WriterGlossaryType) -> None:
		self._glos = glos
		self._filename = ""

	def finish(self) -> None:
		self._filename = ""

	def open(self, filename: str) -> None:
		self._filename = filename

	@staticmethod
	def _defiEscapeFunc(defi: str) -> str:
		return defi.replace("\n", "<br/>")

	def write(self) -> Generator[None, EntryType, None]:
		from pyglossary.text_writer import writeTxt

		newline = self._newline
		resources = self._resources
		info = self._glos.info
		head = (
			f"###Title: {info.name}\n"
			f"###Description: {info.description}\n"
			f"###Author: {info.author.replace('\n', '<br>')}\n"
			f"###Email: {info['email']}\n"
			f"###Website: {info['website']}\n"
			f"###Copyright: {info.copyright.replace('\n', '<br>')}\n"
		)
		yield from writeTxt(
			self._glos,
			entryFmt="{word}\n{defi}\n\n",
			filename=self._filename,
			writeInfo=False,
			defiEscapeFunc=self._defiEscapeFunc,
			ext=".ldf",
			head=head,
			newline=newline,
			resources=resources,
		)
