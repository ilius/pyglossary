# -*- coding: utf-8 -*-
from formats_common import *
from pyglossary.text_reader import TextGlossaryReader
from io import BytesIO
from os.path import dirname

enable = True
lname = "cc_kedict"
format = "cc-kedict"
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
optionsProp = {
}


class YamlReader(TextGlossaryReader):
	tagStyle = (
		"color:white;"
		"background:green;"
		"padding-left:3px;"
		"padding-right:3px;"
		"border-radius:0.5ex;"
		# 0.5ex ~= 0.3em, but "ex" is recommended
	)

	def __init__(
		self,
		glos: GlossaryType,
		spellKey: str = "",
		posKey: str = "",
		synsKey: str = "",
		tagsKey: str = "",
	):
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

	def isInfoWord(self, word):
		return False

	def fixInfoWord(self, word):
		return ""

	def _makeList(
		self,
		hf: "lxml.etree.htmlfile",
		input_objects: "List[Any]",
		processor: "Callable",
		single_prefix=None,
		skip_single=True
	):
		""" Wrap elements into <ol> if more than one element """
		from lxml import etree as ET

		if not input_objects:
			return

		if skip_single and len(input_objects) == 1:
			# if single_prefix is None:
			# 	single_prefix = ET.Element("br")
			hf.write(single_prefix)
			processor(hf, input_objects[0], 1)
			return

		with hf.element("ol"):
			for el in input_objects:
				with hf.element("li"):
					processor(hf, el, len(input_objects))

	def _processExample(
		self,
		hf: "lxml.etree.htmlfile",
		exampleDict: "Dict",
		count: int,
	):
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
		hf: "lxml.etree.htmlfile",
		defDict: "Dict",
		count: int,
	):
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

	def _processNote(
		self,
		hf: "lxml.etree.htmlfile",
		note: str,
		count: int,
	):
		hf.write(note)

	def _processEntry(
		self,
		hf: "lxml.etree.htmlfile",
		edict: "Dict",
	):
		from lxml import etree as ET

		if self._spellKey and self._spellKey in edict:
			spelling = edict[self._spellKey]
			if not isinstance(spelling, str):
				log.error(f"spelling = {spelling} type {type(spelling)}, edict={edict}")
				if spelling is True:
					# https://github.com/mhagiwara/cc-kedict/pull/1
					spelling = "on"
				else:
					spelling = ""
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
						hf.write(" | ")
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

	def _createEntry(self, yamlBlock: str):
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
			return

		f = BytesIO()

		with ET.htmlfile(f, encoding="utf-8") as hf:
			with hf.element("div"):
				self._processEntry(hf, edict)

		defi = f.getvalue().decode("utf-8")
		return word, defi

	def nextPair(self):
		if not self._file:
			raise StopIteration
		lines = []
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


class Reader(object):
	depends = {
		"yaml": "PyYAML",
		"lxml": "lxml",
	}

	def __init__(self, glos: GlossaryType):
		self._glos = glos
		self._yaml = YamlReader(
			glos,
			spellKey="romaja",
			posKey="pos",
			synsKey="syns",
			tagsKey="tags",
		)

	def __len__(self):
		return 0

	def open(self, filename: str) -> None:
		if isdir(filename):
			filename = join(filename, "kedict.yml")
		self._filename = filename

		self._glos.sourceLangName = "Korean"
		self._glos.targetLangName = "English"

		self._glos.setDefaultDefiFormat("h")
		self._yaml.open(filename)

	def close(self):
		self._yaml.close()

	def __iter__(self):
		for entry in self._yaml:
			yield entry
