# -*- coding: utf-8 -*-

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3
# as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License <http://www.gnu.org/licenses/gpl-3.0.txt>
# for more details.
#
# Copyright (C) 2023 Saeed Rasooli
# Copyright (C) 2015 Igor Tkach
#
# This plugin is based on https://github.com/itkach/wordnet2slob

import os
import re
import sys
from collections import defaultdict
from typing import TYPE_CHECKING, Iterator

from pyglossary.core import log

if TYPE_CHECKING:
	from pyglossary.glossary_types import EntryType, GlossaryType
	from pyglossary.option import Option

enable = True
lname = "wordnet"
format = "Wordnet"
description = "WordNet"
extensions = ()
extensionCreate = ""
kind = "directory"
wiki = "https://en.wikipedia.org/wiki/WordNet"
website = (
	"https://wordnet.princeton.edu/",
	"WordNet - A Lexical Database for English",
)

# key is option/argument name, value is instance of Option
optionsProp: "dict[str, Option]" = {}

# original expression from
# http://stackoverflow.com/questions/694344/regular-expression-that-matches-between-quotes-containing-escaped-quotes
# "(?:[^\\"]+|\\.)*"
# some examples don't have closing quote which
# make the subn with this expression hang
# quotedTextPattern = re.compile(r'"(?:[^"]+|\.)*["|\n]')

# make it a capturing group so that we can get rid of quotes
quotedTextPattern = re.compile(r'"([^"]+)"')

refPattern = re.compile(r"`(\w+)'")

class SynSet:
	def __init__(self, line) -> None:
		self.line = line
		if isinstance(line, bytes):
			line = line.decode("utf-8")
		meta, self.gloss = line.split("|")
		self.meta_parts = meta.split()

	@property
	def offset(self):
		return int(self.meta_parts[0])

	@property
	def lex_filenum(self):
		return self.meta_parts[1]

	@property
	def ss_type(self):
		return self.meta_parts[2]

	@property
	def w_cnt(self):
		return int(self.meta_parts[3], 16)

	@property
	def words(self):
		return [self.meta_parts[4 + 2 * i].replace("_", " ") for i in range(self.w_cnt)]

	@property
	def pointers(self):
		p_cnt_index = 4 + 2 * self.w_cnt
		p_cnt = self.meta_parts[p_cnt_index]
		pointer_count = int(p_cnt)
		start = p_cnt_index + 1
		return [
			Pointer(*self.meta_parts[start + i * 4 : start + (i + 1) * 4])
			for i in range(pointer_count)
		]

	def __repr__(self) -> str:
		return "SynSet(%r)" % self.line


class PointerSymbols:
	n = {
		"!": "Antonyms",
		"@": "Hypernyms",
		"@i": "Instance hypernyms",
		"~": "Hyponyms",
		"~i": "Instance hyponyms",
		"#m": "Member holonyms",
		"#s": "Substance holonyms",
		"#p": "Part holonyms",
		"%m": "Member meronyms",
		"%s": "Substance meronyms",
		"%p": "Part meronyms",
		"=": "Attributes",
		"+": "Derivationally related forms",
		";c": "Domain of synset - TOPIC",
		"-c": "Member of this domain - TOPIC",
		";r": "Domain of synset - REGION",
		"-r": "Member of this domain - REGION",
		";u": "Domain of synset - USAGE",
		"-u": "Member of this domain - USAGE",
		"^": "Also see",
	}

	v = {
		"!": "Antonyms",
		"@": "Hypernyms",
		"~": "Hyponyms",
		"*": "Entailments",
		">": "Cause",
		"^": "Also see",
		"$": "Verb group",
		"+": "Derivationally related forms",
		";c": "Domain of synset - TOPIC",
		";r": "Domain of synset - REGION",
		";u": "Domain of synset - USAGE",
	}

	a = s = {
		"!": "Antonyms",
		"+": "Derivationally related forms",
		"&": "Similar to",
		"<": "Participle of verb",
		"\\": "Pertainyms",
		"=": "Attributes",
		"^": "Also see",
		";c": "Domain of synset - TOPIC",
		";r": "Domain of synset - REGION",
		";u": "Domain of synset - USAGE",
	}

	r = {
		"!": "Antonyms",
		"\\": "Derived from adjective",
		"+": "Derivationally related forms",
		";c": "Domain of synset - TOPIC",
		";r": "Domain of synset - REGION",
		";u": "Domain of synset - USAGE",
		"^": "Also see",
	}


class Pointer:
	def __init__(self, symbol, offset, pos, source_target) -> None:
		self.symbol = symbol
		self.offset = int(offset)
		self.pos = pos
		self.source_target = source_target
		self.source = int(source_target[:2], 16)
		self.target = int(source_target[2:], 16)

	def __repr__(self) -> str:
		return (
			f"Pointer({self.symbol!r}, {self.offset!r}, "
			f"{self.pos!r}, {self.source_target!r})"
		)


