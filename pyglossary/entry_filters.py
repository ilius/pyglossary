# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
import re
import typing
from typing import TYPE_CHECKING

from . import core
from .text_utils import (
	fixUtf8,
)

if TYPE_CHECKING:
	from .glossary_types import Callable, EntryType, GlossaryExtendedType, GlossaryType


__all__ = [
	"EntryFilterType",
	"PreventDuplicateWords",
	"RemoveHtmlTagsAll",
	"ShowMaxMemoryUsage",
	"ShowProgressBar",
	"StripFullHtml",
	"entryFiltersRules",
]


log = logging.getLogger("pyglossary")


class EntryFilterType(typing.Protocol):
	name: str = ""
	desc: str = ""
	falseComment: str = ""

	def __init__(self, glos: GlossaryType) -> None:
		raise NotImplementedError

	def prepare(self) -> None:
		raise NotImplementedError

	def run(self, entry: EntryType) -> EntryType | None:
		raise NotImplementedError


class EntryFilter:
	name: str = ""
	desc: str = ""
	falseComment: str = ""

	def __init__(self, glos: GlossaryType) -> None:
		self.glos = glos

	def prepare(self) -> None:
		"""Run this after glossary info is set and ready."""

	def run(self, entry: EntryType) -> EntryType | None:  # noqa: PLR6301
		"""
		Return an Entry object, or None to skip.

		may return the same `entry`,
		or modify and return it,
		or return a new Entry object.
		"""
		return entry


class TrimWhitespaces(EntryFilter):
	name = "trim_whitespaces"
	desc = "Remove leading/trailing whitespaces from word(s) and definition"

	def run(self, entry: EntryType) -> EntryType | None:  # noqa: PLR6301
		entry.strip()
		entry.replace("\r", "")
		return entry


class NonEmptyWordFilter(EntryFilter):
	name = "non_empty_word"
	desc = "Skip entries with empty word"

	def run(self, entry: EntryType) -> EntryType | None:  # noqa: PLR6301
		if not entry.s_word:
			return None
		return entry


class NonEmptyDefiFilter(EntryFilter):
	name = "non_empty_defi"
	desc = "Skip entries with empty definition"

	def run(self, entry: EntryType) -> EntryType | None:  # noqa: PLR6301
		if not entry.defi:
			return None
		return entry


class RemoveEmptyAndDuplicateAltWords(EntryFilter):
	name = "remove_empty_dup_alt_words"
	desc = "Remove empty and duplicate alternate words"

	def run(self, entry: EntryType) -> EntryType | None:  # noqa: PLR6301
		entry.removeEmptyAndDuplicateAltWords()
		if not entry.l_word:
			return None
		return entry


class FixUnicode(EntryFilter):
	name = "utf8_check"
	desc = "Fix Unicode in word(s) and definition"
	falseComment = "Do not fix Unicode in word(s) and definition"

	def run(self, entry: EntryType) -> EntryType | None:  # noqa: PLR6301
		entry.editFuncWord(fixUtf8)
		entry.editFuncDefi(fixUtf8)
		return entry


class LowerWord(EntryFilter):
	name = "lower"
	desc = "Lowercase word(s)"
	falseComment = "Do not lowercase words before writing"

	def __init__(self, glos: GlossaryType) -> None:
		EntryFilter.__init__(self, glos)
		self._re_word_ref = re.compile("href=[\"'](bword://[^\"']+)[\"']")

	def lowerWordRefs(self, defi: str) -> str:
		return self._re_word_ref.sub(
			lambda m: m.group(0).lower(),
			defi,
		)

	def run(self, entry: EntryType) -> EntryType | None:
		entry.editFuncWord(str.lower)
		entry.editFuncDefi(self.lowerWordRefs)
		return entry


class RTLDefi(EntryFilter):
	name = "rtl"
	desc = "Make definition right-to-left"

	def run(self, entry: EntryType) -> EntryType | None:  # noqa: PLR6301
		entry.editFuncDefi(lambda defi: f'<div dir="rtl">{defi}</div>')
		return entry


