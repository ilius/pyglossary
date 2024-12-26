# -*- coding: utf-8 -*-
from __future__ import annotations

import datetime as dt
import os
import typing
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from pyglossary.glossary_types import EntryType, GlossaryType

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

__all__ = ["Writer"]


default_de_normalizer_rules = (
	":: Lower; 'ae' > 'ä'; 'oe' > 'ö'; 'ue' > 'ü'; 'ß' > 'ss'; "
)
default_normalizer_rules = (
	":: Any-Latin; ' ' > ; "
	":: Lower; :: NFD; "
	":: [:Nonspacing Mark:] Remove; "
	":: NFC ;"
)


class Writer:
	_normalizer_rules = ""

	def __init__(self, glos: GlossaryType) -> None:
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

	def write(self) -> typing.Generator[None, EntryType, None]:
		synonyms: dict[str, list[str]] = {}
		htmls: list[tuple[int, str, str]] = []
		log.info("Converting individual entries ...")
		while True:
			entry = yield
			if entry is None:
				break
			if entry.isData():
				log.warn(f"Ignoring binary data entry {entry.l_word[0]}")
				continue

			entry.detectDefiFormat()
			if entry.defiFormat not in {"h", "m"}:
				log.error(f"Unsupported defiFormat={entry.defiFormat}, assuming 'h'")

			words = entry.l_word
			if words[0] in synonyms:
				synonyms[words[0]].extend(words[1:])
			else:
				synonyms[words[0]] = words[1:]

			# Note that we currently write out all entries as "html" type entries.
			# In the future, it might make sense to add an option that somehow
			# specifies the entry type to use.
			htmls.append((0, words[0], entry.defi))

		glos = self._glos

		log.info("Collecting meta data ...")
		name = glos.getInfo("bookname")
		if not name:
			name = glos.getInfo("description")

		sourceLangCode, targetLangCode = "EN", "EN"
		if glos.sourceLang:
			sourceLangCode = glos.sourceLang.code
		if glos.targetLang:
			targetLangCode = glos.targetLang.code

		langs = f"{sourceLangCode}->{targetLangCode}"
		if langs not in name.lower():
			name = f"{self._glos.getInfo('name')} ({langs})"

		log.info(f"QuickDic: {langs = }, {name = }")

		sources = [("", len(htmls))]

		created = None
		createdStr = os.getenv("QUICKDIC_CREATION_TIME")
		if createdStr:
			created = dt.datetime.fromtimestamp(int(createdStr), tz=dt.timezone.utc)
			log.info(f"QuickDic: using created={created.isoformat()!r}")

		self._dic = QuickDic(
			name=name,
			sources=sources,
			pairs=[],
			texts=[],
			htmls=htmls,
			created=created,
			# version: int = 6,
			# indices: list[EntryIndexTuple] | None = None,
		)

		short_name = long_name = iso = sourceLangCode
		normalizer_rules = self._normalizer_rules or (
			default_de_normalizer_rules if iso == "DE" else default_normalizer_rules
		)
		self._dic.add_index(
			short_name,
			long_name,
			iso,
			normalizer_rules,
			synonyms=synonyms,
		)

		self.write_quickdic(self._dic, self._filename)