class WordNet:
	article_template = (
		"<h1>%s</h1><span>%s</span>"
	)
	synSetTypes = {
		"n": "n.",
		"v": "v.",
		"a": "adj.",
		"s": "adj. satellite",
		"r": "adv.",
	}

	file2pos = {
		"data.adj": ["a", "s"],
		"data.adv": ["r"],
		"data.noun": ["n"],
		"data.verb": ["v"],
	}

	def __init__(self, wordnetdir) -> None:
		self.wordnetdir = wordnetdir
		self.collector: "dict[str, list[str]]" = defaultdict(list)

	def iterlines(self, dict_dir):
		for name in os.listdir(dict_dir):
			if not name.startswith("data."):
				continue
			with open(os.path.join(dict_dir, name)) as f:
				for line in f:
					if not line.startswith("  "):
						yield line

	def prepare(self):
		synSetTypes = self.synSetTypes
		file2pos = self.file2pos

		dict_dir = self.wordnetdir

		files = {}
		for name in os.listdir(dict_dir):
			if name.startswith("data.") and name in file2pos:
				f = open(os.path.join(dict_dir, name))  # noqa: SIM115
				for key in file2pos[name]:
					files[key] = f

		def a(word):
			return f'<a href="{word}">{word}</a>'

		for i, line in enumerate(self.iterlines(dict_dir)):
			if i % 100 == 0 and i > 0:
				sys.stdout.write(".")
				sys.stdout.flush()
			if i % 5000 == 0 and i > 0:
				sys.stdout.write("\n")
				sys.stdout.flush()
			if not line or not line.strip():
				continue
			synset = SynSet(line)
			gloss_with_examples, _ = quotedTextPattern.subn(
				lambda x: '<cite class="ex">%s</cite>' % x.group(1), synset.gloss,
			)
			gloss_with_examples, _ = refPattern.subn(
				lambda x: a(x.group(1)), gloss_with_examples,
			)

			words = synset.words
			for i, word in enumerate(words):
				synonyms = [w for w in words if w != word]
				synonyms_str = (
					'<br/><small class="co">Synonyms:</small> %s'
					% ", ".join(a(w) for w in synonyms)
					if synonyms
					else ""
				)
				pointers = defaultdict(list)
				for pointer in synset.pointers:
					if pointer.source and pointer.target and pointer.source - 1 != i:
						continue
					symbol = pointer.symbol
					if symbol and symbol[:1] in (";", "-"):
						continue
					try:
						symbol_desc = getattr(PointerSymbols, synset.ss_type)[symbol]
					except KeyError:
						print(
							f"WARNING: unknown pointer symbol {symbol}"
							f" for {synset.ss_type} ",
						)
						symbol_desc = symbol

					data_file = files[pointer.pos]
					data_file.seek(pointer.offset)
					referenced_synset = SynSet(data_file.readline())
					if pointer.source == pointer.target == 0:
						pointers[symbol_desc] = [
							w for w in referenced_synset.words if w not in words
						]
					else:
						referenced_word = referenced_synset.words[pointer.target - 1]
						if referenced_word not in pointers[symbol_desc]:
							pointers[symbol_desc].append(referenced_word)

				pointers_str = ""
				for symbol_desc, referenced_words in pointers.items():
					if referenced_words:
						pointers_str += (
							'<br/><small class="co">%s:</small> ' % symbol_desc
						)
						pointers_str += ", ".join(a(w) for w in referenced_words)
				self.collector[word].append(
					f'<i class="pos grammar">{synSetTypes[synset.ss_type]}</i>'
					f' {gloss_with_examples}{synonyms_str}{pointers_str}',
				)
		sys.stdout.write("\n")
		sys.stdout.flush()

	def process(self) -> "Iterator[tuple[str, str]]":
		article_template = self.article_template

		for title in self.collector:
			article_pieces = self.collector[title]
			article_pieces_count = len(article_pieces)
			text = None
			if article_pieces_count > 1:
				ol = (
					["<ol>"] + ["<li>%s</li>" % ap for ap in article_pieces] + ["</ol>"]
				)
				text = article_template % (title, "".join(ol))
			elif article_pieces_count == 1:
				text = article_template % (title, article_pieces[0])

			if text:
				yield title, text


class Reader:
	def __init__(self, glos: "GlossaryType") -> None:
		self._glos = glos
		self._filename = ""
		self._wordCount = 0
		self.wordnet: "WordNet | None" = None

	def __len__(self) -> int:
		return self._wordCount

	def open(self, filename: str) -> None:
		self.wordnet = WordNet(filename)
		log.info("Running wordnet.prepare()")
		self.wordnet.prepare()

		# TODO: metadata

	def close(self) -> None:
		self.wordnet = None

	def __iter__(self) -> "Iterator[EntryType]":
		if self.wordnet is None:
			raise ValueError("self.wordnet is None")
		glos = self._glos
		for word, defi in self.wordnet.process():
			yield glos.newEntry(word, defi)
