# -*- coding: utf-8 -*-
# ruff: noqa: ARG005, C417, E501, E721, I001, PYI024, RET504
# Parsing logic adapted from dictcc-stardict (MIT License)
# https://github.com/Linus789/dictcc-stardict/blob/main/convert.py
# Copyright (c) dictcc-stardict contributors

from __future__ import annotations

from collections import namedtuple
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	import pyparsing as pyparsing_module
	from typing import Any


def get_language_pair(input_file: str) -> str:
	with open(input_file, encoding="utf-8") as fp:
		line = fp.readline()
	return line.removeprefix("#").strip().split()[0].lower()


@dataclass(eq=False)
class SourceWord:
	word: str
	has_replacements: bool

	def __hash__(self) -> int:
		return hash(self.word)

	def __eq__(self, other: object) -> bool:
		if not isinstance(other, SourceWord):
			return NotImplemented
		return self.word == other.word


class FieldParser:
	def __init__(self) -> None:
		import pyparsing as pp

		self._init_line_parser(pp)
		self._init_replace_abbreviations(pp)

	def _init_line_parser(self, pp: pyparsing_module) -> None:
		loc_marker = pp.Empty().set_parse_action(
			lambda string, location, tokens: location,
		)
		endloc_marker = loc_marker.copy()
		endloc_marker.callPreparse = False

		Round = self.round = namedtuple("Round", ["value"])
		round_ = pp.Forward()
		round_ << loc_marker("start") + pp.Suppress("(") + pp.ZeroOrMore(
			round_ | pp.CharsNotIn(")", exact=1),
		) + pp.Suppress(")") + endloc_marker("end")
		round_.setParseAction(
			lambda string, location, tokens: Round(
				value=string[tokens.start + 1 : tokens.end - 1]
			),
		)

		Square = self.square = namedtuple("Square", ["value"])
		square = pp.Forward()
		square << loc_marker("start") + pp.Suppress("[") + pp.ZeroOrMore(
			square | pp.CharsNotIn("]", exact=1),
		) + pp.Suppress("]") + endloc_marker("end")
		square.setParseAction(
			lambda string, location, tokens: Square(
				value=string[tokens.start + 1 : tokens.end - 1]
			),
		)

		Curly = self.curly = namedtuple("Curly", ["value"])
		curly = pp.Forward()
		curly << loc_marker("start") + pp.Suppress("{") + pp.ZeroOrMore(
			curly | pp.CharsNotIn("}", exact=1),
		) + pp.Suppress("}") + endloc_marker("end")
		curly.setParseAction(
			lambda string, location, tokens: Curly(
				value=string[tokens.start + 1 : tokens.end - 1]
			),
		)

		Angle = self.angle = namedtuple("Angle", ["value"])
		angle = pp.Forward()
		angle << loc_marker("start") + pp.Suppress("<") + pp.ZeroOrMore(
			angle | pp.CharsNotIn(">", exact=1),
		) + pp.Suppress(">") + endloc_marker("end")
		angle.setParseAction(
			lambda string, location, tokens: Angle(
				value=string[tokens.start + 1 : tokens.end - 1]
			),
		)

		Word = self.word = namedtuple("Word", ["value"])
		word = loc_marker("start") + pp.CharsNotIn(" ([{<") + endloc_marker("end")
		word.set_parse_action(
			lambda string, location, tokens: Word(
				value=string[tokens.start : tokens.end]
			),
		)

		brackets = round_ | square | curly | angle
		self.expr = pp.ZeroOrMore(word | brackets | pp.Suppress(pp.Word(" ")))

	def _init_replace_abbreviations(self, pp: pyparsing_module) -> None:
		self.abbreviations_synonyms = {
			"en": {
				"sth.": {"something"},
				"sb.": {"somebody"},
				"sb.'s": {"somebody's"},
				"sb./sth.": {"somebody", "something", "somebody/something"},
			},
			"de": {
				"jd.": {"jemand"},
				"jds.": {"jemandes"},
				"jdm.": {"jemandem"},
				"jdn.": {"jemanden"},
				"etw.": {"etwas"},
				"jd./etw.": {"jemand", "etwas", "jemand/etwas"},
				"jds./etw.": {"jemandes", "etwas", "jemandes/etwas"},
				"jdm./etw.": {"jemandem", "etwas", "jemandem/etwas"},
				"jdn./etw.": {"jemanden", "etwas", "jemanden/etwas"},
			},
		}

		self.find_abbreviations_exprs = {}

		Abbreviation = self.abbreviation = namedtuple("Abbreviation", ["value"])
		loc_marker = pp.Empty().set_parse_action(
			lambda string, location, tokens: location,
		)
		endloc_marker = loc_marker.copy()
		endloc_marker.callPreparse = False

		for lang, abbreviation_replacements in self.abbreviations_synonyms.items():
			abbreviations = list(abbreviation_replacements.keys())

			if not abbreviations:
				continue

			find_expr = (
				pp.WordStart()
				+ loc_marker("start")
				+ pp.Literal(
					abbreviations[0],
				)
				+ pp.WordEnd()
				+ endloc_marker("end")
			)

			for other_abbreviation in abbreviations[1:]:
				find_expr = find_expr | (
					pp.WordStart()
					+ loc_marker("start")
					+ pp.Literal(other_abbreviation)
					+ pp.WordEnd()
					+ endloc_marker("end")
				)

			find_expr.set_parse_action(
				lambda string, location, tokens: Abbreviation(
					value=string[tokens.start : tokens.end],
				),
			)
			find_expr = pp.ZeroOrMore(find_expr | pp.CharsNotIn("", exact=1))
			find_expr.leave_whitespace()

			self.find_abbreviations_exprs[lang] = find_expr

	def parse_tokens(self, s: str) -> Any:
		return self.expr.parse_string(s)

	def get_possible_source_words(  # noqa: PLR0912, PLR0913
		self,
		field: str,
		word_class: str | None,
		lang: str,
		make_abbreviations_optional: bool = True,
		replace_abbreviations: bool = True,
		as_str: bool = False,
	) -> set[str] | set[SourceWord]:
		if make_abbreviations_optional:
			optional_abbreviations = {
				"en": {
					"any": {"start_or_end": {"sth.", "sb.", "sb.'s", "sb./sth."}},
					"verb": {"start": {"to"}},
				},
				"de": {
					"any": {
						"start_or_end": {
							"jd.",
							"jds.",
							"jdm.",
							"jdn.",
							"etw.",
							"jd./etw.",
							"jds./etw.",
							"jdm./etw.",
							"jdn./etw.",
						},
					},
				},
			}

			lang_abbreviations = optional_abbreviations.get(lang, {})
			possible_abbreviations = dict(lang_abbreviations.get("any", {}))

			for where, values in lang_abbreviations.get(word_class, {}).items():
				if where in possible_abbreviations:
					possible_abbreviations[where].update(values)
				else:
					possible_abbreviations[where] = values

			if "start_or_end" in possible_abbreviations:
				start_or_end_abbreviations = possible_abbreviations.pop("start_or_end")

				if "start" in possible_abbreviations:
					possible_abbreviations["start"].update(start_or_end_abbreviations)
				else:
					possible_abbreviations["start"] = start_or_end_abbreviations

				if "end" in possible_abbreviations:
					possible_abbreviations["end"].update(start_or_end_abbreviations)
				else:
					possible_abbreviations["end"] = start_or_end_abbreviations
		else:
			possible_abbreviations = {}

		tokens = self.parse_tokens(field)
		source_words: set[str] | None = None
		finished_words: set[str] = set()
		already_encountered_word = False
		try:
			last_word_index = [
				i for i, token in enumerate(tokens) if type(token) == self.word
			][-1]
		except IndexError:
			last_word_index = None

		for index, token in enumerate(tokens):
			if (
				make_abbreviations_optional
				and possible_abbreviations
				and type(token) == self.word
			):
				if index == last_word_index and token.value in possible_abbreviations.get(
					"end",
					set(),
				):
					if source_words is None:
						source_words = {token.value}
					else:
						finished_words |= set(source_words)
						source_words = {f"{word} {token.value}" for word in source_words}

					already_encountered_word = True
					continue

				if (
					not already_encountered_word
					and token.value
					in possible_abbreviations.get(
						"start",
						set(),
					)
				):
					if source_words is None:
						source_words = {token.value, ""}
					else:
						source_words = {
							f"{word} {token.value}" for word in source_words
						} | {
							token.value,
							"",
						}

					already_encountered_word = True
					continue

			if type(token) == self.word:
				if source_words is None:
					source_words = {token.value}
				else:
					source_words = {f"{word} {token.value}" for word in source_words}

				already_encountered_word = True
			elif type(token) == self.round:
				if source_words is None:
					source_words = {token.value, ""}
				else:
					source_words |= {f"{word} {token.value}" for word in source_words}

		if source_words is None:
			source_words = set()

		return_words: set[SourceWord] = set()
		source_words = {
			stripped
			for word in (source_words | finished_words)
			if (stripped := " ".join(word.split()))
		}

		if replace_abbreviations and lang in self.find_abbreviations_exprs:
			replacements_for_lang = self.abbreviations_synonyms[lang]
			find_abbreviations_expr = self.find_abbreviations_exprs[lang]

			for word in source_words:
				split_word = find_abbreviations_expr.parse_string(word)
				build_words: set[SourceWord] | None = None

				for sub_word in split_word:
					if type(sub_word) != self.abbreviation:
						if build_words is None:
							build_words = {SourceWord(sub_word, False)}
						else:
							for build_word in build_words:
								build_word.word = f"{build_word.word}{sub_word}"
					else:
						current_replacements = list(
							map(
								lambda x: (x, True), replacements_for_lang[sub_word.value]
							),
						) + [(sub_word.value, False)]

						if build_words is None:
							build_words = {
								SourceWord(replacement, is_replacement)
								for replacement, is_replacement in current_replacements
							}
						else:
							old_build_words = set(build_words)
							build_words.clear()

							for build_word in old_build_words:
								for replacement, is_replacement in current_replacements:
									build_words.add(
										SourceWord(
											f"{build_word.word}{replacement}",
											build_word.has_replacements or is_replacement,
										),
									)

				if build_words is not None:
					return_words.update(build_words)

			for word in return_words:
				word.word = " ".join(word.word.split())
		else:
			return_words = {SourceWord(word, False) for word in source_words}

		result = {word.word if as_str else word for word in return_words if word.word}
		return result