class RemoveHtmlTagsAll(EntryFilter):
	name = "remove_html_all"
	desc = "Remove all HTML tags (not their contents) from definition"

	def __init__(
		self,
		glos: GlossaryType,  # noqa: ARG002
	) -> None:
		self._p_pattern = re.compile(
			"<p( [^<>]*?)?>(.*?)</p>",
			re.DOTALL,
		)
		self._div_pattern = re.compile(
			"<div( [^<>]*?)?>(.*?)</div>",
			re.DOTALL,
		)
		self._br_pattern = re.compile(
			"<br[ /]*>",
			re.IGNORECASE,
		)

	def run(self, entry: EntryType) -> EntryType | None:
		from bs4 import BeautifulSoup

		def fixStr(st: str) -> str:
			st = self._p_pattern.sub("\\2\n", st)
			# if there is </p> left without opening, replace with <br>
			st = st.replace("</p>", "\n")

			st = self._div_pattern.sub("\\2\n", st)
			# if there is </div> left without opening, replace with <br>
			st = st.replace("</div>", "\n")

			st = self._br_pattern.sub("\n", st)
			st = BeautifulSoup(st, "lxml").text
			st = st.strip()
			return st  # noqa: RET504

		entry.editFuncDefi(fixStr)
		return entry


class RemoveHtmlTags(EntryFilter):
	name = "remove_html"
	desc = "Remove given comma-separated HTML tags (not their contents) from definition"

	def __init__(self, glos: GlossaryType, tagsStr: str) -> None:
		tags = tagsStr.split(",")
		self.glos = glos
		self.tags = tags
		tagsRE = "|".join(self.tags)
		self.pattern = re.compile(f"</?({tagsRE})( [^>]*)?>")

	def run(self, entry: EntryType) -> EntryType | None:
		def fixStr(st: str) -> str:
			return self.pattern.sub("", st)

		entry.editFuncDefi(fixStr)
		return entry


class StripFullHtml(EntryFilter):
	name = "strip_full_html"
	desc = "Replace a full HTML document with it's body"

	def __init__(
		self,
		glos: GlossaryType,  # noqa: ARG002
		errorHandler: Callable[[EntryType, str], None] | None,
	) -> None:
		self._errorHandler = errorHandler

	def run(self, entry: EntryType) -> EntryType | None:
		err = entry.stripFullHtml()
		if err and self._errorHandler:
			self._errorHandler(entry, err)
		return entry


# FIXME: It's is not safe to lowercases everything between < and >
# including class name, element ids/names, scripts, <a href="bword://...">
# etc. How can we fix that?
class NormalizeHtml(EntryFilter):
	name = "normalize_html"
	desc = "Normalize HTML tags in definition (WIP)"

	_tags = (
		"a",
		"font",
		"i",
		"b",
		"u",
		"p",
		"sup",
		"div",
		"span",
		"table",
		"tr",
		"th",
		"td",
		"ul",
		"ol",
		"li",
		"img",
		"br",
		"hr",
	)

	def __init__(
		self,
		glos: GlossaryType,  # noqa: ARG002
	) -> None:
		log.info("Normalizing HTML tags")
		self._pattern = re.compile(
			"(" + "|".join(rf"</?{tag}[^<>]*?>" for tag in self._tags) + ")",
			re.DOTALL | re.IGNORECASE,
		)

	@staticmethod
	def _subLower(m: re.Match) -> str:
		return m.group(0).lower()

	def _fixDefi(self, st: str) -> str:
		return self._pattern.sub(self._subLower, st)

	def run(self, entry: EntryType) -> EntryType | None:
		entry.editFuncDefi(self._fixDefi)
		return entry


class SkipDataEntry(EntryFilter):
	name = "skip_resources"
	desc = "Skip resources / data files"

	def run(self, entry: EntryType) -> EntryType | None:  # noqa: PLR6301
		if entry.isData():
			return None
		return entry


