# -*- coding: utf-8 -*-
from __future__ import annotations

import collections
from collections import Counter
from io import BytesIO, IOBase
from json import loads as json_loads
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
	from collections.abc import Callable, Iterator
	from typing import Any

	from pyglossary.glossary_types import EntryType, GlossaryType
	from pyglossary.lxml_types import Element, T_htmlfile


from pyglossary.compression import (
	compressionOpen,
	stdCompressions,
)
from pyglossary.core import exc_note, log, pip
from pyglossary.io_utils import nullBinaryIO
from pyglossary.option import (
	BoolOption,
	ListOption,
	Option,
	StrOption,
)

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
lname = "wiktextract"
name = "Wiktextract"
description = "Wiktextract (.jsonl)"
extensions = (".jsonl",)
extensionCreate = ".jsonl"
singleFile = True
kind = "text"
wiki = ""
website = (
	"https://github.com/tatuylonen/wiktextract",
	"@tatuylonen/wiktextract",
)
optionsProp: dict[str, Option] = {
	"resources": BoolOption(
		comment="Enable resources / data files",
	),
	"word_title": BoolOption(
		comment="Add headwords title to beginning of definition",
	),
	"pron_color": StrOption(
		comment="Pronunciation color",
	),
	"gram_color": StrOption(
		comment="Grammar color",
	),
	"example_padding": StrOption(
		comment="Padding for examples (css value)",
	),
	"audio": BoolOption(
		comment="Enable audio",
	),
	"audio_formats": ListOption(
		comment="List of audio formats to use",
	),
	"categories": BoolOption(
		comment="Enable categories",
	),
}


