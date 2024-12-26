# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from collections.abc import Callable
	from typing import Any

	from pyglossary.lxml_types import Element, T_htmlfile


from pyglossary.core import log
from pyglossary.langs import langDict
from pyglossary.langs.writing_system import getWritingSystemFromText

__all__ = ["XMLLANG", "ReaderUtils"]


XMLLANG = "{http://www.w3.org/XML/1998/namespace}lang"


class ReaderUtils:
	@staticmethod
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

	@staticmethod
	def makeList(  # noqa: PLR0913
		hf: T_htmlfile,
		input_objects: list[Any],
		processor: Callable,
		single_prefix: str = "",
		skip_single: bool = True,
		ordered: bool = True,
		list_type: str = "",
	) -> None:
		"""Wrap elements into <ol> if more than one element."""
		if not input_objects:
			return

		if skip_single and len(input_objects) == 1:
			if single_prefix:
				hf.write(single_prefix)
			processor(hf, input_objects[0])
			return

		attrib: dict[str, str] = {}
		if list_type:
			attrib["type"] = list_type

		with hf.element("ol" if ordered else "ul", attrib=attrib):
			for el in input_objects:
				with hf.element("li"):
					processor(hf, el)

	@staticmethod
	def getTitleTag(sample: str) -> str:
		ws = getWritingSystemFromText(sample)
		if ws:
			return ws.titleTag
		return "b"

	@staticmethod
	def isRTL(elem: Element) -> bool:
		lang = elem.get(XMLLANG)
		if lang is None:
			return False
		langObj = langDict[lang]
		if langObj is None:
			log.warning(f"unknown language {lang}")
			return False
		return bool(langObj.rtl)

	@classmethod
	def getLangDesc(cls, elem: Element) -> str | None:
		lang = elem.attrib.get(XMLLANG)
		if lang:
			langObj = langDict[lang]
			if not langObj:
				log.warning(f"unknown lang {lang!r} in {cls.tostring(elem)}")
				return None
			return langObj.name

		orig = elem.attrib.get("orig")
		if orig:
			return orig

		log.warning(f"unknown lang name in {cls.tostring(elem)}")
		return None

	@classmethod
	def writeLangTag(
		cls,
		hf: T_htmlfile,
		elem: Element,
	) -> None:
		langDesc = cls.getLangDesc(elem)
		if not langDesc:
			return
		# TODO: make it Italic or change font color?
		if elem.text:
			hf.write(f"{langDesc}: {elem.text}")
		else:
			hf.write(f"{langDesc}")  # noqa: FURB183
