# -*- coding: utf-8 -*-

from formats_common import *

enable = True
format = "Info"
description = "Glossary Info (.info)"
extensions = [".info"]

# key is option/argument name, value is instance of Option
optionsProp = {}

depends = {}

def write(glos: GlossaryType, filename: str) -> bool:
	from collections import Counter, OrderedDict
	from pyglossary.json_utils import dataToPrettyJson
	from pprint import pformat
	defiFormatCounter = Counter()
	for entry in glos:
		entry.detectDefiFormat()
		defiFormat = entry.getDefiFormat()
		defiFormatCounter[defiFormat] += 1
	data_entry_count = defiFormatCounter["b"]
	del defiFormatCounter["b"]
	info = OrderedDict()
	for key, value in glos.iterInfo():
		info[key] = value
	info["data_entry_count"] = data_entry_count
	info["defi_format_counter"] = ", ".join(
		f"{defiFormat}={count}"
		for defiFormat, count in
		defiFormatCounter.most_common()
	)
	log.info(pformat(info))
	with open(filename, mode="w", encoding="utf-8") as _file:
		_file.write(dataToPrettyJson(info))

