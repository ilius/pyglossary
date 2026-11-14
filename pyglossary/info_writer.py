"""
This module is used in plugins.

Write PyGlossary ``.info`` metadata sidecar files.

``InfoWriter`` streams glossary metadata (title, languages, author, entry count,
and extra info keys) to a text info file alongside converted dictionary output.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from os.path import splitext
from typing import TYPE_CHECKING, Any

from .core import log
from .langs.writing_system import getWritingSystemFromText
from .utils.io_utils import nullTextIO
from .utils.json_utils import dataToPrettyJson

if TYPE_CHECKING:
	import io
	from collections.abc import Generator

	from .stubs.glossary_types import (
		EntryType,
		WriterGlossaryType,
	)

__all__ = ["InfoWriter"]

re_possible_html = re.compile(
	r"<[a-z1-6]+[ />]",
	re.IGNORECASE,
)
re_style = re.compile(
	r"<([a-z1-6]+)[^<>]* style=",
	re.IGNORECASE | re.DOTALL,
)


@dataclass
class _Counters:
	entryCount: int = 0
	bwordCount: int = 0
	nonLowercaseTermCount: int = 0
	styleByTagCounter: dict[str, int] = field(default_factory=Counter)
	defiFormatCounter: dict[str, int] = field(default_factory=Counter)
	firstTagCounter: dict[str, int] = field(default_factory=Counter)
	allTagsCounter: dict[str, int] = field(default_factory=Counter)
	sourceScriptCounter: dict[str, int] = field(default_factory=Counter)
	dataEntryExtCounter: dict[str, int] = field(default_factory=Counter)


class InfoWriter:
	"""Write glossary info metadata files."""

	def __init__(self, glos: WriterGlossaryType) -> None:
		self._glos = glos
		self._filename = ""
		self._file: io.TextIOBase = nullTextIO
		self._writeOptions: dict[str, Any] | None = None

	def setWriteOptions(self, options: dict[str, Any]) -> None:
		self._writeOptions = options

	def open(self, filename: str) -> None:
		self._filename = filename
		self._file = open(filename, mode="w", encoding="utf-8")

	def finish(self) -> None:
		self._filename = ""
		self._file.close()
		self._file = nullTextIO

	def _countEntry(self, entry: EntryType, counters: _Counters) -> None:
		defi = entry.defi

		counters.entryCount += 1
		counters.bwordCount += defi.count("bword://")

		for term in entry.l_term:
			if term.lower() != term:
				counters.nonLowercaseTermCount += 1

		for m in re_style.finditer(defi):
			counters.styleByTagCounter[m.group(1)] += 1

		defiFormat = entry.detectDefiFormat("")
		counters.defiFormatCounter[defiFormat] += 1
		if defiFormat == "m":
			if re_possible_html.match(defi):
				log.warning(f"undetected html defi: {defi}")
		elif defiFormat == "h":
			match = re_possible_html.search(defi)
			if match is not None:
				counters.firstTagCounter[match.group().strip("< />").lower()] += 1
				for tag in re_possible_html.findall(defi):
					counters.allTagsCounter[tag.strip("< />").lower()] += 1
		elif defiFormat == "b":
			ext = splitext(entry.s_term)[1].lstrip(".")
			counters.dataEntryExtCounter[ext] += 1

		ws = getWritingSystemFromText(entry.s_term)
		if ws:
			wsName = ws.name
		else:
			log.debug(f"No script detected for term: {entry.s_term}")
			wsName = "None"
		counters.sourceScriptCounter[wsName] += 1

	def _buildInfo(self, counters: _Counters) -> dict[str, Any]:
		defiFormatCounter = counters.defiFormatCounter.copy()
		data_entry_count = defiFormatCounter.pop("b", 0)

		info: dict[str, Any] = dict(self._glos.iterInfo())
		info["word_count"] = counters.entryCount
		info["bword_count"] = counters.bwordCount
		info["non_lowercase_word_count"] = counters.nonLowercaseTermCount
		info["data_entry_count"] = data_entry_count
		info["data_entry_extension_count"] = _formatCounter(
			counters.dataEntryExtCounter,
		)
		info["defi_format"] = ", ".join(
			f"{defiFormat}={count}"
			for defiFormat, count in sorted(defiFormatCounter.items())
		)
		info["defi_tag"] = _formatCounter(counters.allTagsCounter)
		info["defi_first_tag"] = _formatCounter(counters.firstTagCounter)
		info["style"] = _formatCounter(counters.styleByTagCounter)
		info["source_script"] = _formatCounter(counters.sourceScriptCounter)
		if self._writeOptions is not None:
			info["write_options"] = self._writeOptions
		info["read_options"] = self._glos.readOptions
		return info

	def write(self) -> Generator[None, EntryType, None]:
		counters = _Counters()
		while True:
			entry = yield
			if entry is None:
				break
			self._countEntry(entry, counters)

		info = self._buildInfo(counters)
		self._file.write(dataToPrettyJson(info) + "\n")


def _formatCounter(counter: dict[str, int]) -> str:
	return ", ".join(f"{name}={count}" for name, count in counter.most_common())
