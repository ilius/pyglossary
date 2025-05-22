# -*- coding: utf-8 -*-
from __future__ import annotations

from pyglossary.flags import ALWAYS
from pyglossary.option import (
	BoolOption,
	IntOption,
	Option,
	StrOption,
)

from .reader import Reader
from .writer import Writer

__all__ = [
	"Reader",
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
