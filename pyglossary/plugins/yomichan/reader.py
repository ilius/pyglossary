# -*- coding: utf-8 -*-
from __future__ import annotations

# mypy: ignore-errors
import re
from operator import itemgetter
from typing import TYPE_CHECKING
from zipfile import ZipFile

from pyglossary.core import log
from pyglossary.json_utils import jsonToData

if TYPE_CHECKING:
	from collections.abc import Generator, Iterator
	from zipfile import ZipInfo

	from pyglossary.glossary_types import EntryType, MultiStr, ReaderGlossaryType

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
		self._readIndex()

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
		yield from self._readTermBanks()
		yield from self._readUsedResources()

	def _readIndex(self) -> None:
		if self._dictFile is None:
			raise RuntimeError("Yomichan: resources were read while reader is not open")
		with self._dictFile.open("index.json") as indexFile:
			index = jsonToData(indexFile.read())
		if not isinstance(index, dict):
			raise TypeError("Yomichan: ill-formed yomichan dictionary")
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

	def _readTermBanks(self) -> Generator[EntryType, None, None]:
		termToAlts = self._readTermBanksAlts()
		orphanedTerms = set(termToAlts)
		log.info("Finished extracting alts")
		for termBankFile in self._termBankFiles:
			yield from self._readTermBank(
				termBankFile.filename, termToAlts, orphanedTerms
			)
		for term in orphanedTerms:
			# SAFETY: orphanedTerms is made from keys of termToAlts
			altInfo = termToAlts[term]
			for alt, causalChain in altInfo:
				yield self._glos.newEntry(
					alt, " « ".join(causalChain) + f" ««« {term}", defiFormat="m"
				)

	def _readTermBanksAlts(self) -> dict[str, list[tuple[str, list[str]]]]:
		"""
		Read all TermBanks to extract alts.

		We will do the same that Yomitan does, which is to redirect to every lemma.
		For instance, if we hover curas in Yomitan, we will see "curar" (verb) and "cura"
		(noun). In the same vein, we will add this alt to curar and cura: "curar|curas",
		"cura|curas". And this, even if curar had multiple readings (it doesn't, just bear
		with me, for the sake of the example): "curar|read1|curas", "curar|read2|curas".
		"""
		termToAlts: dict[str, list[tuple[str, list[str]]]] = {}
		for termBankFile in self._termBankFiles:
			if self._dictFile is None:
				raise RuntimeError(
					"Yomichan: resources were read while reader is not open"
				)
			with self._dictFile.open(termBankFile.filename) as tf:
				termBank = jsonToData(tf.read())
			# {form_of => [(lemma, [causal chain])]}
			for item in termBank:
				alt = item[0]
				if _isDeinflection(item[5]):
					for term, causalChain in item[5]:
						termToAlts.setdefault(term, []).append((alt, causalChain))
		return termToAlts

	def _readTermBank(
		self,
		termBankName: str,
		termToAlts: dict[str, list[tuple[str, list[str]]]],
		orphanedTerms: set[str],
	) -> Generator[EntryType, None, None]:
		if self._dictFile is None:
			raise RuntimeError("Yomichan: resources were read while reader is not open")
		with self._dictFile.open(termBankName) as termBankFile:
			termBank = jsonToData(termBankFile.read())
		for item in termBank:
			term: str = item[0]
			reading: str = item[1]
			terms: MultiStr = term
			if reading:
				terms = [terms, reading]
			if _isDeinflection(item[5]):
				continue  # ignore alts, we already extracted them
			definition = _readDefinition(item[5])
			if altInfo := termToAlts.get(item[0]):
				orphanedTerms.discard(item[0])
				alts = [elt[0] for elt in altInfo]
				terms = [terms, *alts] if isinstance(terms, str) else [*terms, *alts]
			yield self._glos.newEntry(terms, definition, defiFormat="h")

	def _readUsedResources(self) -> Generator[EntryType, None, None]:
		if self._dictFile is None:
			raise RuntimeError("Yomichan: resources were read while reader is not open")
		for file in self._resourceFiles:
			with self._dictFile.open(file.filename) as rawFile:
				data = rawFile.read()
			yield self._glos.newDataEntry(file.filename, data)


def _isDeinflection(item) -> bool:  # noqa: ANN001
	return isinstance(item, list) and all(
		isinstance(e, list)
		and len(e) == 2
		and isinstance(e[0], str)
		and isinstance(e[1], list)
		for e in item
	)


def _readSubStructuredContent(elem: StructuredContent) -> str:
	if isinstance(elem, str):
		return elem
	if isinstance(elem, list):
		return " ".join(map(_readSubStructuredContent, elem))
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
	content = _readSubStructuredContent(elem.get("content", ""))
	additional_properties.append(f' style="{"".join(styles)}"')
	additional_properties = "".join(additional_properties)
	return f"<{tag}{additional_properties}>{content}</{tag}>"


def _readStructuredContent(elem: DefinitionObj) -> str:
	if elem["type"] == "text":
		return elem["text"]
	if elem["type"] == "structured-content":
		return _readSubStructuredContent(elem["content"])
	if elem["type"] == "image":
		properties = []
		for name in ["alt", "width", "height", "title"]:
			prop = elem.get(name)
			if prop is not None:
				properties.append(f' {name}="{prop}"')
		return f'<img src="{elem["path"]}"{"".join(properties)}>'
	raise RuntimeError("Ill-formed Yomichan dictionary")


def _readDefinition(definition: list[YomichanDefinition]) -> str:
	def _ParseDefinition(defi: YomichanDefinition) -> str:
		if isinstance(defi, str):
			return defi
		if isinstance(defi, dict):
			return _readStructuredContent(defi)
		raise NotImplementedError(f"Yomichan: unknown elem in definition: {defi}")

	return "\n".join(map(_ParseDefinition, definition))