class LanguageCleanup(EntryFilter):
	name = "lang"
	desc = "Language-specific cleanup/fixes"

	def __init__(self, glos: GlossaryType) -> None:
		EntryFilter.__init__(self, glos)
		self._run_func: Callable[[EntryType], EntryType | None] | None = None

	def prepare(self) -> None:
		langCodes = {
			lang.code
			for lang in (self.glos.sourceLang, self.glos.targetLang)
			if lang is not None
		}
		if "fa" in langCodes:
			self._run_func = self.run_fa
			log.info("Using Persian filter")

	def run_fa(self, entry: EntryType) -> EntryType | None:  # noqa: PLR6301
		from .persian_utils import faEditStr

		entry.editFuncWord(faEditStr)
		entry.editFuncDefi(faEditStr)
		# RLM = "\xe2\x80\x8f"
		# defi = "\n".join(RLM+line for line in defi.split("\n"))
		# for GoldenDict ^^ FIXME
		return entry

	def run(self, entry: EntryType) -> EntryType | None:
		if self._run_func:
			return self._run_func(entry)
		return entry


class TextListSymbolCleanup(EntryFilter):

	"""
	Symbols like ♦ (diamond) ● (black circle) or * (star) are used in some
	plaintext or even html glossaries to represent items of a list
	(like <li> in proper html).
	This EntryFilter cleans up spaces/newlines issues around them.
	"""

	name = "text_list_symbol_cleanup"
	desc = "Text List Symbol Cleanup"

	winNewlinePattern = re.compile("[\r\n]+")
	spacesNewlinePattern = re.compile(" *\n *")
	blocksNewlinePattern = re.compile("♦\n+♦")

	def cleanDefi(self, st: str) -> str:
		st = st.replace("♦  ", "♦ ")
		st = self.winNewlinePattern.sub("\n", st)
		st = self.spacesNewlinePattern.sub("\n", st)

		st = self.blocksNewlinePattern.sub("♦", st)
		st = st.removesuffix("<p")
		st = st.strip()
		st = st.removesuffix(",")

		return st  # noqa: RET504

	def run(self, entry: EntryType) -> EntryType | None:
		entry.editFuncDefi(self.cleanDefi)
		return entry


class PreventDuplicateWords(EntryFilter):
	name = "prevent_duplicate_words"
	desc = "Prevent duplicate words"

	def __init__(self, glos: GlossaryType) -> None:
		EntryFilter.__init__(self, glos)
		self._wordSet: set[str] = set()

	def run(self, entry: EntryType) -> EntryType | None:
		if entry.isData():
			return entry

		wordSet = self._wordSet
		word = entry.s_word

		if word not in wordSet:
			wordSet.add(word)
			return entry

		n = 2
		while f"{word} ({n})" in wordSet:
			n += 1
		word = f"{word} ({n})"

		wordSet.add(word)
		entry._word = word  # type: ignore
		# use entry.editFuncWord?

		return entry


class SkipEntriesWithDuplicateHeadword(EntryFilter):
	name = "skip_duplicate_headword"
	desc = "Skip entries with a duplicate headword"

	def __init__(self, glos: GlossaryType) -> None:
		EntryFilter.__init__(self, glos)
		self._wset: set[str] = set()

	def run(self, entry: EntryType) -> EntryType | None:
		word = entry.l_word[0]
		if word in self._wset:
			return None
		self._wset.add(word)
		return entry


class TrimArabicDiacritics(EntryFilter):
	name = "trim_arabic_diacritics"
	desc = "Trim Arabic diacritics from headword"

	def __init__(self, glos: GlossaryType) -> None:
		EntryFilter.__init__(self, glos)
		self._pat = re.compile("[\u064b-\u065f]")

	def run(self, entry: EntryType) -> EntryType | None:
		words = list(entry.l_word)
		hw = words[0]
		hw_t = self._pat.sub("", hw)
		hw_t = hw_t.replace("\u0622", "\u0627").replace("\u0623", "\u0627")
		if hw_t == hw or not hw_t:
			return entry
		entry._word = [hw_t, *words]  # type: ignore
		return entry


