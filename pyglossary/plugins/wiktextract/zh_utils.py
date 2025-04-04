# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from collections.abc import Sequence
	from typing import Any

__all__ = ["processChinese"]

LANGS: Sequence[str] = (
	"Mandarin",
	"MSC",
	"Cantonese",
	"Gan",
	"Hakka",
	"Jin",
	"Hokkien",
	"Shanghainese",
	"Teochew",
	"Leizhou",
	"Xiang",
	"Jian'ou",
	"Fuzhou",
	"Puxian-Min",
	"Southern-Pinghua",
	"Wu",
	"Middle-Chinese",
	"Old-Chinese",
)

PHON_SYSTEMS: Sequence[str] = (
	"Pinyin",
	"Hanyu-Pinyin",
	"bopomofo",
	"Cyrillic",
	"Tongyong-Pinyin",
	"Wade-Giles",
	"Yale",
	"Gwoyeu-Romatsyh",
	"Palladius",
	"Latinxua-Sin-Wenz",
	"Guangdong",
	"Guangdong-Romanization",
	"Kienning-Colloquial-Romanized",
	"Wugniu",
	"Jyutping",
	"Wiktionary-specific",
	"Phak-fa-su",
	"PFS",
	"Hakka-Romanization-System",
	"Hagfa-Pinyim",
	"POJ",
	"Peng'im",
	"Sinological-IPA",
	"Foochow-Romanized",
	"Tai-lo",
	"Phofsit-Daibuun",
	"Zhengzhang",
	"Baxter-Sagart",
)

WRITTING_SYSTEMS: dict[str, str] = {
	"Traditional Chinese": "trad.",
	"Simplified Chinese": "simp.",
}


def processSenses(senseList: dict[str, Any]) -> list[dict[str, Any]] | None:
	if not senseList:
		return None

	def processExamples(exampleList: list[dict[str, Any]]) -> list[dict[str, Any]]:
		# there are "tags" and "raw_tags" which contain language
		# and writting system info. Usually there are 2 entries for
		# traditional and simplified characters.
		# the word is consider the same if both "roman" and translation is the same

		skippedExamples = []

		# {translation+phonetic: {script1: str, script2: str, ...}}
		tempExamples = {}
		for example in exampleList:
			tags = example.get("tags", []) + example.get("raw_tags", [])

			targetLang = "Translation"
			translationText = ""

			# Only English for now, but other languages should use different keys
			for _lang in ["english"]:
				if _lang in example:
					translationText = example[_lang]
					targetLang = _lang.capitalize()

			if not tags and not translationText:
				# Nothing to process, simply copy this example
				skippedExamples.append(example)
				continue

			lang = [t for t in tags if t in LANGS]
			langText = lang[0] if lang else ""

			romanSystem = [t for t in tags if t in PHON_SYSTEMS]
			romanSystemText = romanSystem[0] if romanSystem else "Romanization"

			writtingSystem = [
				WRITTING_SYSTEMS[t] for t in tags if t in WRITTING_SYSTEMS
			]
			writtingSystemText = writtingSystem[0] if writtingSystem else ""

			romanText = example.get("roman", "")

			text = example.get("text", "")
			if langText or writtingSystemText:
				separator = ", " if langText and writtingSystemText else ""
				text += f" ({langText}{separator}{writtingSystemText})"

			key = (translationText, romanText)

			if key not in tempExamples:
				tempExamples[key] = {
					"type": "example",
					"text": [],
					targetLang: translationText,
				}
			tempExamples[key]["text"].append(text)
			if romanText:
				tempExamples[key][romanSystemText] = romanText

		return list(tempExamples.values()) + skippedExamples

	def processSense(sense: dict[str, Any]) -> dict[str, Any]:
		if "examples" in sense:
			sense["examples"] = processExamples(sense["examples"])
		return sense

		# Add other sense-related fix here later.

	return [processSense(s) for s in senseList]


