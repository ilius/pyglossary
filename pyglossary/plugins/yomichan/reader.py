"""
Read Yomichan browser-extension term bank ZIP packages.

Unpacks ``.zip`` archives of JSON term banks and reconstructs glossary entries
with readings, tags, and structured definitions. Merges split term-bank files
according to Yomichan sorting and indexing conventions.
"""

from __future__ import annotations

# mypy: ignore-errors
import re
from operator import itemgetter
from typing import TYPE_CHECKING, Any
from zipfile import ZipFile

from pyglossary.core import log
from pyglossary.utils.json_utils import jsonToData

if TYPE_CHECKING:
	from collections.abc import Generator, Iterator
	from zipfile import ZipInfo

	from pyglossary.stubs.glossary_types import EntryType, ReaderGlossaryType

	from ._types import (
		DefinitionObj,
		StructuredContent,
		YomichanDefinition,
	)

__all__ = ["Reader", "_readSubStructuredContent"]

FIELDS_TO_WRITE = ["title", "author", "description", "sourceLanguage", "targetLanguage"]
TERM_BASE_PATTERN = re.compile(r"term_bank_(\d+).json\Z")
TERM_META_BASE_PATTERN = re.compile(r"term_meta_bank_(\d+).json\Z")
BASE_BANK_PATTERN = re.compile(r".+_(meta_)?bank_(\d+).json\Z")


class Reader:
	"""Read Yomichan glossary files."""

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
		self._termMetaBankFiles = []
		self._resourceFiles = []

	def open(self, filename: str) -> None:
		# TODO: Sanitize name
		self._filename = filename
		self._dictFile = ZipFile(filename)
		resourceFiles = []
		termFiles: list[tuple[int, ZipInfo]] = []
		termMetaFiles: list[tuple[int, ZipInfo]] = []
		for file in self._dictFile.filelist:
			match = TERM_BASE_PATTERN.match(file.filename)
			if match is not None:
				termFiles.append((int(match.group(1)), file))
				continue
			match = TERM_META_BASE_PATTERN.match(file.filename)
			if match is not None:
				termMetaFiles.append((int(match.group(1)), file))
				continue
			if file.filename == "index.json" or file.is_dir():
				continue
			# As currently there is no support for them
			if BASE_BANK_PATTERN.match(file.filename):
				continue
			resourceFiles.append(file)
		self._termBankFiles = [val for _, val in sorted(termFiles, key=itemgetter(0))]
		self._termMetaBankFiles = [
			val for _, val in sorted(termMetaFiles, key=itemgetter(0))
		]
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
		return len(self._termBankFiles) + len(self._termMetaBankFiles)

	def countResourceFiles(self) -> int:
		return len(self._resourceFiles)

	def __iter__(self) -> Iterator[EntryType]:
		if self._dictFile is None:
			raise RuntimeError("Yomichan: resources were read while reader is not open")
		termMeta = self._readTermMetaBanks()
		usedTermMeta: set[tuple[str, str]] = set()
		yield from self._readTermBanks(termMeta, usedTermMeta)
		yield from self._readTermMetaEntries(termMeta, usedTermMeta)
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

	def _readTermBanks(
		self,
		termMeta: dict[tuple[str, str], list[str]],
		usedTermMeta: set[tuple[str, str]],
	) -> Generator[EntryType, None, None]:
		termToAlts = self._readTermBanksAlts()
		orphanedTerms = set(termToAlts)
		log.info("Finished extracting alts")
		for termBankFile in self._termBankFiles:
			yield from self._readTermBank(
				termBankFile.filename, termToAlts, orphanedTerms, termMeta, usedTermMeta
			)
		for term in orphanedTerms:
			# SAFETY: orphanedTerms is made from keys of termToAlts
			altInfo = termToAlts[term]
			for alt, causalChain in altInfo:
				yield self._glos.newEntry(
					alt, " « ".join(causalChain) + f" ««« {term}", defiFormat="m"
				)

	def _readTermMetaBanks(self) -> dict[tuple[str, str], list[str]]:
		"""Read term metadata (pitch accent, frequency, IPA) from meta banks."""
		if self._dictFile is None:
			raise RuntimeError("Yomichan: resources were read while reader is not open")
		termMeta: dict[tuple[str, str], list[str]] = {}
		for termMetaBankFile in self._termMetaBankFiles:
			with self._dictFile.open(termMetaBankFile.filename) as tf:
				termMetaBank = jsonToData(tf.read())
			for item in termMetaBank:
				parsed = _readTermMeta(item)
				if parsed is None:
					continue
				term, reading, definition = parsed
				key = (term, reading or term)
				termMeta.setdefault(key, []).append(definition)
		return termMeta

	def _readTermMetaEntries(
		self,
		termMeta: dict[tuple[str, str], list[str]],
		usedTermMeta: set[tuple[str, str]],
	) -> Generator[EntryType, None, None]:
		"""Yield metadata-only entries that have no matching term bank entry."""
		for (term, reading), definitions in termMeta.items():
			if (term, reading) in usedTermMeta:
				continue
			terms = [term]
			if reading and reading != term:
				terms.append(reading)
			yield self._glos.newEntry(
				terms,
				"\n".join(definitions),
				defiFormat="m",
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
		termMeta: dict[tuple[str, str], list[str]],
		usedTermMeta: set[tuple[str, str]],
	) -> Generator[EntryType, None, None]:
		if self._dictFile is None:
			raise RuntimeError("Yomichan: resources were read while reader is not open")
		with self._dictFile.open(termBankName) as termBankFile:
			termBank = jsonToData(termBankFile.read())
		for item in termBank:
			headword: str = item[0]
			terms: list[str] = [headword]
			reading: str = item[1]
			if reading:
				terms.append(reading)
			if _isDeinflection(item[5]):
				continue  # ignore alts, we already extracted them
			definition = _readDefinition(item[5])
			metaKey = (headword, reading or headword)
			if metaDefinitions := termMeta.get(metaKey):
				usedTermMeta.add(metaKey)
				definition = "\n".join([definition, *metaDefinitions])
			if altInfo := termToAlts.get(headword):
				orphanedTerms.discard(headword)
				terms.extend(elt[0] for elt in altInfo)
			yield self._glos.newEntry(terms, definition, defiFormat="h")

	def _readUsedResources(self) -> Generator[EntryType, None, None]:
		if self._dictFile is None:
			raise RuntimeError("Yomichan: resources were read while reader is not open")
		for file in self._resourceFiles:
			with self._dictFile.open(file.filename) as rawFile:
				data = rawFile.read()
			yield self._glos.newDataEntry(file.filename, data)


