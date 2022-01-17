# -*- coding: utf-8 -*-

import re
import logging

from .text_utils import (
	fixUtf8,
)

from .entry_base import BaseEntry


log = logging.getLogger("pyglossary")


class EntryFilter(object):
	name = ""
	desc = ""

	def __init__(self, glos: "GlossaryType"):
		self.glos = glos

	def prepare(self) -> None:
		"""
			run this after glossary info is set and ready
		"""
		pass

	def run(self, entry: BaseEntry) -> "Optional[BaseEntry]":
		"""
			returns an Entry object, or None to skip
				may return the same `entry`,
				or modify and return it,
				or return a new Entry object
		"""
		return entry


class StripWhitespaces(EntryFilter):
	name = "strip"
	desc = "Strip whitespaces in word(s) and definition"

	def run(self, entry: BaseEntry) -> "Optional[BaseEntry]":
		entry.strip()
		entry.replace("\r", "")
		return entry


class NonEmptyWordFilter(EntryFilter):
	name = "non_empty_word"
	desc = "Skip entries with empty word"

	def run(self, entry: BaseEntry) -> "Optional[BaseEntry]":
		if not entry.s_word:
			return
		return entry


class NonEmptyDefiFilter(EntryFilter):
	name = "non_empty_defi"
	desc = "Skip entries with empty definition"

	def run(self, entry: BaseEntry) -> "Optional[BaseEntry]":
		if not entry.defi:
			return
		return entry


class RemoveEmptyAndDuplicateAltWords(EntryFilter):
	name = "remove_empty_dup_alt_words"
	desc = "Remove empty and duplicate alternate words"

	def run(self, entry: BaseEntry) -> "Optional[BaseEntry]":
		entry.removeEmptyAndDuplicateAltWords()
		if not entry.l_word:
			return
		return entry


class FixUnicode(EntryFilter):
	name = "utf8_check"
	desc = "Fix Unicode in word(s) and definition"

	def run(self, entry: BaseEntry) -> "Optional[BaseEntry]":
		entry.editFuncWord(fixUtf8)
		entry.editFuncDefi(fixUtf8)
		return entry


class LowerWord(EntryFilter):
	name = "lower"
	desc = "Lowercase word(s)"

	def __init__(self, glos: "GlossaryType"):
		EntryFilter.__init__(self, glos)
		self._re_word_ref = re.compile('href=["\'](bword://[^"\']+)["\']')

	def lowerWordRefs(self, defi):
		return self._re_word_ref.sub(
			lambda m: m.group(0).lower(),
			defi,
		)

	def run(self, entry: BaseEntry) -> "Optional[BaseEntry]":
		entry.editFuncWord(str.lower)
		entry.editFuncDefi(self.lowerWordRefs)
		return entry


class RTLDefi(EntryFilter):
	name = "rtl"
	desc = "Make definition right-to-left"

	def run(self, entry: BaseEntry) -> "Optional[BaseEntry]":
		entry.editFuncDefi(lambda defi: f'<div dir="rtl">{defi}</div>')
		return entry


class RemoveHtmlTagsAll(EntryFilter):
	name = "remove_html_all"
	desc = "Remove all HTML tags from definition"

	def __init__(self, glos: "GlossaryType"):
		self._p_pattern = re.compile(
			'<p( [^<>]*?)?>(.*?)</p>',
			re.DOTALL,
		)
		self._br_pattern = re.compile(
			"<br[ /]*>",
			re.IGNORECASE,
		)

	def run(self, entry: BaseEntry) -> "Optional[BaseEntry]":
		from bs4 import BeautifulSoup

		def fixStr(st: str) -> str:
			st = self._p_pattern.sub("\\2\n", st)
			# if there is </p> left without opening, replace with <br>
			st = st.replace("</p>", "\n")
			st = self._br_pattern.sub("\n", st)
			return BeautifulSoup(st, "lxml").text

		entry.editFuncDefi(fixStr)
		return entry


class RemoveHtmlTags(EntryFilter):
	name = "remove_html"
	desc = "Remove specific HTML tags from definition"

	def __init__(self, glos: "GlossaryType", tagsStr: str):
		import re
		tags = tagsStr.split(",")
		self.glos = glos
		self.tags = tags
		tagsRE = "|".join(self.tags)
		self.pattern = re.compile(f"</?({tagsRE})( [^>]*)?>")

	def run(self, entry: BaseEntry) -> "Optional[BaseEntry]":
		def fixStr(st: str) -> str:
			return self.pattern.sub("", st)

		entry.editFuncDefi(fixStr)
		return entry