def processSoundList(soundList: list[dict[str, Any]]) -> dict[str, Any]:
	# {"lang":{"dialect": {"system": ["phonatic"]}}}

	# key 'tags' contains:
	#   - language ["Mandarin"]
	#   - phonetic writting system ["Pinyin", "bopomofo"]
	#   - dialag of each langauge ["standard", "Chendu", "Xi'an"]
	#
	# Since the order is random, the groupping is assess only by
	# Language and phonetic writting system for simplicity
	# Otherwise the string will be interpreted as dialect/place name
	# Note that many item in data["sounds"] are not extracted properly
	# in the first place, so only correctly extracted one will be rendered

	# might need to adding more languages in the future
	# data from wiktextract does not provide the groupping
	NORTHERN_MIN: Sequence[str] = ("Jian'ou",)  # noqa:F841
	EASTERN_MIN: Sequence[str] = ("Fuzhou",)  # noqa:F841
	SOUTHERN_MIN: Sequence[str] = ("Hokkien", "Teochew", "Leizhou")  # noqa:F841

	# it seem like readings without specified phonetic system have default
	# however, i'm not so sure and the list here is based purely on
	# wiktionary page of the character「我」
	DEFAULT_PS = {
		"Mandarin": "Pinyin",
		"Cantonese": "Jyutping",
		"Hakka": "Hakka Romanization System",
	}

	PREFERRED_PS_NAME = {
		"Hanyu-Pinyin": "Pinyin",
		"Latinxua-Sin-Wenz": "Scuanxua Ladinxua Xin Wenz",
		"Gwoyeu-Romatsyh": "Gwoyeu Romatsyh",
		"Kienning-Colloquial-Romanized": "Kienning Colloquial Romanized",
		"Foochow-Romanized": "Bàng-uâ-cê",
		"Tai-lo": "Tâi-lô",
		"Phofsit-Daibuun": "Phofsit Daibuun",
		"PFS": "Pha̍k-fa-sṳ",
		"Hakka-Romanization-System": "Hakka Romanization System",
		"Guangdong-Romanization": "Guangdong",
		"Wiktionary-specific": "Wiktionary",
		"Sinological-IPA": "IPA",
		"bopomofo": "Bopomofo",
	}

	processedSounds = {}

	for sound in soundList:
		tags = sound.get("tags")
		if not tags:
			continue

		lang = [t for t in tags if t in LANGS]
		if not lang:
			continue
		langText = lang[0]

		phonSystem = [t for t in tags if t in PHON_SYSTEMS]
		if not phonSystem:
			phonSystem.append(DEFAULT_PS.get(langText, ""))
		phonSystemText = ", ".join(PREFERRED_PS_NAME.get(p, p) for p in phonSystem)

		dialect = [t for t in tags if t != langText and t not in phonSystem]
		dialectText = ", ".join(dialect)

		# Few entries from wiktionary e.g.,「鿦」　have non-unicode text string
		# i.e., "uie\x06". This seem to be an error from wiktionary side.
		phonText = sound.get("zh-pron", "") + sound.get("ipa", "")
		if not phonText or phonText == "uie\x06":
			continue

		if langText not in processedSounds:
			processedSounds[langText] = {dialectText: {phonSystemText: [phonText]}}
			continue
		if dialectText not in processedSounds[langText]:
			processedSounds[langText][dialectText] = {phonSystemText: [phonText]}
			continue
		if phonSystemText not in processedSounds[langText][dialectText]:
			processedSounds[langText][dialectText][phonSystemText] = [phonText]
			continue
		processedSounds[langText][dialectText][phonSystemText].append(phonText)

	return processedSounds


def processChinese(data: dict[str, Any]) -> dict[str, Any]:
	if "sounds" in data:
		data["sounds"] = processSoundList(data["sounds"])
	if "senses" in data:
		data["senses"] = processSenses(data["senses"])
	return data
