# -*- coding: utf-8 -*-

import re

from typing import (
	Optional,
	List,
)

from .text_utils import (
	fixUtf8,
)

from .entry_base import BaseEntry
from .glossary import Glossary



class EntryFilter(object):
	name = ""
	desc = ""

	def __init__(self, glos: Glossary):
		self.glos = glos

	def run(self, entry: BaseEntry) -> Optional[BaseEntry]:
		"""
			returns an Entry object, or None to skip
				may return the same `entry`,
				or modify and return it,
				or return a new Entry object
		"""
		return entry


class StripEntryFilter(EntryFilter):
	name = "strip"
	desc = "Strip Whitespaces"

	def run(self, entry: BaseEntry) -> Optional[BaseEntry]:
		entry.strip()
		entry.replace("\r", "")
		return entry


class NonEmptyWordFilter(EntryFilter):
	name = "non_empty_word"
	desc = "Non-empty Words"

	def run(self, entry: BaseEntry) -> Optional[BaseEntry]:
		if not entry.getWord():
			return
#		words = entry.getWords()
#		if not words:
#			return
#		wordsStr = "".join([w.strip() for w in words])
#		if not wordsStr:
#			return
		return entry


class NonEmptyDefiFilter(EntryFilter):
	name = "non_empty_defi"
	desc = "Non-empty Definition"

	def run(self, entry: BaseEntry) -> Optional[BaseEntry]:
		if not entry.getDefi():
			return
		return entry


class RemoveEmptyAndDuplicateAltWords(EntryFilter):
	name = "remove_empty_dup_alt_words"
	desc = "Remove Empty and Duplicate Alternate Words"

	def run(self, entry: BaseEntry) -> Optional[BaseEntry]:
		entry.removeEmptyAndDuplicateAltWords()
		if not entry.getWords():
			return
		return entry


class FixUnicodeFilter(EntryFilter):
	name = "fix_unicode"
	desc = "Fix Unicode"

	def run(self, entry: BaseEntry) -> Optional[BaseEntry]:
		entry.editFuncWord(fixUtf8)
		entry.editFuncDefi(fixUtf8)
		return entry


class LowerWordFilter(EntryFilter):
	name = "lower_word"
	desc = "Lowercase Words"

	def run(self, entry: BaseEntry) -> Optional[BaseEntry]:
		entry.editFuncWord(str.lower)
		return entry


class RemoveHtmlTagsAll(EntryFilter):
	name = "remove_html_all"

	def run(self, entry: BaseEntry) -> Optional[BaseEntry]:
		from bs4 import BeautifulSoup

		def fixStr(st: str) -> str:
			return BeautifulSoup(st, "lxml").text

		entry.editFuncDefi(fixStr)
		return entry


class RemoveHtmlTags(EntryFilter):
	name = "remove_html"

	def __init__(self, glos: Glossary, tags: List[str]):
		self.glos = glos
		self.tags = tags

	def run(self, entry: BaseEntry) -> Optional[BaseEntry]:
		import re

		def fixStr(st: str) -> str:
			tagsRE = "|".join(self.tags)
			pattern = f"<.?({tagsRE})[^>]*>"
			st = re.sub(pattern, "", st)
			return st

		entry.editFuncDefi(fixStr)
		return entry


class SkipDataEntryFilter(EntryFilter):
	name = "skip_resources"
	desc = "Skip Resources"

	def run(self, entry: BaseEntry) -> Optional[BaseEntry]:
		if entry.isData():
			return
		return entry


class LangEntryFilter(EntryFilter):
	name = "lang"
	desc = "Language-dependent Filters"

	def run_fa(self, entry: BaseEntry) -> Optional[BaseEntry]:
		from pyglossary.persian_utils import faEditStr
		entry.editFuncWord(faEditStr)
		entry.editFuncDefi(faEditStr)
		# RLM = "\xe2\x80\x8f"
		# defi = "\n".join([RLM+line for line in defi.split("\n")])
		# for GoldenDict ^^ FIXME
		return entry

	def run(self, entry: BaseEntry) -> Optional[BaseEntry]:
		langs = (
			self.glos.getInfo("sourceLang") +
			self.glos.getInfo("targetLang")
		).lower()
		if "persian" in langs or "farsi" in langs:
			entry = self.run_fa(entry)

		return entry


class CleanEntryFilter(EntryFilter):  # FIXME
	name = "clean"
	desc = "Clean"

	def cleanDefi(self, st: str) -> str:
		st = st.replace("♦  ", "♦ ")
		st = re.sub("[\r\n]+", "\n", st)
		st = re.sub(" *\n *", "\n", st)

		"""
		This code may correct snippets like:
		- First sentence .Second sentence. -> First sentence. Second sentence.
		- First clause ,second clause. -> First clause, second clause.
		But there are cases when this code have undesirable effects
		( "<" represented as "&lt;" in HTML markup):
		- <Adj.> -> < Adj. >
		- <fig.> -> < fig. >
		"""
		"""
		for j in range(3):
			for ch in ",.;":
				st = replacePostSpaceChar(st, ch)
		"""

		st = re.sub("♦\n+♦", "♦", st)
		if st.endswith("<p"):
			st = st[:-2]
		st = st.strip()
		if st.endswith(","):
			st = st[:-1]

		return st

	def run(self, entry: BaseEntry) -> Optional[BaseEntry]:
		entry.editFuncDefi(self.cleanDefi)
		return entry
