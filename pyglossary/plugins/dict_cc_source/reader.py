# -*- coding: utf-8 -*-
# Conversion logic adapted from dictcc-stardict (MIT License)
# https://github.com/Linus789/dictcc-stardict/blob/main/convert.py

from __future__ import annotations

import html
import unicodedata
from collections import defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING

from pyglossary.compress import compressionOpen
from pyglossary.core import log

from .field_parser import FieldParser, SourceWord, get_language_pair

if TYPE_CHECKING:
	from collections.abc import Iterator

	from pyglossary.glossary_types import EntryType, ReaderGlossaryType

__all__ = ["Reader"]

_TranslationsBucket = dict[tuple[str, ...], set[tuple[str, bool]]]


@dataclass
class _DictEntry:
	translations: list[tuple[str | None, str]]
	source_word_is_replacement: bool | None


class Reader:
	useByteProgress = False
	depends = {
		"pyparsing": "pyparsing",
	}
	compressions = ("gz", "bz2", "lzma")

	_source_lang = ""

	def __init__(self, glos: ReaderGlossaryType) -> None:
		self._glos = glos
		self._filename = ""
		self._entryCount = 0

	def open(self, filename: str) -> None:
		self._glos.detectLangsFromName()
		from_lang = self._source_lang.strip().lower()
		if not from_lang:
			if self._glos.sourceLang:
				from_lang = self._glos.sourceLang.code
			else:
				msg = (
					"dict_cc_source: read option `source_lang` is required "
					"(ISO language code for the source column, e.g. en or de)"
				)
				raise ValueError(msg)

		self._filename = filename
		self._glos.setDefaultDefiFormat("h")
		lang_pair = get_language_pair(filename)
		lang_pair_from, lang_pair_to = lang_pair.split("-")
		self._inverse_langs: bool | None = None
		if from_lang == lang_pair_from:
			self._inverse_langs = False
		elif from_lang == lang_pair_to:
			self._inverse_langs = True
		if self._inverse_langs is None:
			msg = (
				f"{from_lang!r} is not allowed as source language for this file. "
				f"Available: {lang_pair_from!r}, {lang_pair_to!r}."
			)
			raise ValueError(msg)

		self._from_lang = from_lang
		self._to_lang = lang_pair_to if not self._inverse_langs else lang_pair_from

	def close(self) -> None:
		pass

	def __len__(self) -> int:
		return self._entryCount

	def _fill_dictionary(
		self,
		field_parser: FieldParser,
		from_lang: str,
		inverse_langs: bool,
		lines: list[str],
	) -> dict[str, _DictEntry]:
		dictionary: dict[str, _DictEntry] = defaultdict(
			lambda: _DictEntry([], None),
		)
		num_lines = len(lines)
		for index, raw_line in enumerate(lines, start=1):
			if index % 50_000 == 0:
				log.info(f"dict_cc_source: parsing line {index}/{num_lines}")
			line_stripped = raw_line.strip()
			if not line_stripped or line_stripped[0] == "#":
				continue

			fields = line_stripped.split("\t")
			if len(fields) < 2:
				continue

			src, target = (
				unicodedata.normalize("NFC", html.unescape(field)) for field in fields[:2]
			)
			word_class = fields[2].strip().lower() if len(fields) > 2 else None
			word_class = word_class or None

			if inverse_langs:
				src, target = target, src

			target = " ".join(target.split())
			if not target:
				continue

			for possible_source_word in field_parser.get_possible_source_words(
				src,
				word_class,
				from_lang,
			):
				assert isinstance(possible_source_word, SourceWord)
				entry = dictionary[possible_source_word.word]
				entry.translations.append((word_class, target))

				if entry.source_word_is_replacement is None:
					has_rep = possible_source_word.has_replacements
					entry.source_word_is_replacement = has_rep
				else:
					entry.source_word_is_replacement = (
						entry.source_word_is_replacement
						or possible_source_word.has_replacements
					)

		return dictionary

	def _translations_buckets(
		self,
		dictionary: dict[str, _DictEntry],
	) -> _TranslationsBucket:
		translations_to_source_words: _TranslationsBucket = defaultdict(set)

		dictionary_num_entries = len(dictionary)
		for index, (src, entry) in enumerate(dictionary.items(), start=1):
			if index % 50_000 == 0:
				msg = f"dict_cc_source: deduplicating {index}/{dictionary_num_entries}"
				log.info(msg)
			translation_to_word_class: dict[str, str | None] = {}

			for wc, translation in entry.translations:
				if translation in translation_to_word_class:
					if not wc:
						continue
					translation_to_word_class[translation] = wc
				else:
					translation_to_word_class[translation] = wc

			sort_weights: dict[str, int] = {}
			for translation, wc in translation_to_word_class.items():
				if wc == "adj":
					wc_norm = 0
				elif wc == "verb":
					wc_norm = 1
				elif wc == "noun":
					wc_norm = 2
				else:
					wc_norm = 3
				sort_weights[translation] = wc_norm

			translations = sorted(
				sort_weights.items(),
				key=lambda x: (x[1], x[0].lower(), x[0]),
			)
			translations_tuple = tuple(t[0] for t in translations)
			translations_to_source_words[translations_tuple].add(
				(src, bool(entry.source_word_is_replacement)),
			)

		return translations_to_source_words

	def __iter__(self) -> Iterator[EntryType]:
		from_lang = self._from_lang
		inverse_langs = self._inverse_langs
		assert inverse_langs is not None

		field_parser = FieldParser()

		with compressionOpen(self._filename, mode="rt", encoding="utf-8") as fp:
			lines = fp.readlines()

		dictionary = self._fill_dictionary(field_parser, from_lang, inverse_langs, lines)
		translations_to_source_words = self._translations_buckets(dictionary)

		fl = self._from_lang.upper()
		tl = self._to_lang.upper()
		self._glos.setInfo("title", f"dict.cc {fl}-{tl}")

		total = len(translations_to_source_words)
		for count, (translations, src_words) in enumerate(
			translations_to_source_words.items(),
			start=1,
		):
			if count % 50_000 == 0:
				log.info(f"dict_cc_source: building entries {count}/{total}")

			longest_src_word_without_replacements = min(
				src_words,
				key=lambda x: (x[1], -len(x[0])),
			)
			src_words_mut = set(src_words)
			src_words_mut.remove(longest_src_word_without_replacements)
			headword = longest_src_word_without_replacements[0]

			definition = " " + "".join(
				f" {html.escape(translation)} " for translation in translations
			)
			definition += " "

			entry = self._glos.newEntry(headword, definition, defiFormat="h")
			for other_src_word, _ in src_words_mut:
				entry.addAlt(other_src_word)

			yield entry

		self._entryCount = total