def _asList(value: Any) -> list[Any]:  # noqa: ANN401
	if value is None:
		return []
	if isinstance(value, list):
		return value
	return [value]


def _formatFrequency(value: Any) -> str:  # noqa: ANN401
	if isinstance(value, dict):
		if "displayValue" in value:
			return str(value["displayValue"])
		if "value" in value:
			return str(value["value"])
		return ""
	return str(value)


def _formatMetaTags(tags: Any) -> str:  # noqa: ANN401
	tags = _asList(tags)
	if not tags:
		return ""
	return f"; tags: {', '.join(map(str, tags))}"


def _readTermMetaFrequency(term: str, data: Any) -> tuple[str, str, str] | None:  # noqa: ANN401
	if isinstance(data, dict) and "frequency" in data:
		reading = str(data.get("reading", ""))
		frequency = _formatFrequency(data["frequency"])
	else:
		reading = ""
		frequency = _formatFrequency(data)
	if not frequency:
		return None
	return term, reading, f"frequency: {frequency}"


def _readTermMetaPitch(data: dict[str, Any]) -> str | None:
	lines = []
	for pitch in _asList(data.get("pitches")):
		if not isinstance(pitch, dict):
			continue
		parts = [f"pitch: {pitch.get('position', '')}"]
		for field in ("devoice", "nasal"):
			values = _asList(pitch.get(field))
			if values:
				parts.append(f"{field}: {', '.join(map(str, values))}")
		line = "; ".join(parts) + _formatMetaTags(pitch.get("tags"))
		lines.append(line)
	return "\n".join(lines) or None


def _readTermMetaIpa(data: dict[str, Any]) -> str | None:
	lines = []
	for transcription in _asList(data.get("transcriptions")):
		if not isinstance(transcription, dict):
			continue
		line = f"ipa: {transcription.get('ipa', '')}"
		line += _formatMetaTags(transcription.get("tags"))
		lines.append(line)
	return "\n".join(lines) or None


def _readTermMeta(
	item: Any,  # noqa: ANN401
) -> tuple[str, str, str] | None:
	"""Parse a term_meta_bank item into ``(term, reading, definition)``."""
	if not isinstance(item, list) or len(item) != 3:
		return None
	term, mode, data = item
	if not isinstance(term, str) or not isinstance(mode, str):
		return None
	if mode in ("freq", "frequency"):
		return _readTermMetaFrequency(term, data)
	if not isinstance(data, dict):
		return None
	if mode == "pitch":
		definition = _readTermMetaPitch(data)
	elif mode == "ipa":
		definition = _readTermMetaIpa(data)
	else:
		return None
	if definition is None:
		return None
	return term, str(data.get("reading", "")), definition


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
		return "".join(map(_readSubStructuredContent, elem))
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