class UnescapeWordLinks(EntryFilter):
	name = "unescape_word_links"
	desc = "Unescape Word Links"

	def __init__(self, glos: GlossaryType) -> None:
		from pyglossary.html_utils import unescape_unicode

		EntryFilter.__init__(self, glos)
		self._pat = re.compile(
			r'href="bword://[^<>"]*&#?\w+;[^<>"]*"',
			re.IGNORECASE,
		)
		self._unescape = unescape_unicode

	def _sub(self, m: re.Match) -> str:
		return self._unescape(m.group(0))

	def run(self, entry: EntryType) -> EntryType | None:
		if entry.isData():
			return entry
		entry._defi = self._pat.sub(self._sub, entry.defi)  # type: ignore
		return entry


class ShowProgressBar(EntryFilter):
	name = "progressbar"
	desc = "Progress Bar"

	def __init__(self, glos: GlossaryExtendedType) -> None:
		EntryFilter.__init__(self, glos)
		self.glos: GlossaryExtendedType = glos
		self._wordCount = -1
		self._wordCountThreshold = 0
		self._lastPos = 0
		self._index = 0

	def run(self, entry: EntryType) -> EntryType | None:
		index = self._index
		self._index = index + 1

		if entry is not None and (bp := entry.byteProgress()):
			if bp[0] > self._lastPos + 100_000:
				self.glos.progress(bp[0], bp[1], unit="bytes")
				self._lastPos = bp[0]
			return entry

		if self._wordCount == -1:
			self._wordCount = len(self.glos)
			self._wordCountThreshold = max(
				1,
				min(
					500,
					self._wordCount // 200,
				),
			)

		if self._wordCount > 1 and index % self._wordCountThreshold == 0:
			self.glos.progress(index, self._wordCount)

		return entry


class ShowMaxMemoryUsage(EntryFilter):
	name = "max_memory_usage"
	desc = "Show Max Memory Usage"
	MAX_WORD_LEN = 30

	def __init__(self, glos: GlossaryType) -> None:
		import os

		import psutil

		EntryFilter.__init__(self, glos)
		self._process = psutil.Process(os.getpid())
		self._max_mem_usage = 0

	def run(self, entry: EntryType) -> EntryType | None:
		usage = self._process.memory_info().rss // 1024
		if usage > self._max_mem_usage:
			self._max_mem_usage = usage
			word = entry.s_word
			if len(word) > self.MAX_WORD_LEN:
				word = word[: self.MAX_WORD_LEN - 3] + "..."
			core.trace(log, f"MaxMemUsage: {usage:,}, {word=}")
		return entry


entryFiltersRules = [
	(None, True, TrimWhitespaces),
	(None, True, NonEmptyWordFilter),
	("skip_resources", False, SkipDataEntry),
	("utf8_check", False, FixUnicode),
	("lower", False, LowerWord),
	("skip_duplicate_headword", False, SkipEntriesWithDuplicateHeadword),
	("trim_arabic_diacritics", False, TrimArabicDiacritics),
	("rtl", False, RTLDefi),
	("remove_html_all", False, RemoveHtmlTagsAll),
	("remove_html", "", RemoveHtmlTags),
	("normalize_html", False, NormalizeHtml),
	("unescape_word_links", False, UnescapeWordLinks),
	(None, True, LanguageCleanup),
	# -------------------------------------
	# TODO
	# ("text_list_symbol_cleanup", False, TextListSymbolCleanup),
	# -------------------------------------
	(None, True, NonEmptyWordFilter),
	(None, True, NonEmptyDefiFilter),
	(None, True, RemoveEmptyAndDuplicateAltWords),
	# -------------------------------------
	# filters that are enabled by plugins using glossary methods:
	(None, False, PreventDuplicateWords),
	(None, False, StripFullHtml),
	# -------------------------------------
	# filters are added conditionally (other than with config or glossary methods):
	(None, False, ShowProgressBar),
	(None, False, ShowMaxMemoryUsage),
]
