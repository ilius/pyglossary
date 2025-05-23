# -*- coding: utf-8 -*-
from __future__ import annotations

import re
from operator import itemgetter
from typing import TYPE_CHECKING
from zipfile import ZipFile, ZipInfo

from pyglossary.json_utils import jsonToData

if TYPE_CHECKING:
	from collections.abc import Generator, Iterator

	from pyglossary.glossary_types import EntryType, ReaderGlossaryType

	from .types import (
		DefinitionObj,
		StructuredContent,
		YomichanDefinition,
	)

__all__ = ["Reader"]

FIELDS_TO_WRITE = ["title", "author", "description", "sourceLanguage", "targetLanguage"]
TERM_BASE_PATTERN = re.compile(r"term_bank_(\d+).json\Z")
BASE_BANK_PATTERN = re.compile(r".+_(meta_)?bank_(\d+).json\Z")


class Reader:
	useByteProgress = False
	compressions = ["zip"]

	def __init__(self, glos: ReaderGlossaryType) -> None:
		self._glos = glos
		self.clear()

	def clear(self) -> None:
		self._dictFile: ZipFile | None = None
		self._filename = ""
		self._isSequenced = False
		self._termBankFiles = []
		self._resourceFiles = []

	def open(self, filename: str) -> None:
		# TODO: Sanitize name
		self._filename = filename
		self._dictFile = ZipFile(filename)
		resourceFiles = []
		termFiles: list[tuple[int, ZipInfo]] = []
		for file in self._dictFile.filelist:
			match = TERM_BASE_PATTERN.match(file.filename)
			if match is not None:
				termFiles.append((int(match.group(1)), file))
				continue
			if file.filename == "index.json" or file.is_dir():
				continue
			# As currently there is no support for them
			if BASE_BANK_PATTERN.match(file.filename):
				continue
			resourceFiles.append(file)
		self._termBankFiles = [val for _, val in sorted(termFiles, key=itemgetter(0))]
		self._resourceFiles = resourceFiles
		self._ReadIndex()

	def close(self) -> None:
		if self._dictFile:
			self._dictFile.close()
		self.clear()

	def __len__(self) -> int:
		if self._dictFile is None:
			raise RuntimeError("Yomichan: len(reader) called while reader is not open")
		# TODO: how do I count real length??
		return len(self._termBankFiles)

	def __iter__(self) -> Iterator[EntryType]:
		if self._dictFile is None:
			raise RuntimeError("Yomichan: resources were read while reader is not open")
		for termBankFile in self._termBankFiles:
			yield from self._ReadTermBank(termBankFile.filename)
		yield from self._ReadUsedResources()

	def _ReadIndex(self) -> None:
		if self._dictFile is None:
			raise RuntimeError("Yomichan: resources were read while reader is not open")
		with self._dictFile.open("index.json") as indexFile:
			index = jsonToData(indexFile.read())
		if not isinstance(index, dict):
			raise RuntimeError("Yomichan: ill-formed yomichan dictionary")
		if index["format"] != 3:
			raise NotImplementedError(
				"Yomichan: supported only dictionaries of 3 version",
			)
		self._glos.setInfo("sourceLang", "ja")
		for c_field in FIELDS_TO_WRITE:
			value = index.get(c_field)
			if value is not None:
				self._glos.setInfo(c_field, value)
		self._isSequenced = index.get("isSequenced", False)

	def _ReadTermBank(self, termBankName: str) -> Generator[EntryType, None, None]:
		if self._dictFile is None:
			raise RuntimeError("Yomichan: resources were read while reader is not open")
		with self._dictFile.open(termBankName) as termBankFile:
			termBank = jsonToData(termBankFile.read())
		for term in termBank:
			word = term[0]
			if reading := term[1]:
				word = [word, reading]
			definition = _ReadDefinition(term[5])
			yield self._glos.newEntry(word, definition, defiFormat="h")

	def _ReadUsedResources(self) -> Generator[EntryType, None, None]:
		if self._dictFile is None:
			raise RuntimeError("Yomichan: resources were read while reader is not open")
		for file in self._resourceFiles:
			with self._dictFile.open(file.filename) as rawFile:
				data = rawFile.read()
			yield self._glos.newDataEntry(file.filename, data)


def _ReadSubStructuredContent(elem: StructuredContent) -> str:
	if isinstance(elem, str):
		return elem
	if isinstance(elem, list):
		return " ".join(map(_ReadSubStructuredContent, elem))
	styles = []
	additional_properties = [
		f' {key}="{val}"' for key, val in elem.get("data", {}).items()
	]
	if "style" in elem:
		styles = [f"{k}: {v};" for k, v in elem["style"].items()]
	for field in ("lang", "title", "alt", "href", "colSpan", "rowSpan"):
		if field not in elem:
			continue
		additional_properties.append(f' {field}="{elem.get(field)}"')

	# Tag processing
	# TODO: Process all tags?
	if elem["tag"] == "br":
		return f"<br{''.join(additional_properties)}>"
	if elem["tag"] == "img":
		for name in ("width", "height"):
			if name not in elem:
				continue
			if elem.get("sizeUnits", "px") == "em":
				styles.append(f"{name}: {elem.get(name)}em;")
			else:
				additional_properties.append(f" {name}={elem.get(name)}")
		if "verticalAlign" in elem:
			styles.append(f"vertical-align: {elem['verticalAlign']};")
		additional_properties.append(f' style="{"".join(styles)}"')
		additional_properties = "".join(additional_properties)
		return f'<img src="{elem["path"]}"{additional_properties}>'
	# General tags
	tag = elem["tag"]
	content = _ReadSubStructuredContent(elem.get("content", ""))
	additional_properties.append(f' style="{"".join(styles)}"')
	additional_properties = "".join(additional_properties)
	return f"<{tag}{additional_properties}>{content}</{tag}>"


def _ReadStructuredContent(elem: DefinitionObj) -> str:
	if elem["type"] == "text":
		return elem["text"]
	if elem["type"] == "structured-content":
		return _ReadSubStructuredContent(elem["content"])
	if elem["type"] == "image":
		properties = []
		for name in ["alt", "width", "height", "title"]:
			prop = elem.get(name)
			if prop is not None:
				properties.append(f' {name}="{prop}"')
		return f'<img src="{elem["path"]}"{"".join(properties)}>'
	raise RuntimeError("Ill-formed Yomichan dictionary")


def _ReadDefinition(definition: list[YomichanDefinition]) -> str:
	def _ParseDefinition(defi: YomichanDefinition) -> str:
		if isinstance(defi, str):
			return defi
		if isinstance(defi, dict):
			return _ReadStructuredContent(defi)
		raise NotImplementedError(f"Yomichan: unknown elem in definition: {defi}")

	return "\n".join(map(_ParseDefinition, definition))
