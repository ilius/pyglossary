from __future__ import annotations

from os.path import splitext
from typing import TYPE_CHECKING, Any

from pyglossary.core import log
from pyglossary.io_utils import nullTextIO

if TYPE_CHECKING:
	import io
	from collections.abc import Generator

	from pyglossary.glossary_types import (
		EntryType,
		GlossaryType,
	)


class InfoWriter:
	def __init__(self, glos: GlossaryType) -> None:
		self._glos = glos
		self._filename = ""
		self._file: io.TextIOBase = nullTextIO

	def open(self, filename: str) -> None:
		self._filename = filename
		self._file = open(filename, mode="w", encoding="utf-8")

	def finish(self) -> None:
		self._filename = ""
		self._file.close()
		self._file = nullTextIO

	def write(self) -> Generator[None, EntryType, None]:  # noqa: PLR0912, C901
		import re
		from collections import Counter

		from pyglossary.json_utils import dataToPrettyJson
		from pyglossary.langs.writing_system import getWritingSystemFromText

		glos = self._glos

		re_possible_html = re.compile(
			r"<[a-z1-6]+[ />]",
			re.IGNORECASE,
		)
		re_style = re.compile(
			r"<([a-z1-6]+)[^<>]* style=",
			re.IGNORECASE | re.DOTALL,
		)

		wordCount = 0
		bwordCount = 0

		nonLowercaseWordCount = 0

		styleByTagCounter: dict[str, int] = Counter()

		defiFormatCounter: dict[str, int] = Counter()
		firstTagCounter: dict[str, int] = Counter()
		allTagsCounter: dict[str, int] = Counter()
		sourceScriptCounter: dict[str, int] = Counter()
		dataEntryExtCounter: dict[str, int] = Counter()

		while True:
			entry = yield
			if entry is None:
				break
			defi = entry.defi

			wordCount += 1
			bwordCount += defi.count("bword://")

			for word in entry.l_word:
				if word.lower() != word:
					nonLowercaseWordCount += 1

			for m in re_style.finditer(defi):
				tag = m.group(1)
				styleByTagCounter[tag] += 1

			defiFormat = entry.detectDefiFormat("")
			defiFormatCounter[defiFormat] += 1
			if defiFormat == "m":
				if re_possible_html.match(defi):
					log.warning(f"undetected html defi: {defi}")
			elif defiFormat == "h":
				match = re_possible_html.search(defi)
				if match is not None:
					firstTagCounter[match.group().strip("< />").lower()] += 1
					for tag in re_possible_html.findall(defi):
						allTagsCounter[tag.strip("< />").lower()] += 1
			elif defiFormat == "b":
				_filenameNoExt, ext = splitext(entry.s_word)
				ext = ext.lstrip(".")
				dataEntryExtCounter[ext] += 1

			ws = getWritingSystemFromText(entry.s_word)
			if ws:
				wsName = ws.name
			else:
				log.debug(f"No script detected for word: {entry.s_word}")
				wsName = "None"
			sourceScriptCounter[wsName] += 1

		data_entry_count = defiFormatCounter["b"]
		del defiFormatCounter["b"]
		info: dict[str, Any] = dict(glos.iterInfo())
		info["word_count"] = wordCount
		info["bword_count"] = bwordCount
		info["non_lowercase_word_count"] = nonLowercaseWordCount
		info["data_entry_count"] = data_entry_count
		info["data_entry_extension_count"] = ", ".join(
			f"{ext}={count}" for ext, count in dataEntryExtCounter.most_common()
		)
		info["defi_format"] = ", ".join(
			f"{defiFormat}={count}"
			for defiFormat, count in sorted(defiFormatCounter.items())
		)
		info["defi_tag"] = ", ".join(
			f"{defiFormat}={count}"
			for defiFormat, count in allTagsCounter.most_common()
		)
		info["defi_first_tag"] = ", ".join(
			f"{defiFormat}={count}"
			for defiFormat, count in firstTagCounter.most_common()
		)
		info["style"] = ", ".join(
			f"{defiFormat}={count}"
			for defiFormat, count in styleByTagCounter.most_common()
		)
		info["source_script"] = ", ".join(
			f"{defiFormat}={count}"
			for defiFormat, count in sourceScriptCounter.most_common()
		)
		info["read_options"] = glos.readOptions
		self._file.write(dataToPrettyJson(info) + "\n")
