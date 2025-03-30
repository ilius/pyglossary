# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any


def processSoundList(
    soundList: dict[str, Any]
) -> dict[str, Any]:
    # {"lang":{"dialect": {"system": ["phonatic"]}}}
    # "_" = not found

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

    LANGS: tuple[str] = (
        "Mandarin", "Cantonese", "Gan",
        "Hakka", "Jin", "Hokkien",
        "Teochew", "Leizhou", "Xiang",
        "Jian'ou", "Fuzhou", "Puxian-Min",
        "Southern-Pinghua", "Wu",
        "Middle-Chinese", "Old-Chinese")

    # might need to adding more languages in the future
    # data from wiktextract does not provide the groupping
    NORTHERN_MIN: tuple[str] = ("Jian'ou")  # noqa:F841
    EASTERN_MIN: tuple[str] = ("Fuzhou")  # noqa:F841
    SOUTHERN_MIN: tuple[str] = ("Hokkien", "Teochew", "Leizhou")  # noqa:F841

    PHON_SYSTEMS: tuple[str] = (
        "Pinyin", "Hanyu-Pinyin", "bopomofo", "Cyrillic",
        "Tongyong-Pinyin", "Wade-Giles", "Yale",
        "Gwoyeu-Romatsyh", "Palladius", "Latinxua-Sin-Wenz",
        "Guangdong", "Guangdong-Romanization",
        "Kienning-Colloquial-Romanized",
        "Jyutping", "Wiktionary-specific", "Phak-fa-su", "PFS",
        "Hakka-Romanization-System", "Hagfa-Pinyim",
        "POJ", "Peng'im", "Sinological-IPA", "Foochow-Romanized",
        "Tai-lo", "Phofsit-Daibuun",
        "Zhengzhang", "Baxter-Sagart"
    )

    # it seem like readings without specified phonetic system have default
    # however, i'm not so sure and the list here is based purely on
    # wiktionary page of the character「我」
    DEFAULT_PS = {
        "Mandarin": "Pinyin",
        "Cantonese": "Jyutping",
        "Hakka": "Hakka Romanization System"
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
        "Sinological-IPA": "ipa"
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
        if not phonSystemText:
            phonSystemText = "_"

        dialect = [t for t in tags if t != langText and t not in phonSystem]
        dialectText = ", ".join(dialect)
        if not dialectText:
            dialectText = "_"

        phonText = sound.get("zh-pron", "") + sound.get("ipa", "")
        if not phonText:
            return None

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
    # TODO
    return data
