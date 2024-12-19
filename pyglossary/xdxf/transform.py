from __future__ import annotations

import logging
from io import BytesIO
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
	from pyglossary.lxml_types import Element, T_htmlfile


log = logging.getLogger("pyglossary")

__all__ = [
	"XdxfTransformer",
]


class XdxfTransformer:
	_gram_color: str = "green"
	_example_padding: int = 10

	def __init__(self, encoding: str = "utf-8") -> None:
		self._encoding = encoding
		self._childTagWriteMapping = {
			"br": self._write_br,
			"u": self._write_basic_format,
			"i": self._write_basic_format,
			"b": self._write_basic_format,
			"sub": self._write_basic_format,
			"sup": self._write_basic_format,
			"tt": self._write_basic_format,
			"big": self._write_basic_format,
			"small": self._write_basic_format,
			"blockquote": self._write_blockquote,
			"tr": self._write_tr,
			"k": self._write_k,
			"sr": self._write_sr,
			"ex": self._write_example,
			"mrkd": self._write_mrkd,
			"kref": self._write_kref,
			"iref": self._write_iref,
			"pos": self._write_pos,
			"abr": self._write_abr,
			"dtrn": self._write_dtrn,
			"co": self._write_co,
			"c": self._write_c,
			"rref": self._write_rref,
			"def": self._write_def,
			"deftext": self._write_deftext,
			"span": self._write_span,
			"abbr_def": self._write_abbr_def,
			"gr": self._write_gr,
			"ex_orig": self._write_ex_orig,
			"categ": self._write_categ,
			"opt": self._write_opt,
			"img": self._write_img,
			"abbr": self._write_abbr,
			"etm": self._write_etm,
		}

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
	def hasPrevText(prev: str | Element | None) -> bool:
		if isinstance(prev, str):
			return True
		if prev is None:
			return False
		if prev.tag == "k":
			return False
		if prev.tag in {
			"dtrn",
			"def",
			"span",
			"co",
			"i",
			"b",
			"sub",
			"sup",
			"tt",
			"big",
			"small",
		}:
			return True
		if prev.text:  # noqa: SIM103
			return True
		# print(prev)
		return False

	def writeString(  # noqa: PLR0913
		self,
		hf: T_htmlfile,
		child: str,
		parent: Element,
		prev: str | Element | None,
		stringSep: str | None = None,
	) -> None:
		from lxml import etree as ET

		def addSep() -> None:
			if stringSep is None:
				hf.write(ET.Element("br"))
			else:
				hf.write(stringSep)

		hasPrev = self.hasPrevText(prev)
		trail = False
		if parent.tag in {"ar", "font"}:
			if child.startswith("\n"):
				child = child.lstrip("\n")
				if hasPrev:
					hf.write(ET.Element("br"))
			elif child.endswith("\n"):
				child = child.rstrip("\n")
				trail = True
			if not hasPrev:
				child = child.lstrip()
		elif child.startswith("\n"):
			child = child.lstrip()
			if hasPrev:
				addSep()

		child = child.rstrip()
		lines = [line for line in child.split("\n") if line]
		for index, line in enumerate(lines):
			if index > 0:
				# and line[0] not in ".,;)"
				addSep()
			hf.write(line)
		if trail:
			addSep()

	def _write_example(self, hf: T_htmlfile, elem: Element) -> None:
		children = elem.xpath("child::node()")
		if not children:
			return
		if not isinstance(children, list):
			log.warning(f"unexpected {children=}")
			return
		prev = None
		stringSep = " "
		with hf.element(
			"div",
			attrib={
				"class": "example",
				"style": f"padding: {self._example_padding}px 0px;",
			},
		):
			for child in children:
				if isinstance(child, str):
					# if not child.strip():
					# 	continue
					self.writeString(hf, child, elem, prev, stringSep=stringSep)
					continue
				if isinstance(child, bytes | tuple):
					# TODO
					log.warning(f"unexpected {child=}")
					continue
				if not child:
					continue
				if child.tag == "iref":
					with hf.element("div"):
						self._write_iref(hf, child)  # NESTED 5
					continue
				if child.tag in {"ex_orig", "ex_tran"}:
					with hf.element("div"):
						self.writeChildrenOf(hf, child, stringSep=stringSep)  # NESTED 5
					continue
				# log.warning(f"unknown tag {child.tag} inside <ex>")
				self.writeChild(hf, child, elem, prev, stringSep=stringSep)
				prev = child

	def _write_iref(self, hf: T_htmlfile, child: Element) -> None:
		iref_url = child.attrib.get("href", "")
		if iref_url.endswith((".mp3", ".wav", ".aac", ".ogg")):
			#  with hf.element("audio", src=iref_url):
			with hf.element(
				"a",
				attrib={
					"class": "iref",
					"href": iref_url,
				},
			):
				hf.write("🔊")
			return

		with hf.element(
			"a",
			attrib={
				"class": "iref",
				"href": child.attrib.get("href", child.text or ""),
			},
		):
			self.writeChildrenOf(hf, child, stringSep=" ")

	def _write_blockquote(self, hf: T_htmlfile, child: Element) -> None:
		with hf.element("div", attrib={"class": "m"}):
			self.writeChildrenOf(hf, child)

	def _write_tr(self, hf: T_htmlfile, child: Element) -> None:
		from lxml import etree as ET

		hf.write("[")
		self.writeChildrenOf(hf, child)
		hf.write("]")
		hf.write(ET.Element("br"))

	def _write_k(self, hf: T_htmlfile, child: Element) -> None:
		with hf.element("div", attrib={"class": child.tag}):
			# with hf.element(glos.titleTag(child.text)):
			# ^ no glos object here!
			with hf.element("b"):
				self.writeChildrenOf(hf, child)

	def _write_mrkd(self, hf: T_htmlfile, child: Element) -> None:  # noqa: PLR6301
		if not child.text:
			return
		with hf.element("span", attrib={"class": child.tag}):
			with hf.element("b"):
				hf.write(child.text)

	def _write_kref(self, hf: T_htmlfile, child: Element) -> None:
		if not child.text:
			log.warning(f"kref with no text: {self.tostring(child)}")
			return
		with hf.element(
			"a",
			attrib={
				"class": "kref",
				"href": f"bword://{child.attrib.get('k', child.text)}",
			},
		):
			hf.write(child.text)

	def _write_sr(self, hf: T_htmlfile, child: Element) -> None:
		with hf.element("div", attrib={"class": child.tag}):
			self.writeChildrenOf(hf, child)

	def _write_pos(self, hf: T_htmlfile, child: Element) -> None:
		with hf.element("span", attrib={"class": child.tag}):
			with hf.element("font", color="green"):
				with hf.element("i"):
					self.writeChildrenOf(hf, child)  # NESTED 5

	def _write_abr(self, hf: T_htmlfile, child: Element) -> None:
		with hf.element("span", attrib={"class": child.tag}):
			with hf.element("font", color="green"):
				with hf.element("i"):
					self.writeChildrenOf(hf, child)  # NESTED 5

	def _write_dtrn(self, hf: T_htmlfile, child: Element) -> None:
		self.writeChildrenOf(hf, child, sep=" ")

	def _write_co(self, hf: T_htmlfile, child: Element) -> None:
		self.writeChildrenOf(hf, child, sep=" ")

	def _write_basic_format(self, hf: T_htmlfile, child: Element) -> None:
		with hf.element(child.tag):
			self.writeChildrenOf(hf, child)
			# if child.text is not None:
			# 	hf.write(child.text.strip("\n"))

	def _write_br(self, hf: T_htmlfile, child: Element) -> None:
		from lxml import etree as ET

		hf.write(ET.Element("br"))
		self.writeChildrenOf(hf, child)

	def _write_c(self, hf: T_htmlfile, child: Element) -> None:
		color = child.attrib.get("c", "green")
		with hf.element("font", color=color):
			self.writeChildrenOf(hf, child)

	def _write_rref(self, _hf: T_htmlfile, child: Element) -> None:
		if not child.text:
			log.warning(f"rref with no text: {self.tostring(child)}")
			return

	def _write_def(self, hf: T_htmlfile, child: Element) -> None:
		# TODO: create a list (ol / ul) unless it has one item only
		# like FreeDict reader
		with hf.element("div"):
			self.writeChildrenOf(hf, child)

	def _write_deftext(self, hf: T_htmlfile, child: Element) -> None:
		self.writeChildrenOf(hf, child, stringSep=" ", sep=" ")

	def _write_span(self, hf: T_htmlfile, child: Element) -> None:
		with hf.element("span"):
			self.writeChildrenOf(hf, child)

	def _write_abbr_def(self, hf: T_htmlfile, child: Element) -> None:
		# _type = child.attrib.get("type", "")
		# {"": "", "grm": "grammatical", "stl": "stylistical",
		#  "knl": "area/field of knowledge", "aux": "subsidiary"
		#  "oth": "others"}[_type]
		self.writeChildrenOf(hf, child)

	def _write_gr(self, hf: T_htmlfile, child: Element) -> None:
		from lxml import etree as ET

		with hf.element("font", color=self._gram_color):
			hf.write(child.text or "")
		hf.write(ET.Element("br"))

	def _write_ex_orig(self, hf: T_htmlfile, child: Element) -> None:
		with hf.element("i"):
			self.writeChildrenOf(hf, child)

	# def _write_ex_transl(self, hf: T_htmlfile, child: Element) -> None:

	def _write_categ(self, hf: T_htmlfile, child: Element) -> None:
		with hf.element("span", style="background-color: green;"):
			self.writeChildrenOf(hf, child, stringSep=" ")

	def _write_opt(self, hf: T_htmlfile, child: Element) -> None:  # noqa: PLR6301
		if child.text:
			hf.write(" (")
			hf.write(child.text)
			hf.write(")")

	def _write_img(self, hf: T_htmlfile, child: Element) -> None:  # noqa: PLR6301
		with hf.element("img", attrib=dict(child.attrib)):
			pass

	def _write_abbr(self, hf: T_htmlfile, child: Element) -> None:  # noqa: PLR6301
		# FIXME: may need an space or newline before it
		with hf.element("i"):
			hf.write(child.text or "")

	def _write_etm(self, hf: T_htmlfile, child: Element) -> None:  # noqa: PLR6301
		# Etymology (history and origin)
		# TODO: formatting?
		hf.write(child.text or "")

	def writeChildElem(  # noqa: PLR0913
		self,
		hf: T_htmlfile,
		child: Element,
		parent: Element,  # noqa: ARG002
		prev: str | Element | None,
		stringSep: str | None = None,  # noqa: ARG002
	) -> None:
		func = self._childTagWriteMapping.get(child.tag, None)
		if func is not None:
			func(hf, child)
			return

		if child.tag == "ex_transl" and prev is not None:
			if isinstance(prev, str):
				pass
			elif prev.tag == "ex_orig":
				if child.text != prev.text:
					with hf.element("i"):
						self.writeChildrenOf(hf, child)
				return

		log.warning(f"unknown tag {child.tag}")
		self.writeChildrenOf(hf, child)

	def writeChild(  # noqa: PLR0913
		self,
		hf: T_htmlfile,
		child: str | Element,
		parent: Element,
		prev: str | Element | None,
		stringSep: str | None = None,
	) -> None:
		if isinstance(child, str):
			if not child.strip():
				return
			self.writeString(hf, child, parent, prev, stringSep=stringSep)
			return
		self.writeChildElem(
			hf=hf,
			child=child,
			parent=parent,
			prev=prev,
			stringSep=stringSep,
		)

	def shouldAddSep(  # noqa: PLR6301
		self,
		child: str | Element,
		prev: str | Element,
	) -> bool:
		if isinstance(child, str):
			return not (len(child) > 0 and child[0] in ".,;)")

		if child.tag in {"sub", "sup"}:
			return False

		if isinstance(prev, str):
			pass
		elif prev.tag in {"sub", "sup"}:
			return False

		return True

	def writeChildrenOf(
		self,
		hf: T_htmlfile,
		elem: Element,
		sep: str | None = None,
		stringSep: str | None = None,
	) -> None:
		children = elem.xpath("child::node()")
		if not children:
			return
		if not isinstance(children, list):
			log.warning(f"unexpceted {children=}")
			return
		prev = None
		for child in children:
			if sep and prev is not None and self.shouldAddSep(child, prev):
				hf.write(sep)
			if isinstance(child, bytes | tuple):
				log.warning(f"unexpected {child=}")
				continue
			self.writeChild(hf, child, elem, prev, stringSep=stringSep)
			prev = child

	def transform(self, article: Element) -> str:
		from lxml import etree as ET

		# encoding = self._encoding
		f = BytesIO()
		with ET.htmlfile(f, encoding="utf-8") as hf:
			with hf.element("div", attrib={"class": "article"}):
				self.writeChildrenOf(cast("T_htmlfile", hf), article)

		text = f.getvalue().decode("utf-8")
		text = text.replace("<br>", "<br/>")  # for compatibility
		return text  # noqa: RET504

	def transformByInnerString(self, articleInnerStr: str) -> str:
		from lxml import etree as ET

		return self.transform(
			ET.fromstring(f"<ar>{articleInnerStr}</ar>"),
		)
