import logging
from io import BytesIO
from os.path import join
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
	from typing import Union

	from lxml.etree import _Element as Element
	from lxml.etree import _XSLTResultTree

	from pyglossary.lxml_type import T_htmlfile

from pyglossary import core
from pyglossary.core import rootDir

log = logging.getLogger("pyglossary")


class XslXdxfTransformer(object):
	_gram_color: str = "green"
	_example_padding: int = 10

	def __init__(self, encoding: str = "utf-8") -> None:
		try:
			from lxml import etree as ET
		except ModuleNotFoundError as e:
			e.msg += f", run `{core.pip} install lxml` to install"
			raise e

		with open(join(rootDir, "pyglossary", "xdxf.xsl"), "r") as f:
			xslt_txt = f.read()

		xslt = ET.XML(xslt_txt)
		self._transform = ET.XSLT(xslt)
		self._encoding = encoding

	def tostring(self, elem: "Union[_XSLTResultTree, Element]") -> str:
		from lxml import etree as ET
		return ET.tostring(
			elem,
			method="html",
			pretty_print=True,
		).decode("utf-8").strip()

	def transform(self, article: "Element") -> str:
		result_tree = self._transform(article)
		text = self.tostring(result_tree)
		text = text.replace("<br/> ", "<br/>")
		return text  # noqa: RET504

	def transformByInnerString(self, articleInnerStr: str) -> str:
		from lxml import etree as ET
		return self.transform(
			ET.fromstring(f"<ar>{articleInnerStr}</ar>"),
		)


