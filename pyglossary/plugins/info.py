# -*- coding: utf-8 -*-

from formats_common import *

enable = True
format = "Info"
description = "Glossary Info (.info)"
extensions = (".info",)
singleFile = True

# key is option/argument name, value is instance of Option
optionsProp = {}


class Writer(object):
	def __init__(self, glos: GlossaryType):
		self._glos = glos
		self._filename = None
		self._file = None

	def open(self, filename: str):
		self._filename = filename
		self._file = open(filename, mode="wt", encoding="utf-8")

	def finish(self):
		self._filename = None
		if self._file:
			self._file.close()
			self._file = None

	def write(self) -> "Generator[None, BaseEntry, None]":
		import re
		from collections import Counter, OrderedDict
		from pyglossary.json_utils import dataToPrettyJson
		from pyglossary.langs.writing_system import getWritingSystemFromText

		glos = self._glos

		re_possible_html = re.compile(
			r"<[a-z1-6]+[ />]",
			re.I,
		)
		re_style = re.compile(
			r"<([a-z1-6]+)[^<>]* style=",
			re.I | re.DOTALL,
		)

		wordCount = 0
		bwordCount = 0

		styleByTagCounter = Counter()

		defiFormatCounter = Counter()
		firstTagCounter = Counter()
		allTagsCounter = Counter()
		sourceScriptCounter = Counter()

		while True:
			entry = yield
			if entry is None:
				break
			defi = entry.defi

			wordCount += 1
			bwordCount += defi.count("bword://")

			for m in re_style.finditer(defi):
				tag = m.group(1)
				styleByTagCounter[tag] += 1

			entry.detectDefiFormat()
			defiFormat = entry.defiFormat
			defiFormatCounter[defiFormat] += 1
			if defiFormat == "m":
				if re_possible_html.match(defi):
					log.warn(f"undetected html defi: {defi}")
			elif defiFormat == "h":
				match = re_possible_html.search(defi)
				if match is not None:
					tag = match.group().strip("< />").lower()
					firstTagCounter[tag] += 1
					for tag in re_possible_html.findall(defi):
						tag = tag.strip("< />").lower()
						allTagsCounter[tag] += 1

			ws = getWritingSystemFromText(entry.s_word)
			if ws:
				wsName = ws.name
			else:
				log.debug(f"No script detected for word: {entry.s_word}")
				wsName = "None"
			sourceScriptCounter[wsName] += 1

		data_entry_count = defiFormatCounter["b"]
		del defiFormatCounter["b"]
		info = OrderedDict()
		for key, value in glos.iterInfo():
			info[key] = value
		info["word_count"] = wordCount
		info["bword_count"] = bwordCount
		info["data_entry_count"] = data_entry_count
		info["defi_format"] = ", ".join(
			f"{defiFormat}={count}"
			for defiFormat, count in
			sorted(defiFormatCounter.items())
		)
		info["defi_tag"] = ", ".join(
			f"{defiFormat}={count}"
			for defiFormat, count in
			allTagsCounter.most_common()
		)
		info["defi_first_tag"] = ", ".join(
			f"{defiFormat}={count}"
			for defiFormat, count in
			firstTagCounter.most_common()
		)
		info["style"] = ", ".join(
			f"{defiFormat}={count}"
			for defiFormat, count in
			styleByTagCounter.most_common()
		)
		info["source_script"] = ", ".join(
			f"{defiFormat}={count}"
			for defiFormat, count in
			sourceScriptCounter.most_common()
		)
		self._file.write(dataToPrettyJson(info) + "\n")


class Reader(object):
	def __init__(self, glos: GlossaryType):
		self._glos = glos

	def close(self) -> None:
		pass

	def open(self, filename: str) -> None:
		from pyglossary.json_utils import jsonToOrderedData

		with open(filename, "r", encoding="utf-8") as infoFp:
			info = jsonToOrderedData(infoFp.read())
		for key, value in info.items():
			self._glos.setInfo(key, value)

	def __len__(self) -> int:
		return 0

	def __iter__(self) -> "Iterator[BaseEntry]":
		yield None
