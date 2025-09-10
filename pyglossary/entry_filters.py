# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
import re
import typing
from typing import TYPE_CHECKING

from . import core
from .text_utils import fixUtf8Str

if TYPE_CHECKING:
	from .glossary_types import Callable, EntryType
	from .langs import Lang


__all__ = [
	"EntryFilterType",
	"PreventDuplicateTerms",
	"RemoveHtmlTagsAll",
	"ShowMaxMemoryUsage",
	"StripFullHtml",
	"entryFiltersRules",
]


log = logging.getLogger("pyglossary")


class _GlossaryType(typing.Protocol):
	@property
	def sourceLang(self) -> Lang | None: ...

	@property
	def targetLang(self) -> Lang | None: ...

	def progress(self, pos: int, total: int, unit: str = "entries") -> None: ...

	def __len__(self) -> int: ...


class EntryFilterType(typing.Protocol):
	name: str = ""
	desc: str = ""
	falseComment: str = ""

	def __init__(self, glos: _GlossaryType) -> None:
		raise NotImplementedError

	def prepare(self) -> None:
		raise NotImplementedError

	def run(self, entry: EntryType) -> EntryType | None:
		raise NotImplementedError


class EntryFilter:
	name: str = ""
	desc: str = ""
	falseComment: str = ""

	def __init__(self, glos: _GlossaryType) -> None:
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
	desc = "Remove leading/trailing whitespaces from term(s) and definition"

	def run(self, entry: EntryType) -> EntryType | None:  # noqa: PLR6301
		entry.strip()
		entry.replace("\r", "")
		return entry


class NonEmptyTermFilter(EntryFilter):
	name = "non_empty_term"
	desc = "Skip entries with empty terms"

	def run(self, entry: EntryType) -> EntryType | None:  # noqa: PLR6301
		if not entry.s_term:
			return None
		return entry


class NonEmptyDefiFilter(EntryFilter):
	name = "non_empty_defi"
	desc = "Skip entries with empty definition"

	def run(self, entry: EntryType) -> EntryType | None:  # noqa: PLR6301
		if not entry.defi:
			return None
		return entry


class RemoveEmptyAndDuplicateAltTerms(EntryFilter):
	name = "remove_empty_dup_alt_terms"
	desc = "Remove empty and duplicate alternate terms"

	def run(self, entry: EntryType) -> EntryType | None:  # noqa: PLR6301
		entry.removeEmptyAndDuplicateAltTerms()
		if not entry.l_term:
			return None
		return entry


class FixUnicode(EntryFilter):
	name = "utf8_check"
	desc = "Fix Unicode in term(s) and definition"
	falseComment = "Do not fix Unicode in term(s) and definition"

	def run(self, entry: EntryType) -> EntryType | None:  # noqa: PLR6301
		entry.editFuncTerm(fixUtf8Str)
		entry.editFuncDefi(fixUtf8Str)
		return entry


class LowerTerm(EntryFilter):
	name = "lower"
	desc = "Lowercase term(s)"
	falseComment = "Do not lowercase terms before writing"

	def __init__(self, glos: _GlossaryType) -> None:
		EntryFilter.__init__(self, glos)
		self._re_term_ref = re.compile("href=[\"'](bword://[^\"']+)[\"']")

	def lowerTermRefs(self, defi: str) -> str:
		return self._re_term_ref.sub(
			lambda m: m.group(0).lower(),
			defi,
		)

	def run(self, entry: EntryType) -> EntryType | None:
		entry.editFuncTerm(str.lower)
		entry.editFuncDefi(self.lowerTermRefs)
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
		glos: _GlossaryType,  # noqa: ARG002
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

	def __init__(self, glos: _GlossaryType, tagsStr: str) -> None:
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
		glos: _GlossaryType,  # noqa: ARG002
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
		glos: _GlossaryType,  # noqa: ARG002
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

	def __init__(self, glos: _GlossaryType) -> None:
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

		entry.editFuncTerm(faEditStr)
		entry.editFuncDefi(faEditStr)
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


