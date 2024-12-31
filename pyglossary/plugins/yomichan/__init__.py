# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
import re
from os.path import join
from typing import TYPE_CHECKING, Any

from pyglossary.flags import ALWAYS
from pyglossary.option import (
	BoolOption,
	IntOption,
	Option,
	StrOption,
)

if TYPE_CHECKING:
	from collections.abc import Generator, Sequence

	from pyglossary.glossary_types import EntryType, GlossaryType

__all__ = [
	"Writer",
	"description",
	"enable",
	"extensionCreate",
	"extensions",
	"kind",
	"lname",
	"name",
	"optionsProp",
	"singleFile",
	"website",
	"wiki",
]

enable = True
lname = "yomichan"
name = "Yomichan"
description = "Yomichan (.zip)"
extensions = (".zip",)
extensionCreate = ".zip"
singleFile = True
sortOnWrite = ALWAYS
sortKeyName = "headword"
kind = "package"
wiki = ""
website = (
	"https://foosoft.net/projects/yomichan/",
	"foosoft.net",
)
optionsProp: dict[str, Option] = {
	"term_bank_size": IntOption(
		comment="The number of terms in each term bank json file.",
	),
	"term_from_headword_only": BoolOption(
		comment=(
			"If set to true, only create a term for the headword for each entry, "
			"as opposed to create one term for each alternate word. "
			"If the headword is ignored by the `ignore_word_with_pattern` option, "
			"the next word in the alternate list that is not ignored is used as "
			"headword."
		),
	),
	"no_term_from_reading": BoolOption(
		comment=(
			"When there are multiple alternate words, don't create term for the "
			"one that is the same as the the reading form, which is chosen to be "
			"the first alternate forms that consists solely of Hiragana and "
			"Katakana. "
			"For example, an entry could contain both 'だいがく' and '大学' as "
			"alternate words. Setting this option to true would prevent a term "
			"to be created for the former."
		),
	),
	"delete_word_pattern": StrOption(
		comment=(
			"When given, all non-overlapping matches of this regular expression "
			"are removed from word strings. "
			"For example, if an entry has word 'あま·い', setting the "
			"pattern to `·` removes all center dots, or more precisely use "
			"`·(?=[\\u3040-\\u309F])` to only remove center dots that precede "
			"Hiragana characters. Either way, the original word is replaced "
			"with 'あまい'."
		),
	),
	"ignore_word_with_pattern": StrOption(
		comment=(
			"When given, don't create terms for a word if any of its substrings "
			"matches this regular expression. "
			"For example, an entry could contain both 'だいがく【大学】' and '大学' "
			"as alternate words. Setting this option with value `r'【.+】'` would "
			"prevent a term to be created for the former."
		),
	),
	"alternates_from_word_pattern": StrOption(
		comment=(
			"When given, the regular expression is used to find additional "
			"alternate words for the same entry from matching substrings in "
			"the original words. "
			"If there are no capturing groups in the regular expression, "
			"then all matched substrings are added to the list of alternate "
			"words. "
			"If there are capturing groups, then substrings matching the groups "
			"are added to the alternate words list instead. "
			"For example, if an entry has 'だいがく【大学】' as a word, then "
			"`\\w+(?=【)` adds 'だいがく' as an additional word, while "
			"`(\\w+)【(\\w+)】` adds both 'だいがく' and '大学'."
		),
	),
	"alternates_from_defi_pattern": StrOption(
		comment=(
			"When given, the regular expression is used to find additional "
			"alternate words for the same entry from matching substrings in "
			"the definition. `^` and `$` can be used to match start and end of "
			"lines, respectively. "
			"If there are no capturing groups in the regular expression, "
			"then all matched substrings are added to the list of alternate "
			"words. "
			"If there are capturing groups, then substrings matching the groups "
			"are added to the alternate words list instead. "
			"For example, if an entry has 'だいがく【大学】' in its definition, then "
			"`\\w+【(\\w+)】` adds '大学' as an additional word."
		),
	),
	"rule_v1_defi_pattern": StrOption(
		comment=(
			"When given, if any substring of an entry's definition matches this "
			"regular expression, then the term(s) created from entry are labeled "
			"as ichidan verb. Yomichan uses this information to match conjugated "
			"forms of words. `^` and `$` can be used to match start and end of "
			"lines, respectively. "
			"For example, setting this option to `^\\(動[上下]一\\)$` identifies "
			"entries where there's a line of '(動上一)' or '(動下一)'."
		),
	),
	"rule_v5_defi_pattern": StrOption(
		comment=(
			"When given, if any substring of an entry's definition matches this "
			"regular expression, then the term(s) created from entry are labeled "
			"as godan verb. Yomichan uses this information to match conjugated "
			"forms of words. `^` and `$` can be used to match start and end of "
			"lines, respectively. "
			"For example, setting this option to `^\\(動五\\)$` identifies "
			"entries where there's a line of '(動五)'."
		),
	),
	"rule_vs_defi_pattern": StrOption(
		comment=(
			"When given, if any substring of an entry's definition matches this "
			"regular expression, then the term(s) created from entry are labeled "
			"as suru verb. Yomichan uses this information to match conjugated "
			"forms of words. `^` and `$` can be used to match start and end of "
			"lines, respectively. "
			"For example, setting this option to `^スル$` identifies entries where "
			"there's a line of 'スル'."
		),
	),
	"rule_vk_defi_pattern": StrOption(
		comment=(
			"When given, if any substring of an entry's definition matches this "
			"regular expression, then the term(s) created from entry are labeled "
			"as kuru verb. Yomichan uses this information to match conjugated "
			"forms of words. `^` and `$` can be used to match start and end of "
			"lines, respectively. "
			"For example, setting this option to `^\\(動カ変\\)$` identifies "
			"entries where there's a line of '(動カ変)'."
		),
	),
	"rule_adji_defi_pattern": StrOption(
		comment=(
			"When given, if any substring of an entry's definition matches this "
			"regular expression, then the term(s) created from entry are labeled "
			"as i-adjective. Yomichan uses this information to match conjugated "
			"forms of words. `^` and `$` can be used to match start and end of "
			"lines, respectively. "
			"For example, setting this option to `r'^\\(形\\)$'` identify "
			"entries where there's a line of '(形)'."
		),
	),
}


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

	def __init__(self, glos: GlossaryType) -> None:
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
