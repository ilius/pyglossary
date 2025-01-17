# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
import re
from os.path import join
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
	from collections.abc import Generator, Sequence

	from pyglossary.glossary_types import EntryType, WriterGlossaryType

__all__ = ["Writer"]


def _isKana(char: str) -> bool:
	assert len(char) == 1
	val = ord(char)
	return (
		0x3040 <= val <= 0x309F  # Hiragana
		or 0x30A0 <= val <= 0x30FF  # Katakana (incl. center dot)
		or 0xFF65 <= val <= 0xFF9F  # Half-width Katakana (incl. center dot)
	)


def _isKanji(char: str) -> bool:
	assert len(char) == 1
	val = ord(char)
	return (
		0x3400 <= val <= 0x4DBF  # CJK Unified Ideographs Extension A
		or 0x4E00 <= val <= 0x9FFF  # CJK Unified Ideographs
		or 0xF900 <= val <= 0xFAFF  # CJK Compatibility Ideographs
		or 0x20000 <= val <= 0x2A6DF  # CJK Unified Ideographs Extension B
		or 0x2A700 <= val <= 0x2B73F  # CJK Unified Ideographs Extension C
		or 0x2B740 <= val <= 0x2B81F  # CJK Unified Ideographs Extension D
		or 0x2F800 <= val <= 0x2FA1F  # CJK Compatibility Ideographs Supplement
	)


def _uniqueList(lst: Sequence[str]) -> list[str]:
	seen: set[str] = set()
	result: list[str] = []
	for elem in lst:
		if elem not in seen:
			seen.add(elem)
			result.append(elem)

	return result


def _compilePat(pattern: str) -> re.Pattern | None:
	if not pattern:
		return None
	return re.compile(pattern)


class Writer:
	depends = {
		"bs4": "beautifulsoup4",
	}

	_term_bank_size = 10_000
	_term_from_headword_only = True
	_no_term_from_reading = True
	_delete_word_pattern = ""
	_ignore_word_with_pattern = ""
	_alternates_from_word_pattern = ""
	_alternates_from_defi_pattern = ""
	_rule_v1_defi_pattern = ""
	_rule_v5_defi_pattern = ""
	_rule_vs_defi_pattern = ""
	_rule_vk_defi_pattern = ""
	_rule_adji_defi_pattern = ""

	def __init__(self, glos: WriterGlossaryType) -> None:
		self._glos = glos
		self._filename = ""
		# Yomichan technically supports "structured content" that renders to
		# HTML, but it doesn't seem widely used. So here we also strip HTML
		# formatting for simplicity.
		glos.removeHtmlTagsAll()
		self.delete_word_pattern = _compilePat(self._delete_word_pattern)
		self.ignore_word_with_pattern = _compilePat(self._ignore_word_with_pattern)
		self.alternates_from_word_pattern = _compilePat(
			self._alternates_from_word_pattern
		)
		self.alternates_from_defi_pattern = _compilePat(
			self._alternates_from_defi_pattern
		)
		self.rules = [
			(_compilePat(self._rule_v1_defi_pattern), "v1"),
			(_compilePat(self._rule_v5_defi_pattern), "v5"),
			(_compilePat(self._rule_vs_defi_pattern), "vs"),
			(_compilePat(self._rule_vk_defi_pattern), "vk"),
			(_compilePat(self._rule_adji_defi_pattern), "adj-i"),
		]

	def _getInfo(self, key: str) -> str:
		info = self._glos.getInfo(key)
		return info.replace("\n", "<br>")

	def _getAuthor(self) -> str:
		return self._glos.author.replace("\n", "<br>")

	def _getDictionaryIndex(self) -> dict[str, Any]:
		# Schema: https://github.com/FooSoft/yomichan/
		# blob/master/ext/data/schemas/dictionary-index-schema.json
		return {
			"title": self._getInfo("title"),
			"revision": "PyGlossary export",
			"sequenced": True,
			"format": 3,
			"author": self._getAuthor(),
			"url": self._getInfo("website"),
			"description": self._getInfo("description"),
		}

	def _getExpressionsAndReadingFromEntry(
		self,
		entry: EntryType,
	) -> tuple[list[str], str]:
		term_expressions = entry.l_word

		alternates_from_word_pattern = self.alternates_from_word_pattern
		if alternates_from_word_pattern:
			for word in entry.l_word:
				term_expressions += alternates_from_word_pattern.findall(word)

		if self.alternates_from_defi_pattern:
			term_expressions += self.alternates_from_defi_pattern.findall(
				entry.defi,
				re.MULTILINE,
			)

		delete_word_pattern = self.delete_word_pattern
		if delete_word_pattern:
			term_expressions = [
				delete_word_pattern.sub("", expression)
				for expression in term_expressions
			]

		ignore_word_with_pattern = self.ignore_word_with_pattern
		if ignore_word_with_pattern:
			term_expressions = [
				expression
				for expression in term_expressions
				if not ignore_word_with_pattern.search(expression)
			]

		term_expressions = _uniqueList(term_expressions)

		try:
			reading = next(
				expression
				for expression in entry.l_word + term_expressions
				if all(map(_isKana, expression))
			)
		except StopIteration:
			reading = ""

		if self._no_term_from_reading and len(term_expressions) > 1:
			term_expressions = [
				expression for expression in term_expressions if expression != reading
			]

		if self._term_from_headword_only:
			term_expressions = term_expressions[:1]

		return term_expressions, reading

	def _getRuleIdentifiersFromEntry(self, entry: EntryType) -> list[str]:
		return [
			rule
			for pattern, rule in self.rules
			if pattern and pattern.search(entry.defi, re.MULTILINE)
		]

	def _getTermsFromEntry(
		self,
		entry: EntryType,
		sequenceNumber: int,
	) -> list[list[Any]]:
		termExpressions, reading = self._getExpressionsAndReadingFromEntry(entry)
		ruleIdentifiers = self._getRuleIdentifiersFromEntry(entry)

		# Schema: https://github.com/FooSoft/yomichan/
		# blob/master/ext/data/schemas/dictionary-term-bank-v3-schema.json
		return [
			[
				expression,
				# reading only added if expression contains kanji
				reading if any(map(_isKanji, expression)) else "",
				"",  # definition tags
				" ".join(ruleIdentifiers),
				0,  # score
				[entry.defi],
				sequenceNumber,
				"",  # term tags
			]
			for expression in termExpressions
		]

	def open(self, filename: str) -> None:
		self._filename = filename
		self._glos.mergeEntriesWithSameHeadwordPlaintext()

	def finish(self) -> None:
		self._filename = ""

	def write(self) -> Generator[None, EntryType, None]:
		direc = self._filename

		os.makedirs(direc, exist_ok=True)

		with open(join(direc, "index.json"), "w", encoding="utf-8") as f:
			json.dump(self._getDictionaryIndex(), f, ensure_ascii=False)

		entryCount = 0
		termBankIndex = 0
		terms: list[list[Any]] = []

		def flushTerms() -> None:
			nonlocal termBankIndex
			if not terms:
				return
			with open(
				join(direc, f"term_bank_{termBankIndex + 1}.json"),
				mode="w",
				encoding="utf-8",
			) as _file:
				json.dump(terms, _file, ensure_ascii=False)
			terms.clear()
			termBankIndex += 1

		while True:
			entry: EntryType
			entry = yield
			if entry is None:
				break

			if entry.isData():
				continue

			terms.extend(self._getTermsFromEntry(entry, entryCount))
			entryCount += 1
			if len(terms) >= self._term_bank_size:
				flushTerms()

		flushTerms()
