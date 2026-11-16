"""
Write QuickDic version 6 ``.quickdic`` archives.

Builds QuickDic v6 ZIP bundles with binary indexes and compressed definition
stores. Applies QuickDic collation and packages resources expected by Android
QuickDic v6 clients.
"""

from __future__ import annotations

import datetime as dt
import os
from typing import TYPE_CHECKING

from pyglossary.core import log

from .quickdic import QuickDic
from .write_funcs import (
	write_entry_html,
	write_entry_index,
	write_entry_pairs,
	write_entry_source,
	write_entry_text,
	write_int,
	write_list,
	write_long,
	write_string,
)

if TYPE_CHECKING:
	from collections.abc import Generator

	from pyglossary.stubs.glossary_types import EntryType, WriterGlossaryType

__all__ = ["Writer"]


_defaultNormalizerRulesDE = ":: Lower; 'ae' > 'ä'; 'oe' > 'ö'; 'ue' > 'ü'; 'ß' > 'ss'; "
_defaultNormalizerRules = (
	":: Any-Latin; ' ' > ; :: Lower; :: NFD; :: [:Nonspacing Mark:] Remove; :: NFC ;"
)


class Writer:
	"""Write glossary files in QuickDic 6 format."""

	_normalizer_rules = ""

	def __init__(self, glos: WriterGlossaryType) -> None:
		self._glos = glos
		self._filename = ""
		self._dic = None

	def finish(self) -> None:
		self._filename = ""
		self._dic = None

	def open(self, filename: str) -> None:
		self._filename = filename

	@staticmethod
	def write_quickdic(dic: QuickDic, path: str) -> None:
		with open(path, "wb") as fp:
			log.info(f"Writing to {path} ...")
			write_int(fp, dic.version)
			write_long(fp, int(dic.created.timestamp() * 1000))
			write_string(fp, dic.name)
			write_list(fp, write_entry_source, dic.sources)
			write_list(fp, write_entry_pairs, dic.pairs)
			write_list(fp, write_entry_text, dic.texts)
			write_list(fp, write_entry_html, dic.htmls)
			write_list(fp, write_entry_index, dic.indices)
			write_string(fp, "END OF DICTIONARY")

	@staticmethod
	def _process_entry(
		entry: EntryType,
		synonyms: dict[str, list[str]],
		htmls: list[tuple[int, str, str]],
	) -> None:
		if entry.isData():
			log.warning(f"Ignoring binary data entry {entry.l_term[0]}")
			return

		entry.detectDefiFormat()
		if entry.defiFormat not in {"h", "m"}:
			log.error(f"Unsupported defiFormat={entry.defiFormat}, assuming 'h'")

		terms = entry.l_term
		if terms[0] in synonyms:
			synonyms[terms[0]] += terms[1:]
		else:
			synonyms[terms[0]] = terms[1:]

		# Note that we currently write out all entries as "html" type entries.
		# In the future, it might make sense to add an option that somehow
		# specifies the entry type to use.
		htmls.append((0, terms[0], entry.defi))

	def _get_lang_codes(self) -> tuple[str, str]:
		glos = self._glos
		sourceLangCode, targetLangCode = "EN", "EN"
		if glos.sourceLang:
			sourceLangCode = glos.sourceLang.code
		if glos.targetLang:
			targetLangCode = glos.targetLang.code
		return sourceLangCode, targetLangCode

	def _get_name(self, langs: str) -> str:
		glos = self._glos
		name = glos.getInfo("bookname")
		if not name:
			name = glos.getInfo("description")
		if langs not in name.lower():
			name = f"{glos.getInfo('name')} ({langs})"
		return name

	@staticmethod
	def _get_created() -> dt.datetime | None:
		createdStr = os.getenv("QUICKDIC_CREATION_TIME")
		if not createdStr:
			return None
		created = dt.datetime.fromtimestamp(int(createdStr), tz=dt.UTC)
		log.info(f"QuickDic: using created={created.isoformat()!r}")
		return created

	def _build_dic(
		self,
		htmls: list[tuple[int, str, str]],
		synonyms: dict[str, list[str]],
	) -> QuickDic:
		log.info("Collecting meta data ...")
		sourceLangCode, targetLangCode = self._get_lang_codes()
		langs = f"{sourceLangCode}->{targetLangCode}"
		name = self._get_name(langs)
		log.info(f"QuickDic: {langs = }, {name = }")

		dic = QuickDic(
			name=name,
			sources=[("", len(htmls))],
			pairs=[],
			texts=[],
			htmls=htmls,
			created=self._get_created(),
			# version: int = 6,
			# indices: list[EntryIndexTuple] | None = None,
		)

		short_name = long_name = iso = sourceLangCode
		normalizer_rules = self._normalizer_rules or (
			_defaultNormalizerRulesDE if iso == "DE" else _defaultNormalizerRules
		)
		dic.add_index(
			short_name,
			long_name,
			iso,
			normalizer_rules,
			synonyms=synonyms,
		)
		return dic

	def write(self) -> Generator[None, EntryType, None]:
		synonyms: dict[str, list[str]] = {}
		htmls: list[tuple[int, str, str]] = []
		log.info("Converting individual entries ...")
		while True:
			entry = yield
			if entry is None:
				break
			self._process_entry(entry, synonyms, htmls)

		self._dic = self._build_dic(htmls, synonyms)
		self.write_quickdic(self._dic, self._filename)
