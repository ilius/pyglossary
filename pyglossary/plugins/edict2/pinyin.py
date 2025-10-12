# coding=utf-8
# based on https://github.com/zkoch/CEDICT_Parser

from __future__ import annotations

__all__ = ["convert"]

_TONES = {
	"a1": "ā",
	"a2": "á",
	"a3": "ǎ",
	"a4": "à",
	"e1": "ē",
	"e2": "é",
	"e3": "ě",
	"e4": "è",
	"i1": "ī",
	"i2": "í",
	"i3": "ǐ",
	"i4": "ì",
	"o1": "ō",
	"o2": "ó",
	"o3": "ǒ",
	"o4": "ò",
	"u1": "ū",
	"u2": "ú",
	"u3": "ǔ",
	"u4": "ù",
	"ü1": "ǖ",
	"ü2": "ǘ",
	"ü3": "ǚ",
	"ü4": "ǜ",
}

_VOWELS = ("a", "e", "o", "iu", "ui", "i", "u", "ü")


def convert(word: str) -> tuple[str, str]:
	tone = word[-1]
	pinyin = word[:-1].lower()

	if tone == "5":
		return pinyin, tone
	if tone not in {"1", "2", "3", "4"}:
		return word, ""

	for vowel in _VOWELS:
		if vowel in pinyin:
			vowel1 = vowel[-1]
			return pinyin.replace(vowel1, _TONES[vowel1 + tone]), tone

	return pinyin, tone
