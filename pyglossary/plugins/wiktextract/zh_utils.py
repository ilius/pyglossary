"""
Wiktextract Chinese-language parsing utilities.

Provides helpers for normalizing Wiktextract Chinese headwords, readings, and
sense text during import. Used by the Wiktextract reader for zh-specific fields.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from collections.abc import Iterable, Sequence
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

# class ExampleDict(TypedDict):
# #type: str
# text: list[str]
# Translation: NotRequired[str]
# English: NotRequired[str]


def _firstTag(
	tags: Sequence[str],
	options: Iterable[str],
	default: str = "",
) -> str:
	for tag in tags:
		if tag in options:
			return tag
	return default


def _exampleTranslation(example: dict[str, Any]) -> tuple[str, str]:
	# Only English for now, but other languages should use different keys
	if "english" in example:
		return "English", example["english"]
	return "Translation", ""


def _exampleText(example: dict[str, Any], tags: Sequence[str]) -> str:
	langText = _firstTag(tags, LANGS)
	writingSystem = _firstTag(tags, WRITTING_SYSTEMS)
	writingSystemText = WRITTING_SYSTEMS.get(writingSystem, "")

	text = example.get("text", "")
	if not (langText or writingSystemText):
		return text
	separator = ", " if langText and writingSystemText else ""
	return f"{text} ({langText}{separator}{writingSystemText})"


def _addExample(
	tempExamples: dict[tuple[str, str], dict[str, Any]],
	skippedExamples: list[dict[str, Any]],
	example: dict[str, Any],
) -> None:
	# there are "tags" and "raw_tags" which contain language
	# and writing system info. Usually there are 2 entries for
	# traditional and simplified characters.
	# the word is consider the same if both "roman" and translation is the same

	tags = example.get("tags", []) + example.get("raw_tags", [])
	targetLang, translationText = _exampleTranslation(example)

	if not tags and not translationText:
		# Nothing to process, simply copy this example
		skippedExamples.append(example)
		return

	romanText = example.get("roman", "")
	romanSystemText = _firstTag(tags, PHON_SYSTEMS, "Romanization")
	text = _exampleText(example, tags)

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


def processExamples(exampleList: list[dict[str, Any]]) -> list[dict[str, Any]]:
	skippedExamples: list[dict[str, Any]] = []

	# {translation+phonetic: {script1: str, script2: str, ...}}
	tempExamples: dict[tuple[str, str], dict[str, Any]] = {}
	for example in exampleList:
		_addExample(tempExamples, skippedExamples, example)

	return list(tempExamples.values()) + skippedExamples


def _processSense(sense: dict[str, Any]) -> dict[str, Any]:
	if "examples" in sense:
		sense["examples"] = processExamples(sense["examples"])
	return sense

	# Add other sense-related fix here later.


def processSenses(senseList: list[dict[str, Any]]) -> list[dict[str, Any]] | None:
	if not senseList:
		return None
	return [_processSense(s) for s in senseList]


# {"lang":{"dialect": {"system": ["phonatic"]}}}

# key 'tags' contains:
#   - language ["Mandarin"]
#   - phonetic writing system ["Pinyin", "bopomofo"]
#   - dialect of each language ["standard", "Chendu", "Xi'an"]
#
# Since the order is random, the grouping is assess only by
# Language and phonetic writing system for simplicity
# Otherwise the string will be interpreted as dialect/place name
# Note that many item in data["sounds"] are not extracted properly
# in the first place, so only correctly extracted one will be rendered

# might need for adding more languages in the future
# data from wiktextract does not provide the grouping
# NORTHERN_MIN: Sequence[str] = ("Jian'ou",)  # noqa: F841
# EASTERN_MIN: Sequence[str] = ("Fuzhou",)  # noqa: F841
# SOUTHERN_MIN: Sequence[str] = ("Hokkien", "Teochew", "Leizhou")  # noqa: F841

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


def _processSound(
	sound: dict[str, Any],
) -> tuple[str, str, str, str] | None:
	tags = sound.get("tags")
	if not tags:
		return None

	langText = _firstTag(tags, LANGS)
	if not langText:
		return None

	phonSystem = [t for t in tags if t in PHON_SYSTEMS]
	if not phonSystem:
		phonSystem.append(DEFAULT_PS.get(langText, ""))
	phonSystemText = ", ".join(PREFERRED_PS_NAME.get(p, p) for p in phonSystem)

	dialectText = ", ".join(t for t in tags if t != langText and t not in phonSystem)

	# Few entries from wiktionary e.g.,「鿦」　have non-unicode text string
	# i.e., "uie\x06". This seem to be an error from wiktionary side.
	phonText = sound.get("zh-pron", "") + sound.get("ipa", "")
	if not phonText or phonText == "uie\x06":
		return None

	return langText, dialectText, phonSystemText, phonText


def _addSound(
	processedSounds: dict[str, Any],
	langText: str,
	dialectText: str,
	phonSystemText: str,
	phonText: str,
) -> None:
	langSounds = processedSounds.setdefault(langText, {})
	dialectSounds = langSounds.setdefault(dialectText, {})
	phonTexts = dialectSounds.setdefault(phonSystemText, [])
	phonTexts.append(phonText)


def processSoundList(soundList: list[dict[str, Any]]) -> dict[str, Any]:
	processedSounds: dict[str, Any] = {}

	for sound in soundList:
		processed = _processSound(sound)
		if processed is None:
			continue
		_addSound(processedSounds, *processed)

	return processedSounds


def processChinese(data: dict[str, Any]) -> dict[str, Any]:
	if "sounds" in data:
		data["sounds"] = processSoundList(data["sounds"])
	if "senses" in data:
		data["senses"] = processSenses(data["senses"])
	return data
