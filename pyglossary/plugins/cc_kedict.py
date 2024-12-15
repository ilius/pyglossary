# -*- coding: utf-8 -*-
# mypy: ignore-errors
from __future__ import annotations

from io import BytesIO
from os.path import isdir, join
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
	from collections.abc import Callable, Iterator

	import lxml

	from pyglossary.glossary_types import EntryType, GlossaryType
	from pyglossary.option import Option

from pyglossary.core import exc_note, log, pip
from pyglossary.text_reader import TextGlossaryReader

__all__ = [
	"Reader",
	"description",
	"enable",
	"extensionCreate",
	"extensions",
	"kind",
	"lname",
	"name",
	"optionsProp",
	"singleFile",
	"website",
	"wiki",
]

enable = True
lname = "cc_kedict"
name = "cc-kedict"
description = "cc-kedict"
extensions = ()
extensionCreate = ""
singleFile = True
kind = "text"
wiki = ""
website = (
	"https://github.com/mhagiwara/cc-kedict",
	"@mhagiwara/cc-kedict",
)
optionsProp: dict[str, Option] = {}


class YamlReader(TextGlossaryReader):
	tagStyle = (
		"color:white;"
		"background:green;"
		"padding-left:3px;"
		"padding-right:3px;"
		"border-radius:0.5ex;"
		# 0.5ex ~= 0.3em, but "ex" is recommended
	)

	def __init__(  # noqa: PLR0913
		self,
		glos: GlossaryType,
		spellKey: str = "",
		posKey: str = "",
		synsKey: str = "",
		tagsKey: str = "",
	) -> None:
		TextGlossaryReader.__init__(self, glos)
		self._spellKey = spellKey
		self._posKey = posKey
		self._synsKey = synsKey
		self._tagsKey = tagsKey

		self._posMapping = {
			"n": "noun",
			"v": "verb",
			"a": "adjective",
			"pron": "pronoun",
			"propn": "proper noun",
			"intj": "interjection",
			"det": "determiner",
			"part": "particle",
			"adv": "adverb",
			"num": "number",
			"abbrev": "abbreviation",
			"suf": "suffix",
			"pref": "prefix",
		}

	@classmethod
	def isInfoWord(cls, _word: str) -> bool:
		return False

	@classmethod
	def fixInfoWord(cls, _word: str) -> str:
		return ""

	@staticmethod
	def _makeList(
		hf: lxml.etree.htmlfile,
		input_objects: list[Any],
		processor: Callable,
		single_prefix: str | None = None,
		skip_single: bool = True,
	) -> None:
		"""Wrap elements into <ol> if more than one element."""
		if not input_objects:
			return

		if skip_single and len(input_objects) == 1:
			# if single_prefix is None:
			# 	single_prefix = ET.Element("br")
			if single_prefix:
				hf.write(single_prefix)
			processor(hf, input_objects[0], 1)
			return

		with hf.element("ol"):
			for el in input_objects:
				with hf.element("li"):
					processor(hf, el, len(input_objects))

	def _processExample(  # noqa: PLR6301
		self,
		hf: lxml.etree.htmlfile,
		exampleDict: dict,
		_count: int,
	) -> None:
		from lxml import etree as ET

		if not exampleDict.get("example"):
			log.error(f"invalid example: {exampleDict}")
			return

		hf.write(exampleDict["example"])

		transliteration = exampleDict.get("transliteration")
		if transliteration:
			hf.write(ET.Element("br"))
			with hf.element("font", color="green"):
				hf.write(f"{transliteration}")

		translation = exampleDict.get("translation")
		if translation:
			hf.write(ET.Element("br"))
			with hf.element("i"):
				hf.write(f"{translation}")

	def _processDef(
		self,
		hf: lxml.etree.htmlfile,
		defDict: dict,
		count: int,
	) -> None:
		from lxml import etree as ET

		text = defDict.get("def", "")
		if text:
			hf.write(text)

		examples = defDict.get("examples")
		if examples:
			if text:
				if count == 1:
					hf.write(ET.Element("br"))
				hf.write(ET.Element("br"))
			with hf.element("i"):
				hf.write("Examples:")
			self._makeList(
				hf,
				examples,
				self._processExample,
				skip_single=False,
			)

	def _processNote(  # noqa: PLR6301
		self,
		hf: lxml.etree.htmlfile,
		note: str,
		_count: int,
	) -> None:
		hf.write(note)

	def _processEntry(
		self,
		hf: lxml.etree.htmlfile,
		edict: dict,
	) -> None:
		from lxml import etree as ET

		if self._spellKey and self._spellKey in edict:
			spelling = edict[self._spellKey]
			if not isinstance(spelling, str):
				log.error(f"{spelling=}, {type(spelling)=}, {edict=}")
				# https://github.com/mhagiwara/cc-kedict/pull/1
				spelling = "on" if spelling is True else ""
			if spelling:
				with hf.element("font", color="green"):
					hf.write(spelling)
				hf.write(ET.Element("br"))

		if self._posKey and self._posKey in edict:
			pos = edict[self._posKey]
			pos = self._posMapping.get(pos, pos)
			with hf.element("i"):
				hf.write(pos.capitalize())
			hf.write(ET.Element("br"))

		if self._tagsKey and self._tagsKey in edict:
			tags = edict[self._tagsKey]
			for i, tag in enumerate(tags):
				if i > 0:
					hf.write(" ")
				with hf.element("span", style=self.tagStyle):
					hf.write(tag)
			hf.write(ET.Element("br"))

		defs = edict.get("defs")
		if defs:
			self._makeList(
				hf,
				defs,
				self._processDef,
			)

		if self._synsKey and self._synsKey in edict:
			hf.write("Synonyms: ")
			for i, word in enumerate(edict[self._synsKey]):
				if i > 0:
					with hf.element("big"):
						hf.write(" | ")  # NESTED: 5
				with hf.element("a", href=f"bword://{word}"):
					hf.write(word)
			hf.write(ET.Element("br"))

		notes = edict.get("notes")
		if notes:
			hf.write(ET.Element("br"))
			hf.write("Notes:")
			self._makeList(
				hf,
				notes,
				self._processNote,
				skip_single=False,
			)

	def _createEntry(
		self,
		yamlBlock: str,
	) -> tuple[str, str, None] | None:
		from lxml import etree as ET
		from yaml import load

		try:
			from yaml import CLoader as Loader
		except ImportError:
			from yaml import Loader

		edict = load(yamlBlock, Loader=Loader)
		word = edict.get("word")
		if not word:
			log.error(f"no word in {edict}")
			return None

		f = BytesIO()

		with ET.htmlfile(f, encoding="utf-8") as hf:
			with hf.element("div"):
				self._processEntry(hf, edict)

		defi = f.getvalue().decode("utf-8")
		return word, defi, None

	def nextBlock(self) -> EntryType:
		if not self._file:
			raise StopIteration
		lines: list[str] = []
		while True:
			line = self.readline()
			if not line:
				break
			line = line.rstrip("\n\r")
			if not line:
				continue
			if line.startswith("- "):
				line = " " + line[1:]
				if lines:
					self._bufferLine = line
					return self._createEntry("\n".join(lines))

			lines.append(line)

		if lines:
			return self._createEntry("\n".join(lines))

		raise StopIteration


class Reader:
	depends = {
		"yaml": "PyYAML",
		"lxml": "lxml",
	}

	def __init__(self, glos: GlossaryType) -> None:
		self._glos = glos
		self._yaml = YamlReader(
			glos,
			spellKey="romaja",
			posKey="pos",
			synsKey="syns",
			tagsKey="tags",
		)

	def __len__(self) -> int:
		return 0

	def open(self, filename: str) -> None:
		try:
			from lxml import etree as ET  # noqa: F401
		except ModuleNotFoundError as e:
			exc_note(e, f"Run `{pip} install lxml` to install")
			raise

		if isdir(filename):
			filename = join(filename, "kedict.yml")
		self._filename = filename

		self._glos.sourceLangName = "Korean"
		self._glos.targetLangName = "English"

		self._glos.setDefaultDefiFormat("h")
		self._yaml.open(filename)

	def close(self) -> None:
		self._yaml.close()

	def __iter__(self) -> Iterator[EntryType]:
		yield from self._yaml
