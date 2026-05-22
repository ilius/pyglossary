# -*- coding: utf-8 -*-
from __future__ import annotations

import html
from typing import TYPE_CHECKING

from pyglossary.text_reader import TextGlossaryReader

if TYPE_CHECKING:
	from pyglossary.glossary_types import ReaderGlossaryType
	from pyglossary.text_reader import nextBlockResultType

__all__ = ["Reader"]

# CLAWS7 tag first letter; see https://ucrel.lancs.ac.uk/claws7tags.html
POS_NAMES: dict[str, str] = {
	"a": "determiner",
	"c": "conjunction",
	"d": "WH-determiner",
	"e": "adverb",
	"g": "genitive",
	"i": "preposition",
	"j": "adjective",
	"m": "cardinal numeral",
	"n": "noun",
	"p": "pronoun",
	"r": "adverb",
	"s": "subordinating conjunction",
	"t": "infinitive marker",
	"u": "interjection",
	"v": "verb",
	"x": "negative",
	"y": "pronoun",
	"z": "spelling",
}

GENRES: tuple[str, ...] = (
	"blog",
	"web",
	"TVM",
	"spok",
	"fic",
	"mag",
	"news",
	"acad",
)

GENRE_LABELS: dict[str, str] = {
	"blog": "Blog",
	"web": "Web",
	"TVM": "TV/Movies",
	"spok": "Spoken",
	"fic": "Fiction",
	"mag": "Magazine",
	"news": "News",
	"acad": "Academic",
}

DEFI_TEMPLATE = """\
<div class="wordfrequency">
<style>.wordfrequency th,.wordfrequency td{{text-align:left}}.wordfrequency th:not(:last-child),.wordfrequency td:not(:last-child){{padding-right:1.5em}}</style>
<h3><font class="pos grammar" color="{gram_color}">{pos_name}</font></h3>
<table>
<tbody>
<tr><td>Rank</td><td>{rank}</td></tr>
<tr><td>Frequency</td><td>{freq}</td></tr>
<tr><td>Per million</td><td>{per_mil}</td></tr>
<tr><td>% capitalized</td><td>{pct_caps}</td></tr>
<tr><td>% all caps</td><td>{pct_allc}</td></tr>
<tr><td>Range</td><td>{range_}</td></tr>
<tr><td>Dispersion</td><td>{disp}</td></tr>
</tbody>
</table>
<h4>Frequency by genre</h4>
<table>
<thead><tr><th>Genre</th><th>Count</th><th>Per million</th></tr></thead>
<tbody>
{genre_rows}
</tbody>
</table>
</div>
"""

GENRE_ROW_TEMPLATE = "<tr><td>{label}</td><td>{count}</td><td>{per_mil}</td></tr>\n"


def _parse_int(value: str) -> int:
	try:
		return int(value.replace(",", ""))
	except ValueError:
		return 0


def _format_int(value: str) -> str:
	try:
		return f"{int(value):,}"
	except ValueError:
		return value


def _pos_name(pos: str) -> str:
	if not pos:
		return ""
	key = pos[0].lower()
	name = POS_NAMES.get(key)
	if name:
		return name.title()
	return pos


class Reader(TextGlossaryReader):
	useByteProgress = True
	_gram_color: str = "green"

	def __init__(self, glos: ReaderGlossaryType, hasInfo: bool = False) -> None:
		TextGlossaryReader.__init__(self, glos, hasInfo=hasInfo)
		self._columns: list[str] = []
		self._colIndex: dict[str, int] = {}

	def open(self, filename: str) -> None:
		self._glos.setDefaultDefiFormat("h")
		self._columns = []
		self._colIndex = {}
		TextGlossaryReader.open(self, filename)
		self._readPreamble()

	def newEntry(self, word, defi: str):  # noqa: ANN001, ANN201
		entry = TextGlossaryReader.newEntry(self, word, defi)
		entry.defiFormat = "h"
		return entry

	def _setColumns(self, columns: list[str]) -> None:
		self._columns = columns
		self._colIndex = {name: i for i, name in enumerate(columns)}

	def _readPreamble(self) -> None:
		description_lines: list[str] = []
		while True:
			line = self.readline()
			if not line:
				return
			line = line.rstrip("\n")
			if not line:
				continue
			if line.startswith("*"):
				description_lines.append(line.lstrip("* ").strip())
				continue
			if line.startswith("-----"):
				continue
			if line.startswith("rank\t"):
				self._setColumns(line.split("\t"))
				if description_lines:
					self.setInfo("description", "\n".join(description_lines))
				self.setInfo("name", "Word Frequency (COCA)")
				self.setInfo("website", "https://www.wordfrequency.info/")
				return

	def _col(self, parts: list[str], name: str) -> str:
		index = self._colIndex.get(name)
		if index is None or index >= len(parts):
			return ""
		return parts[index]

	def _renderDefinition(self, parts: list[str]) -> str:
		pos = self._col(parts, "PoS")
		genre_items: list[tuple[str, str, str]] = []
		for genre in GENRES:
			count = self._col(parts, genre)
			per_mil = self._col(parts, f"{genre}PM")
			if _parse_int(count) == 0:
				continue
			genre_items.append((genre, count, per_mil))
		genre_items.sort(key=lambda item: _parse_int(item[1]), reverse=True)
		genre_rows: list[str] = []
		for genre, count, per_mil in genre_items:
			genre_rows.append(
				GENRE_ROW_TEMPLATE.format(
					label=html.escape(GENRE_LABELS.get(genre, genre)),
					count=html.escape(_format_int(count)),
					per_mil=html.escape(per_mil),
				),
			)
		return DEFI_TEMPLATE.format(
			pos_name=html.escape(_pos_name(pos)),
			gram_color=html.escape(self._gram_color),
			rank=html.escape(self._col(parts, "rank")),
			freq=html.escape(_format_int(self._col(parts, "freq"))),
			per_mil=html.escape(self._col(parts, "perMil")),
			pct_caps=html.escape(self._col(parts, "%caps")),
			pct_allc=html.escape(self._col(parts, "%allC")),
			range_=html.escape(_format_int(self._col(parts, "range"))),
			disp=html.escape(self._col(parts, "disp")),
			genre_rows="".join(genre_rows),
		)

	def _makeBlock(self, parts: list[str]) -> nextBlockResultType:
		lemma = self._col(parts, "lemma")
		if not lemma:
			return None
		return lemma, self._renderDefinition(parts), None

	def nextBlock(self) -> nextBlockResultType:
		if not self._file:
			raise StopIteration
		while True:
			line = self.readline()
			if not line:
				raise StopIteration
			line = line.rstrip("\n")
			if not line:
				continue
			if line.startswith(("*", "-----")):
				continue
			if line.startswith("rank\t"):
				self._setColumns(line.split("\t"))
				continue
			parts = line.split("\t")
			if len(parts) < 3:
				continue
			if not self._colIndex:
				self._setColumns(
					[
						"rank",
						"lemma",
						"PoS",
						"freq",
						"perMil",
						"%caps",
						"%allC",
						"range",
						"disp",
						*GENRES,
						*(f"{g}PM" for g in GENRES),
					],
				)
			block = self._makeBlock(parts)
			if block:
				return block
