# -*- coding: utf-8 -*-
# ruff: noqa: ARG005, C417, E501, E721, I001, PYI024, RET504
# Parsing logic adapted from dictcc-stardict (MIT License)
# https://github.com/Linus789/dictcc-stardict/blob/main/convert.py
# Copyright (c) dictcc-stardict contributors

from __future__ import annotations

from collections import namedtuple
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	import pyparsing as pyparsing_module
	from typing import Any

__all__ = ["FieldParser", "SourceWord", "get_language_pair"]

_OPTIONAL_ABBREVIATIONS: dict[str, dict[str, dict[str, set[str]]]] = {
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


@dataclass
class _SourceWordsBuilder:
	possible_abbreviations: dict[str, set[str]]
	last_word_index: int | None
	source_words: set[str] | None = None
	finished_words: set[str] = field(default_factory=set)
	already_encountered_word: bool = False


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

	def _get_optional_abbreviations(
		self,
		lang: str,
		word_class: str | None,
	) -> dict[str, set[str]]:
		lang_abbreviations = _OPTIONAL_ABBREVIATIONS.get(lang, {})
		possible_abbreviations = {
			where: set(values)
			for where, values in lang_abbreviations.get("any", {}).items()
		}
		for where, values in lang_abbreviations.get(word_class, {}).items():
			if where in possible_abbreviations:
				possible_abbreviations[where].update(values)
			else:
				possible_abbreviations[where] = set(values)

		start_or_end = possible_abbreviations.pop("start_or_end", None)
		if start_or_end is not None:
			possible_abbreviations.setdefault("start", set()).update(start_or_end)
			possible_abbreviations.setdefault("end", set()).update(start_or_end)

		return possible_abbreviations

	def _last_word_index(self, tokens: Any) -> int | None:
		last_word_index = None
		for index, token in enumerate(tokens):
			if type(token) == self.word:
				last_word_index = index
		return last_word_index

	def _add_word(self, source_words: set[str] | None, value: str) -> set[str]:
		if source_words is None:
			return {value}
		return {f"{word} {value}" for word in source_words}

	def _add_optional_word(
		self,
		source_words: set[str] | None,
		value: str,
	) -> set[str]:
		return self._add_word(source_words, value) | {value, ""}

	def _add_word_variant(
		self,
		source_words: set[str] | None,
		value: str,
	) -> set[str]:
		words = self._add_word(source_words, value)
		if source_words is None:
			words.add("")
		else:
			words |= source_words
		return words

	def _handle_abbreviation_token(
		self,
		builder: _SourceWordsBuilder,
		token: Any,
		index: int,
	) -> bool:
		possible_abbreviations = builder.possible_abbreviations
		if index == builder.last_word_index and token.value in possible_abbreviations.get(
			"end",
			set(),
		):
			if builder.source_words is not None:
				builder.finished_words |= builder.source_words
			builder.source_words = self._add_word(builder.source_words, token.value)
			builder.already_encountered_word = True
			return True

		if (
			not builder.already_encountered_word
			and token.value in possible_abbreviations.get("start", set())
		):
			builder.source_words = self._add_optional_word(
				builder.source_words,
				token.value,
			)
			builder.already_encountered_word = True
			return True

		return False

	def _get_source_words(
		self,
		field_value: str,
		possible_abbreviations: dict[str, set[str]],
		make_abbreviations_optional: bool,
	) -> set[str]:
		tokens = self.parse_tokens(field_value)
		builder = _SourceWordsBuilder(
			possible_abbreviations=possible_abbreviations,
			last_word_index=self._last_word_index(tokens),
		)

		for index, token in enumerate(tokens):
			if (
				make_abbreviations_optional
				and possible_abbreviations
				and type(token) == self.word
				and self._handle_abbreviation_token(builder, token, index)
			):
				continue

			if type(token) == self.word:
				builder.source_words = self._add_word(
					builder.source_words,
					token.value,
				)
				builder.already_encountered_word = True
			elif type(token) == self.round:
				builder.source_words = self._add_word_variant(
					builder.source_words,
					token.value,
				)

		return {
			stripped
			for word in (builder.source_words or set()) | builder.finished_words
			if (stripped := " ".join(word.split()))
		}

	def _expand_abbreviations_in_word(
		self,
		word: str,
		replacements_for_lang: dict[str, set[str]],
		find_abbreviations_expr: Any,
	) -> set[SourceWord]:
		split_word = find_abbreviations_expr.parse_string(word)
		build_words: set[SourceWord] | None = None

		for sub_word in split_word:
			if type(sub_word) != self.abbreviation:
				if build_words is None:
					build_words = {SourceWord(sub_word, False)}
				else:
					for build_word in build_words:
						build_word.word = f"{build_word.word}{sub_word}"
				continue

			current_replacements = [
				*(
					(replacement, True)
					for replacement in replacements_for_lang[sub_word.value]
				),
				(sub_word.value, False),
			]

			if build_words is None:
				build_words = {
					SourceWord(replacement, is_replacement)
					for replacement, is_replacement in current_replacements
				}
				continue

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

		return build_words or set()

	def _replace_abbreviations(
		self,
		source_words: set[str],
		lang: str,
	) -> set[SourceWord]:
		replacements_for_lang = self.abbreviations_synonyms[lang]
		find_abbreviations_expr = self.find_abbreviations_exprs[lang]
		return_words: set[SourceWord] = set()

		for word in source_words:
			return_words.update(
				self._expand_abbreviations_in_word(
					word,
					replacements_for_lang,
					find_abbreviations_expr,
				),
			)

		for word in return_words:
			word.word = " ".join(word.word.split())

		return return_words

	def get_possible_source_words(  # noqa: PLR0913
		self,
		field_value: str,
		word_class: str | None,
		lang: str,
		make_abbreviations_optional: bool = True,
		replace_abbreviations: bool = True,
		as_str: bool = False,
	) -> set[str] | set[SourceWord]:
		possible_abbreviations = (
			self._get_optional_abbreviations(lang, word_class)
			if make_abbreviations_optional
			else {}
		)
		source_words = self._get_source_words(
			field_value,
			possible_abbreviations,
			make_abbreviations_optional,
		)

		if replace_abbreviations and lang in self.find_abbreviations_exprs:
			return_words = self._replace_abbreviations(source_words, lang)
		else:
			return_words = {SourceWord(word, False) for word in source_words}

		return {word.word if as_str else word for word in return_words if word.word}
