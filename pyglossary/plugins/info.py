# -*- coding: utf-8 -*-

from formats_common import *

enable = True
format = "Info"
description = "Glossary Info (.info)"
extensions = (".info",)
singleFile = True

# key is option/argument name, value is instance of Option
optionsProp = {}

depends = {}

class Writer(object):
	def __init__(self, glos: GlossaryType):
		self._glos = glos

	def write(self, filename: str) -> Generator[None, "BaseEntry", None]:
		import re
		from collections import Counter, OrderedDict
		from pyglossary.json_utils import dataToPrettyJson

		glos = self._glos
		re_possible_html = re.compile(r"<[a-zA-Z]+[ />]")

		defiFormatCounter = Counter()
		firstTagCounter = Counter()
		allTagsCounter = Counter()
		wordCount = 0
		while True:
			entry = yield
			if entry is None:
				break
			entry.detectDefiFormat()
			defiFormat = entry.defiFormat
			wordCount += 1
			defiFormatCounter[defiFormat] += 1
			defi = entry.defi
			if defiFormat == "m":
				if re_possible_html.match(defi):
					log.warn(f"undetected html defi: {defi}")
			elif defiFormat == "h":
				tag = re_possible_html.search(defi).group().strip("< />").lower()
				firstTagCounter[tag] += 1
				for tag in re_possible_html.findall(defi):
					tag = tag.strip("< />").lower()
					allTagsCounter[tag] += 1

		data_entry_count = defiFormatCounter["b"]
		del defiFormatCounter["b"]
		info = OrderedDict()
		for key, value in glos.iterInfo():
			info[key] = value
		info["word_count"] = wordCount
		info["data_entry_count"] = data_entry_count
		info["defi_format_counter"] = ", ".join(
			f"{defiFormat}={count}"
			for defiFormat, count in
			sorted(defiFormatCounter.items())
		)
		info["defi_tag_counter"] = ", ".join(
			f"{defiFormat}={count}"
			for defiFormat, count in
			allTagsCounter.most_common()
		)
		info["defi_first_tag_counter"] = ", ".join(
			f"{defiFormat}={count}"
			for defiFormat, count in
			firstTagCounter.most_common()
		)
		with open(filename, mode="w", encoding="utf-8") as _file:
			_file.write(dataToPrettyJson(info))

