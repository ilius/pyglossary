"""
FreeDict TEI import utility functions.

Provides language detection, writing-system helpers, and shared formatting
helpers for FreeDict ``.tei`` sources. Used by the FreeDict readers during TEI
conversion.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pyglossary.core import log
from pyglossary.langs import langDict
from pyglossary.langs.writing_system import getWritingSystemFromText

if TYPE_CHECKING:
	from pyglossary.stubs.lxml_types import Element


__all__ = [
	"XMLLANG",
	"getLangDesc",
	"getTitleTag",
	"isRTL",
	"tostring",
]


XMLLANG = "{http://www.w3.org/XML/1998/namespace}lang"


def tostring(elem: Element) -> str:
	from lxml import etree as ET

	return (
		ET.tostring(
			elem,
			method="html",
			pretty_print=True,
		)
		.decode("utf-8")
		.strip()
	)


def getTitleTag(sample: str) -> str:
	ws = getWritingSystemFromText(sample)
	if ws:
		return ws.titleTag
	return "b"


def isRTL(elem: Element) -> bool:
	lang = elem.get(XMLLANG)
	if lang is None:
		return False
	langObj = langDict[lang]
	if langObj is None:
		log.warning(f"unknown language {lang}")
		return False
	return bool(langObj.rtl)


def getLangDesc(elem: Element) -> str | None:
	lang = elem.attrib.get(XMLLANG)
	if lang:
		langObj = langDict[lang]
		if not langObj:
			log.warning(f"unknown lang {lang!r} in {tostring(elem)}")
			return None
		return langObj.name

	orig = elem.attrib.get("orig")
	if orig:
		return orig

	log.warning(f"unknown lang name in {tostring(elem)}")
	return None