class XdxfTransformer(object):
	_gram_color: str = "green"
	_example_padding: int = 10

	def __init__(self, encoding: str = "utf-8") -> None:
		self._encoding = encoding

	def tostring(self, elem: "Element") -> str:
		from lxml import etree as ET
		return ET.tostring(
			elem,
			method="html",
			pretty_print=True,
		).decode("utf-8").strip()

	def hasPrevText(self, prev: "Union[None, str, Element]") -> bool:
		if isinstance(prev, str):
			return True
		if prev is None:
			return False
		if prev.tag == "k":
			return False
		if prev.tag in (
			"dtrn", "def", "span", "co",
			"i", "b", "sub", "sup", "tt", "big", "small",
		):
			return True
		if prev.text:
			return True
		# print(prev)
		return False

	def writeString(
		self,
		hf: "T_htmlfile",
		child: str,
		parent: "Element",
		prev: "Union[None, str, Element]",
		stringSep: "str | None" = None,
	) -> None:
		from lxml import etree as ET

		def addSep() -> None:
			if stringSep is None:
				hf.write(ET.Element("br"))
			else:
				hf.write(stringSep)

		hasPrev = self.hasPrevText(prev)
		trail = False
		if parent.tag in ("ar", "font"):
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
		return

	def writeExample(
		self,
		hf: "T_htmlfile",
		elem: "Element",
	) -> None:
		prev = None
		stringSep = " "
		with hf.element("div", attrib={
			"class": "example",
			"style": f"padding: {self._example_padding}px 0px;",
		}):
			for child in elem.xpath("child::node()"):
				if isinstance(child, str):
					# if not child.strip():
					# 	continue
					self.writeString(hf, child, elem, prev, stringSep=stringSep)
					continue
				if child.tag == "iref":
					with hf.element("div"):
						self.writeIRef(hf, child)  # NESTED 5
					continue
				if child.tag in ("ex_orig", "ex_tran"):
					with hf.element("div"):
						self.writeChildrenOf(hf, child, stringSep=stringSep)  # NESTED 5
					continue
				# log.warning(f"unknown tag {child.tag} inside <ex>")
				self.writeChild(hf, child, elem, prev, stringSep=stringSep)
				prev = child

	def writeIRef(
		self,
		hf: "T_htmlfile",
		child: "Element",
	) -> None:
		iref_url = child.attrib.get("href", "")
		if iref_url.endswith((".mp3", ".wav", ".aac", ".ogg")):
			#  with hf.element("audio", src=iref_url):
			with hf.element("a", attrib={
				"class": "iref",
				"href": iref_url,
			}):
				hf.write("🔊")
			return

		with hf.element("a", attrib={
			"class": "iref",
			"href": child.attrib.get("href", child.text or ""),
		}):
			self.writeChildrenOf(hf, child, stringSep=" ")

	def writeChildElem(
		self,
		hf: "T_htmlfile",
		child: "Element",
		parent: "Element",
		prev: "Union[None, str, Element]",
		stringSep: "str | None" = None,
	) -> None:
		from lxml import etree as ET

		if child.tag == "br":
			hf.write(ET.Element("br"))
			return

		if child.tag in ("i", "b", "sub", "sup", "tt", "big", "small"):
			with hf.element(child.tag):
				self.writeChildrenOf(hf, child)
				# if child.text is not None:
				# 	hf.write(child.text.strip("\n"))
			return

		if child.tag == "blockquote":
			with hf.element("div", attrib={"class": "m"}):
				self.writeChildrenOf(hf, child)
			return

		if child.tag == "tr":
			hf.write("[")
			self.writeChildrenOf(hf, child)
			hf.write("]")
			hf.write(ET.Element("br"))
			return

		if child.tag == "k":
			with hf.element("div", attrib={"class": child.tag}):
				# with hf.element(glos.titleTag(child.text)):
				# ^ no glos object here!
				with hf.element("b"):
					self.writeChildrenOf(hf, child)
			return

		if child.tag == "sr":
			with hf.element("div", attrib={"class": child.tag}):
				self.writeChildrenOf(hf, child)
			return

		if child.tag == "ex":
			self.writeExample(hf, child)
			return

		if child.tag == "mrkd":
			if not child.text:
				return
			with hf.element("span", attrib={"class": child.tag}):
				with hf.element("b"):
					hf.write(child.text)
			return

		if child.tag in ("pos", "abr"):
			with hf.element("span", attrib={"class": child.tag}):
				with hf.element("font", color="green"):
					with hf.element("i"):
						self.writeChildrenOf(hf, child)  # NESTED 5
			return

		if child.tag in ("dtrn", "co"):
			self.writeChildrenOf(hf, child, sep=" ")
			return

		if child.tag == "c":
			color = child.attrib.get("c", "green")
			with hf.element("font", color=color):
				self.writeChildrenOf(hf, child)
			return

		if child.tag == "kref":
			if not child.text:
				log.warning(f"kref with no text: {self.tostring(child)}")
				return
			with hf.element("a", attrib={
				"class": "kref",
				"href": f"bword://{child.attrib.get('k', child.text)}",
			}):
				hf.write(child.text)
			return

		if child.tag == "iref":
			self.writeIRef(hf, child)
			return

		if child.tag == "rref":  # noqa: SIM102
			if not child.text:
				log.warning(f"rref with no text: {self.tostring(child)}")
				return

		if child.tag == "def":
			# TODO: create a list (ol / ul) unless it has one item only
			# like FreeDict reader
			with hf.element("div"):
				self.writeChildrenOf(hf, child)
			return

		if child.tag == "deftext":
			self.writeChildrenOf(hf, child, stringSep=" ", sep=" ")
			return

		if child.tag == "span":
			with hf.element("span"):
				self.writeChildrenOf(hf, child)
			return

		if child.tag == "abbr_def":
			# _type = child.attrib.get("type", "")
			# {"": "", "grm": "grammatical", "stl": "stylistical",
			#  "knl": "area/field of knowledge", "aux": "subsidiary"
			#  "oth": "others"}[_type]
			self.writeChildrenOf(hf, child)
			return

		if child.tag == "gr":
			with hf.element("font", color=self._gram_color):
				hf.write(child.text or "")
			hf.write(ET.Element("br"))
			return

		if child.tag == "ex_orig":
			with hf.element("i"):
				self.writeChildrenOf(hf, child)
			return

		if child.tag == "ex_transl" and prev is not None:
			if isinstance(prev, str):
				pass
			elif prev.tag == "ex_orig":
				if child.text != prev.text:
					with hf.element("i"):
						self.writeChildrenOf(hf, child)
				return

		if child.tag == "categ":  # Category
			with hf.element("span", style="background-color: green;"):
				self.writeChildrenOf(hf, child, stringSep=" ")
			return

		if child.tag == "opt":
			if child.text:
				hf.write(" (")
				hf.write(child.text)
				hf.write(")")
			return

		if child.tag == "img":
			with hf.element("img", attrib=dict(child.attrib)):
				pass
			return

		if child.tag == "abbr":
			# FIXME: may need an space or newline before it
			with hf.element("i"):
				hf.write(f"{child.text}")
			return

		if child.tag == "etm":  # Etymology (history and origin)
			# TODO: formatting?
			hf.write(f"{child.text}")
			return

		log.warning(f"unknown tag {child.tag}")
		self.writeChildrenOf(hf, child)


	def writeChild(
		self,
		hf: "T_htmlfile",
		child: "Union[str, Element]",
		parent: "Element",
		prev: "Union[None, str, Element]",
		stringSep: "str | None" = None,
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

	def shouldAddSep(
		self,
		child: "Union[str, Element]",
		prev: "Union[str, Element]",
	) -> bool:
		if isinstance(child, str):
			if len(child) > 0 and child[0] in ".,;)":
				return False
			return True

		if child.tag in ("sub", "sup"):
			return False

		if isinstance(prev, str):
			pass
		elif prev.tag in ("sub", "sup"):
			return False

		return True

	def writeChildrenOf(
		self,
		hf: "T_htmlfile",
		elem: "Element",
		sep: "str | None" = None,
		stringSep: "str | None" = None,
	) -> None:
		prev = None
		for child in elem.xpath("child::node()"):
			if sep and prev is not None and self.shouldAddSep(child, prev):
				hf.write(sep)
			self.writeChild(hf, child, elem, prev, stringSep=stringSep)
			prev = child

	def transform(self, article: "Element") -> str:
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