# FIXME: It's is not safe to lowercases everything between < and >
# including class name, element ids/names, scripts, <a href="bword://..."> 
# etc. How can we fix that?
class NormalizeHtml(EntryFilter):
	name = "normalize_html"
	desc = "Normalize HTML tags in definition (WIP)"

	def __init__(self, glos: "GlossaryType"):
		log.info("Normalizing HTML tags")
		self._pattern = re.compile(
			"(" + "|".join([
				fr"</?{tag}[^<>]*?>"
				for tag in (
					"a", "font", "i", "b", "u", "p", "sup",
					"div", "span",
					"table", "tr", "th", "td",
					"ul", "ol", "li",
					"img",
					"br", "hr",
				)
			]) + ")",
			re.S | re.I,
		)

	def _subLower(self, m) -> str:
		return m.group(0).lower()

	def _fixDefi(self, st: str) -> str:
		st = self._pattern.sub(self._subLower, st)
		return st

	def run(self, entry: BaseEntry) -> "Optional[BaseEntry]":
		entry.editFuncDefi(self._fixDefi)
		return entry


class SkipDataEntry(EntryFilter):
	name = "skip_resources"
	desc = "Skip resources / data files"

	def run(self, entry: BaseEntry) -> "Optional[BaseEntry]":
		if entry.isData():
			return
		return entry


class LanguageCleanup(EntryFilter):
	name = "lang"
	desc = "Language-specific cleanup/fixes"

	def __init__(self, glos: "GlossaryType"):
		EntryFilter.__init__(self, glos)
		self._run_func = None  # type: Callable[[BaseEntry], [Optional[BaseEntry]]]

	def prepare(self) -> None:
		langCodes = {
			lang.code
			for lang in (self.glos.sourceLang, self.glos.targetLang)
			if lang is not None
		}
		if "fa" in langCodes:
			self._run_func = self.run_fa
			log.info("Using Persian filter")

	def run_fa(self, entry: BaseEntry) -> "Optional[BaseEntry]":
		from pyglossary.persian_utils import faEditStr
		entry.editFuncWord(faEditStr)
		entry.editFuncDefi(faEditStr)
		# RLM = "\xe2\x80\x8f"
		# defi = "\n".join([RLM+line for line in defi.split("\n")])
		# for GoldenDict ^^ FIXME
		return entry

	def run(self, entry: BaseEntry) -> "Optional[BaseEntry]":
		if self._run_func:
			entry = self._run_func(entry)
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
		if st.endswith("<p"):
			st = st[:-2]
		st = st.strip()
		if st.endswith(","):
			st = st[:-1]

		return st

	def run(self, entry: BaseEntry) -> "Optional[BaseEntry]":
		entry.editFuncDefi(self.cleanDefi)
		return entry


class PreventDuplicateWords(EntryFilter):
	name = "prevent_duplicate_words"
	desc = "Prevent duplicate words"

	def __init__(self, glos: "GlossaryType"):
		EntryFilter.__init__(self, glos)
		self._wordSet = set()

	def run(self, entry: BaseEntry) -> "Optional[BaseEntry]":
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
		entry._word = word
		# use entry.editFuncWord?

		return entry


class ShowProgressBar(EntryFilter):
	name = "progressbar"
	desc = "Progress Bar"

	def __init__(self, glos: "GlossaryType"):
		EntryFilter.__init__(self, glos)
		self._wordCount = -1
		self._wordCountThreshold = 0
		self._lastPos = 0
		self._index = 0

	def run(self, entry: BaseEntry) -> "Optional[BaseEntry]":
		index = self._index
		self._index = index + 1

		if entry is not None:
			bp = entry.byteProgress()
			if bp:
				if bp[0] > self._lastPos + 20000:
					self.glos.progress(bp[0], bp[1], unit="bytes")
					self._lastPos = bp[0]
				return entry

		if self._wordCount == -1:
			self._wordCount = len(self.glos)
			self._wordCountThreshold = max(1, min(
				500,
				self._wordCount // 200,
			))

		if self._wordCount > 1:
			if index % self._wordCountThreshold == 0:
				self.glos.progress(index, self._wordCount)

		return entry


class ShowMaxMemoryUsage(EntryFilter):
	name = "max_memory_usage"
	desc = "Show Max Memory Usage"

	def __init__(self, glos: "GlossaryType"):
		EntryFilter.__init__(self, glos)
		self._max_mem_usage = 0

	def run(self, entry: BaseEntry) -> "Optional[BaseEntry]":
		import os
		import psutil
		usage = psutil.Process(os.getpid()).memory_info().rss // 1024
		if usage > self._max_mem_usage:
			self._max_mem_usage = usage
			word = entry.s_word
			if len(word) > 30:
				word = word[:37] + "..."
			log.trace(f"MaxMemUsage: {usage}, word={word}")
		return entry