class Reader:
	compressions = stdCompressions
	depends = {
		"lxml": "lxml",
	}

	_word_title: bool = False
	_pron_color: str = "gray"
	_gram_color: str = "green"

	# 'top right' or 'top right bottom left'
	_example_padding: str = "10px 20px"

	_audio: bool = True

	_audio_formats: list[str] = ["ogg", "mp3"]

	_categories: bool = False

	topicStyle = (
		"color:white;"
		"background:green;"
		"padding-left:3px;"
		"padding-right:3px;"
		"border-radius:0.5ex;"
		# 0.5ex ~= 0.3em, but "ex" is recommended
	)

	def __init__(self, glos: GlossaryType) -> None:
		self._glos = glos
		self._filename = ""
		self._file: IOBase = nullBinaryIO
		self._fileSize = 0
		self._wordCount = 0

	def open(
		self,
		filename: str,
	) -> None:
		try:
			pass
		except ModuleNotFoundError as e:
			exc_note(e, f"Run `{pip} install lxml` to install")
			raise

		self._filename = filename
		cfile = compressionOpen(filename, mode="rt", encoding="utf-8")

		if cfile.seekable():
			cfile.seek(0, 2)
			self._fileSize = cfile.tell()
			cfile.seek(0)
			self._glos.setInfo("input_file_size", str(self._fileSize))
		else:
			self.warning("Wiktextract Reader: file is not seekable")

		self._glos.setDefaultDefiFormat("h")

		if self._word_title:
			self._glos.setInfo("definition_has_headwords", "True")

		self._file = cfile
		self._warnings: Counter[str] = collections.Counter()

	def close(self) -> None:
		self._file.close()
		self._file = nullBinaryIO
		self._filename = ""
		self._fileSize = 0

	def __len__(self) -> int:
		return 0

	def __iter__(self) -> Iterator[EntryType]:
		while line := self._file.readline():
			line = line.strip()
			if not line:
				continue
			yield self.makeEntry(json_loads(line))
		for _msg, count in self._warnings.most_common():
			msg = _msg
			if count > 1:
				msg = f"[{count} times] {msg}"
			log.warning(msg)

	def warning(self, msg: str) -> None:
		self._warnings[msg] += 1

	def makeEntry(self, data: dict[str, Any]) -> EntryType:  # noqa: PLR0912
		from lxml import etree as ET

		glos = self._glos
		f = BytesIO()

		def br() -> Element:
			return ET.Element("br")

		keywords: list[str] = []
		inflectedKeywords: list[str] = []

		word = data.get("word")
		if word:
			keywords.append(word)

		for formDict in data.get("forms", []):
			form: str = formDict.get("form", "")
			if not form:
				continue
			if len(form) > 80:
				self.warning(f"'form' too long: {form}")
				continue
			source: str = formDict.get("source", "")
			# tags = formDict.get("tags", [])
			if source == "Inflection":
				inflectedKeywords.append(form)
			else:
				keywords.append(form)

		keywords += inflectedKeywords

		with ET.htmlfile(f, encoding="utf-8") as hf:
			with hf.element("div"):
				if self._word_title:
					for keyword in keywords:
						with hf.element(glos.titleTag(keyword)):
							hf.write(keyword)
						hf.write(br())

				hf_ = cast("T_htmlfile", hf)

				self.writeSoundList(hf_, data.get("sounds"))

				pos: str | None = data.get("pos")
				if pos:
					with hf.element("div", attrib={"class": "pos"}):
						with hf.element("font", color=self._gram_color):
							hf.write(pos)

				senses = data.get("senses") or []

				self.writeSenseList(hf_, senses)  # type: ignore

				self.writeSynonyms(hf_, data.get("synonyms"))  # type: ignore

				self.writeAntonyms(hf_, data.get("antonyms"))  # type: ignore

				# TODO: data.get("translations")
				# list[dict[str, str]]
				# dict keys: code, "lang", "sense", "word"

				etymology: str = data.get("etymology_text", "")
				if etymology:
					hf.write(br())
					with hf.element("div"):
						hf.write(f"Etymology: {etymology}")

				if self._categories:
					categories = []
					for sense in senses:
						senseCats = sense.get("categories")
						if senseCats:
							categories += senseCats
					self.writeSenseCategories(hf_, categories)

		defi = f.getvalue().decode("utf-8")
		# defi = defi.replace("\xa0", "&nbsp;")  # do we need to do this?
		file = self._file
		return self._glos.newEntry(
			keywords,
			defi,
			defiFormat="h",
			byteProgress=(file.tell(), self._fileSize),
		)

	def writeSoundPron(
		self,
		hf: T_htmlfile,
		sound: dict[str, Any],
	) -> None:
		# "homophone" key found in Dutch and Arabic dictionaries
		# (similar-sounding words for Arabic)
		for key in ("ipa", "other", "rhymes", "homophone"):
			value = sound.get(key)
			if not value:
				continue
			with hf.element("font", color=self._pron_color):
				hf.write(str(value))
			hf.write(f" ({key})")

	def writeSoundAudio(
		self,
		hf: T_htmlfile,
		sound: dict[str, Any],
	) -> None:
		# TODO: add a read-option for audio
		# keys for audio:
		# "audio" (file name), "text" (link text), "ogg_url", "mp3_url"
		# possible "tags" (list[str])

		text = sound.get("text")
		if text:
			hf.write(f"{text}: ")
		with hf.element("audio", attrib={"controls": ""}):
			for _format in self._audio_formats:
				url = sound.get(f"{_format}_url")
				if not url:
					continue
				with hf.element(
					"source",
					attrib={
						"src": url,
						"type": f"audio/{_format}",
					},
				):
					pass

	def writeSoundList(
		self,
		hf: T_htmlfile,
		soundList: list[dict[str, Any]] | None,
	) -> None:
		if not soundList:
			return

		pronList: list[dict[str, Any]] = []
		audioList: list[dict[str, Any]] = []

		for sound in soundList:
			if "audio" in sound:
				if self._audio:
					audioList.append(sound)
				continue
			pronList.append(sound)
			# can it contain both audio and pronunciation?

		if pronList:
			with hf.element("div", attrib={"class": "pronunciations"}):
				for i, sound in enumerate(pronList):
					if i > 0:
						hf.write(", ")
					self.writeSoundPron(hf, sound)

		for sound in audioList:
			with hf.element("div", attrib={"class": "audio"}):
				self.writeSoundAudio(hf, sound)

	def writeSenseList(
		self,
		hf: T_htmlfile,
		senseList: list[dict[str, Any]],
	) -> None:
		if not senseList:
			return

		self.makeList(
			hf,
			senseList,
			self.writeSense,
		)

	def writeSenseGloss(  # noqa: PLR6301
		self,
		hf: T_htmlfile,
		text: str | None,
	) -> None:
		hf.write(text or "")

	def writeSenseCategory(  # noqa: PLR6301
		self,
		hf: T_htmlfile,
		category: dict[str, Any],
	) -> None:
		# keys: name: str, kind: str, parents: list, source: str
		# values for "source" (that I found): "w", "w+disamb"
		name = category.get("name")
		if not name:
			self.warning(f"{category = }")
			return
		desc = name
		source = category.get("source")
		if source:
			desc = f"{desc} (source: {source})"
		hf.write(desc)

	def writeSenseCategories(
		self,
		hf: T_htmlfile,
		categories: list[dict[str, Any]] | None,
	) -> None:
		if not categories:
			return
		# long names, mostly about grammar?
		with hf.element("div", attrib={"class": "categories"}):
			hf.write("Categories: ")
			self.makeList(hf, categories, self.writeSenseCategory)

	def writeSenseExample(  # noqa: PLR6301, PLR0912
		self,
		hf: T_htmlfile,
		example: dict[str, str | list],
	) -> None:
		# example keys: text, "english", "ref", "type"
		textList: list[tuple[str | None, str]] = []
		text_: str | list = example.pop("example", "")
		if text_:
			assert isinstance(text_, str)
			textList.append((None, text_))

		example.pop("ref", "")
		example.pop("type", "")

		for key, value in example.items():
			if not value:
				continue
			prefix: str | None = key
			if prefix in ("text",):  # noqa: PLR6201, FURB171
				prefix = None
			if isinstance(value, str):
				textList.append((prefix, value))
			elif isinstance(value, list):
				for item in value:
					if isinstance(item, str):
						textList.append((prefix, item))
					elif isinstance(item, list):
						textList += [(prefix, item2) for item2 in item]
			else:
				log.error(f"writeSenseExample: invalid type for {value=}")

		if not textList:
			return

		def writePair(prefix: str | None, text: str) -> None:
			if prefix:
				with hf.element("b"):
					hf.write(prefix)
				hf.write(": ")
			hf.write(text)

		if len(textList) == 1:
			prefix, text = textList[0]
			writePair(prefix, text)
			return

		with hf.element("ul"):
			for prefix, text in textList:
				with hf.element("li"):
					writePair(prefix, text)

	def writeSenseExamples(
		self,
		hf: T_htmlfile,
		examples: list[dict[str, str | list]] | None,
	) -> None:
		from lxml import etree as ET

		if not examples:
			return
		hf.write(ET.Element("br"))
		with hf.element("div", attrib={"class": "examples"}):
			hf.write("Examples:")
			hf.write(ET.Element("br"))
			for example in examples:
				with hf.element(
					"div",
					attrib={
						"class": "example",
						"style": f"padding: {self._example_padding};",
					},
				):
					self.writeSenseExample(hf, example)

	def writeSenseFormOf(  # noqa: PLR6301
		self,
		hf: T_htmlfile,
		form_of: dict[str, str],
	) -> None:
		from lxml import etree as ET

		# {"word": ..., "extra": ...}
		word = form_of.get("word")
		if not word:
			return
		hf.write(word)
		extra = form_of.get("extra")
		if extra:
			hf.write(ET.Element("br"))
			hf.write(extra)

	def writeSenseFormOfList(
		self,
		hf: T_htmlfile,
		form_of_list: list[dict[str, str]] | None,
	) -> None:
		if not form_of_list:
			return
		with hf.element("div", attrib={"class": "form_of"}):
			hf.write("Form of: ")
			self.makeList(hf, form_of_list, self.writeSenseFormOf)

	def writeTags(
		self,
		hf: T_htmlfile,
		tags: list[str] | None,
		toRemove: list[str] | None,
	) -> None:
		if not tags:
			return

		if toRemove:
			for tag in toRemove:
				if tag in tags:
					tags.remove(tag)
		if not tags:
			return

		with hf.element("div", attrib={"class": "tags"}):
			for i, tag in enumerate(tags):
				if i > 0:
					hf.write(", ")
				with hf.element("font", color=self._gram_color):
					hf.write(tag)

	def writeTopics(
		self,
		hf: T_htmlfile,
		topics: list[str] | None,
	) -> None:
		if not topics:
			return

		with hf.element("div", attrib={"class": "tags"}):
			for i, topic in enumerate(topics):
				if i > 0:
					hf.write(" ")
				with hf.element("span", style=self.topicStyle):
					hf.write(topic)

	def addWordLink(  # noqa: PLR6301
		self,
		hf: T_htmlfile,
		word: str,
		wordClass: str = "",
	) -> None:
		i = word.find(" [")
		if i >= 0:
			word = word[:i]
		if not word:
			return
		attrib = {"href": f"bword://{word}"}
		if wordClass:
			attrib["class"] = wordClass
		with hf.element(
			"a",
			attrib=attrib,
		):
			hf.write(word)

	def writeSynonyms(
		self,
		hf: T_htmlfile,
		synonyms: list[dict[str, Any]] | None,
	) -> None:
		if not synonyms:
			return

		#   "word": "str",
		#   "sense": "str",
		#   "_dis1": "str",
		#   "tags": list[str]
		#   "extra": "str",
		#   "english": "str"

		with hf.element("div"):
			hf.write("Synonyms: ")
			for i, item in enumerate(synonyms):
				if i > 0:
					hf.write(", ")
				word = item.get("word")
				if not word:
					continue
				self.addWordLink(hf, word)

	def writeAntonyms(
		self,
		hf: T_htmlfile,
		antonyms: list[dict[str, str]] | None,
	) -> None:
		if not antonyms:
			return
		# dict keys: word
		with hf.element("div"):
			hf.write("Antonyms: ")
			for i, item in enumerate(antonyms):
				if i > 0:
					hf.write(", ")
				word = item.get("word")
				if not word:
					continue
				self.addWordLink(hf, word, wordClass="antonym")

	def writeRelated(
		self,
		hf: T_htmlfile,
		relatedList: list[dict[str, str]] | None,
	) -> None:
		if not relatedList:
			return
		# dict keys: sense, "word", "english"
		with hf.element("div"):
			hf.write("Related: ")
			for i, item in enumerate(relatedList):
				if i > 0:
					hf.write(", ")
				word = item.get("word")
				if not word:
					continue
				self.addWordLink(hf, word)

	def writeSenseLinks(
		self,
		hf: T_htmlfile,
		linkList: list[list[str]] | None,
	) -> None:
		if not linkList:
			return
		with hf.element("div"):
			hf.write("Links: ")
			for i, link in enumerate(linkList):
				if len(link) != 2:
					self.warning(f"unexpected {link =}")
					continue
				text, ref = link
				sq = ref.find("#")
				if sq == 0:
					ref = text
				elif sq > 0:
					ref = ref[:sq]
				if i > 0:
					hf.write(", ")
				self.addWordLink(hf, ref)

	def writeSense(
		self,
		hf: T_htmlfile,
		sense: dict[str, Any],
	) -> None:
		from lxml import etree as ET

		# tags seem to be mostly about grammar, so with format it like grammar
		self.writeTags(
			hf,
			sense.get("tags"),
			toRemove=["form-of"],
		)

		# for key in ("english",):
		# 	text: "str | None" = sense.get("english")
		# 	if not text:
		# 		continue
		# 	keyCap = key.capitalize()
		# 	with hf.element("div"):
		# 		with hf.element("b"):
		# 			hf.write(keyCap)
		# 		hf.write(f": {text}")

		# sense["glosses"] and sense["english"] seems to be unreliable
		# for example:
		#   "raw_glosses": ["(short) story, fable, play"],
		#   "english": "short",
		#   "glosses": ["story, fable, play"],

		glosses: list[str] | None = sense.get("raw_glosses")
		if not glosses:
			glosses = sense.get("glosses")
		if glosses:
			self.makeList(hf, glosses, self.writeSenseGloss)

		self.writeTopics(hf, sense.get("topics"))

		self.writeSenseFormOfList(hf, sense.get("form_of"))

		self.writeSynonyms(hf, sense.get("synonyms"))

		self.writeAntonyms(hf, sense.get("antonyms"))

		self.writeRelated(hf, sense.get("related"))

		self.writeSenseLinks(hf, sense.get("links"))

		self.writeSenseExamples(hf, sense.get("examples"))

		# alt_of[i]["word"] seem to point to a word that is
		# mentioned in sense["raw_glosses"]
		# so we could try to find that word and turn it into a link
		# sense.get("alt_of"): list[dict[str, str]] | None

		# sense.get("wikipedia", []): list[str]
		# sense.get("wikidata", []): list[str]
		# sense.get("id", ""): str  # not useful
		# sense.get("senseid", []): list[str]  # not useful

		hf.write(ET.Element("br"))

	@staticmethod
	def makeList(  # noqa: PLR0913
		hf: T_htmlfile,
		input_objects: list[Any],
		processor: Callable,
		ordered: bool = True,
		skip_single: bool = True,
		# single_prefix: str = "",
		# list_type: str = "",
	) -> None:
		"""Wrap elements into <ol> if more than one element."""
		if not input_objects:
			return

		if skip_single and len(input_objects) == 1:
			# if single_prefix:
			# 	hf.write(single_prefix)
			processor(hf, input_objects[0])
			return

		attrib: dict[str, str] = {}
		# if list_type:
		# 	attrib["type"] = list_type

		with hf.element("ol" if ordered else "ul", attrib=attrib):
			for el in input_objects:
				with hf.element("li"):
					processor(hf, el)