class PreventDuplicateTerms(EntryFilter):
	name = "prevent_duplicate_terms"
	desc = "Prevent duplicate terms"

	def __init__(self, glos: _GlossaryType) -> None:
		EntryFilter.__init__(self, glos)
		self._termSet: set[str] = set()

	def run(self, entry: EntryType) -> EntryType | None:
		if entry.isData():
			return entry

		termSet = self._termSet
		term = entry.s_term

		if term not in termSet:
			termSet.add(term)
			return entry

		n = 2
		while f"{term} ({n})" in termSet:
			n += 1
		term = f"{term} ({n})"

		termSet.add(term)
		entry._term = term  # type: ignore
		# use entry.editFuncTerm?

		return entry


class SkipEntriesWithDuplicateHeadword(EntryFilter):
	name = "skip_duplicate_headword"
	desc = "Skip entries with a duplicate headword (first term)"

	def __init__(self, glos: _GlossaryType) -> None:
		EntryFilter.__init__(self, glos)
		self._wset: set[str] = set()

	def run(self, entry: EntryType) -> EntryType | None:
		term = entry.l_term[0]
		if term in self._wset:
			return None
		self._wset.add(term)
		return entry


class TrimArabicDiacritics(EntryFilter):
	name = "trim_arabic_diacritics"
	desc = "Trim Arabic diacritics from headword (first term)"

	def __init__(self, glos: _GlossaryType) -> None:
		EntryFilter.__init__(self, glos)
		self._pat = re.compile("[\u064b-\u065f]")

	def run(self, entry: EntryType) -> EntryType | None:
		terms = list(entry.l_term)
		hw = terms[0]
		hw_t = self._pat.sub("", hw)
		hw_t = hw_t.replace("\u0622", "\u0627").replace("\u0623", "\u0627")
		if hw_t == hw or not hw_t:
			return entry
		entry._term = [hw_t, *terms]  # type: ignore
		return entry


class UnescapeTermLinks(EntryFilter):
	name = "unescape_word_links"  # used in config, do not change
	desc = "Unescape Term/Entry Links"

	def __init__(self, glos: _GlossaryType) -> None:
		from .html_utils import unescape_unicode

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


class ShowMaxMemoryUsage(EntryFilter):
	name = "max_memory_usage"
	desc = "Show Max Memory Usage"
	MAX_TERM_LEN = 30

	def __init__(self, glos: _GlossaryType) -> None:
		import os

		import psutil

		EntryFilter.__init__(self, glos)
		self._process = psutil.Process(os.getpid())
		self._max_mem_usage = 0

	def run(self, entry: EntryType) -> EntryType | None:
		usage = self._process.memory_info().rss // 1024
		if usage > self._max_mem_usage:
			self._max_mem_usage = usage
			term = entry.s_term
			if len(term) > self.MAX_TERM_LEN:
				term = term[: self.MAX_TERM_LEN - 3] + "..."
			core.trace(log, f"MaxMemUsage: {usage:,}, {term=}")
		return entry


entryFiltersRules = [
	(None, True, TrimWhitespaces),
	(None, True, NonEmptyTermFilter),
	("skip_resources", False, SkipDataEntry),
	("utf8_check", False, FixUnicode),
	("lower", False, LowerTerm),
	("skip_duplicate_headword", False, SkipEntriesWithDuplicateHeadword),
	("trim_arabic_diacritics", False, TrimArabicDiacritics),
	("rtl", False, RTLDefi),
	("remove_html_all", False, RemoveHtmlTagsAll),
	("remove_html", "", RemoveHtmlTags),
	("normalize_html", False, NormalizeHtml),
	("unescape_word_links", False, UnescapeTermLinks),
	(None, True, LanguageCleanup),
	# -------------------------------------
	# TODO
	# ("text_list_symbol_cleanup", False, TextListSymbolCleanup),
	# -------------------------------------
	(None, True, NonEmptyTermFilter),
	(None, True, NonEmptyDefiFilter),
	(None, True, RemoveEmptyAndDuplicateAltTerms),
	# -------------------------------------
	# filters that are enabled by plugins using glossary methods:
	(None, False, PreventDuplicateTerms),
	(None, False, StripFullHtml),
	# -------------------------------------
	# filters are added conditionally (other than with config or glossary methods):
	(None, False, ShowMaxMemoryUsage),
]
