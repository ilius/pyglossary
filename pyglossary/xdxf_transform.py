from pyglossary import core
from pyglossary.core import rootDir
import logging
from io import BytesIO
from os.path import join
import lxml

from typing import Optional, Union

log = logging.getLogger("pyglossary")

# <k> and visual tags, no additional space/newline before/after them
transparent_tags = {
	"k",
	"b", "i", "c",
	"sub", "sup",
}

# Add a newline between following tags and any tag before/after (other than transparent_tags)
block_tags = {
	"co",  # editorial comment
	"dtrn",  # Direct Translation of the key-phrase
	"tr",  # transcription/pronunciation
	"def",  # definition
	"gr",  # grammer
	"pos",  # not in standard, treat it like <gr>
	"sr",  # semantic relations
	"iref",  # child of <ex>
	"ex_orig",  # child of <ex>
	"ex_tran",  # child of <ex>
}

# No space/newline before/after <abr> (unless because of adjacent tags)

# No space/newline before/after <kref>, unless inside <sr> (or because of adjacent tags)
# So there must be newline between several <kref> inside <sr>

# Add a newline between two directly adjacent "ex" tags, <ex>...</ex><ex>...</ex>

# TODO: figure out rules for spaces



def getTag(child: "Union[str, lxml.etree.Element]") -> str:
	if isinstance(child, str):
		return ""
	return child.tag


class IterationState(object):
	def __init__(self):
		self.elems = []
		self.opaqueElems = []
		self.lastElem = None
		self.lastOpaqueElem = None

	def open(self, elem) -> None:
		tag = getTag(elem)
		self.elems.append(elem)
		if tag not in transparent_tags:
			self.opaqueElems.append(elem)

	def close(self):
		elem = self.elems[-1]
		self.elems = self.elems[:-1]
		self.lastElem = elem
		tag = getTag(elem)
		if tag not in transparent_tags:
			assert getTag(self.opaqueElems[-1]) == tag
			self.opaqueElems = self.opaqueElems[:-1]
			self.lastOpaqueElem = elem

	@property
	def tag(self):
		if not self.elems:
			return None
		return getTag(self.elems[-1])

	@property
	def parentTag(self):
		if len(self.elems) < 2:
			return None
		return getTag(self.elems[-2])

	@property
	def lastTag(self):
		if self.lastElem is None:
			return None
		return getTag(self.lastElem)

	@property
	def lastOpaqueTag(self):
		if self.lastOpaqueElem is None:
			return None
		return getTag(self.lastOpaqueElem)





class XslXdxfTransformer(object):
	_gram_color: str = "green"
	_example_padding: int = 10

	def __init__(self, encoding="utf-8"):
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

	def tostring(self, elem: "lxml.etree.Element") -> str:
		from lxml import etree as ET
		return ET.tostring(
			elem,
			method="html",
			pretty_print=True,
		).decode("utf-8").strip()

	def transform(self, article: "lxml.etree.Element") -> str:
		result_tree = self._transform(article)
		text = self.tostring(result_tree)
		text = text.replace("<br/> ", "<br/>")
		return text

	def transformByInnerString(self, articleInnerStr: str) -> str:
		from lxml import etree as ET
		return self.transform(
			ET.fromstring(f"<ar>{articleInnerStr}</ar>")
		)


class XdxfTransformer(object):
	_gram_color: str = "green"
	_example_padding: int = 10

	def __init__(self, encoding="utf-8"):
		self._encoding = encoding

	def tostring(self, elem: "lxml.etree.Element") -> str:
		from lxml import etree as ET
		return ET.tostring(
			elem,
			method="html",
			pretty_print=True,
		).decode("utf-8").strip()

	def hasPrevText(self, prev: "Union[None, str, lxml.etree.Element]"):
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
		hf: "lxml.etree.htmlfile",
		child: str,
		parent: "lxml.etree.Element",
		prev: "Union[None, str, lxml.etree.Element]",
		stringSep: "Optional[str]" = None,
	):
		from lxml import etree as ET

		def addSep():
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

		#if self.shouldAddSep(child, prev):
		#	addSep()

		# child = child.rstrip()
		lines = [line for line in child.split("\n") if line]
		for index, line in enumerate(lines):
			if self.shouldAddSep(line, None):
				addSep()
			hf.write(line)
		#if trail:
		#	addSep()
		return

	def writeExample(
		self,
		hf: "lxml.etree.htmlfile",
		elem: "Union[str, lxml.etree.Element]",
	):
		prev = None
		stringSep = " "
		with hf.element("div", **{
			"class": "example",
			"style": f"padding: {self._example_padding}px 0px;",
		}):
			for child in elem.xpath("child::node()"):
				if isinstance(child, str):
					self.writeString(hf, child, elem, prev, stringSep=stringSep)
					continue
				if child.tag == "iref":
					with hf.element("div"):
						self.writeIRef(hf, child)  # NESTED 5
					continue
				if child.tag in ("ex_orig", "ex_tran"):
					with hf.element("div"):
						self.writeChildren(hf, child)  # NESTED 5
					continue
				# log.warning(f"unknown tag {child.tag} inside <ex>")
				self.writeChild(hf, child, elem, prev, stringSep=stringSep)
				prev = child

	def writeIRef(
		self,
		hf: "lxml.etree.htmlfile",
		child: "Union[str, lxml.etree.Element]",
	):
		iref_url = child.attrib.get("href", "")
		if iref_url.endswith((".mp3", ".wav", ".aac", ".ogg")):
			#  with hf.element("audio", src=iref_url):
			with hf.element("a", **{
				"class": "iref",
				"href": iref_url,
			}):
				hf.write("🔊")
			return
		else:
			with hf.element("a", **{
				"class": "iref",
				"href": child.attrib.get("href", child.text),
			}):
				self.writeChildren(hf, child)

	def writeChild(
		self,
		hf: "lxml.etree.htmlfile",
		child: "Union[str, lxml.etree.Element]",
		parent: "lxml.etree.Element",
		prev: "Union[None, str, lxml.etree.Element]",
		stringSep: "Optional[str]" = None,
	):
		from lxml import etree as ET

		if isinstance(child, str):
			if not child.strip():
				return
			self.writeString(hf, child, parent, prev, stringSep=stringSep)
			return

		if child.tag == "br":
			hf.write(ET.Element("br"))
			return

		if child.tag in ("i", "b", "sub", "sup", "tt", "big", "small"):
			with hf.element(child.tag):
				self.writeChildren(hf, child)
				# if child.text is not None:
				# 	hf.write(child.text.strip("\n"))
			return

		if child.tag == "blockquote":
			with hf.element("div", **{"class": "m"}):
				self.writeChildren(hf, child)
			return

		if child.tag == "tr":
			hf.write("[")
			self.writeChildren(hf, child)
			hf.write("]")
			hf.write(ET.Element("br"))
			return

		if child.tag == "k":
			with hf.element("div", **{"class": child.tag}):
				# with glos.titleElement(hf, child.text):
				# ^ no glos object here!
				with hf.element("b"):
					self.writeChildren(hf, child)
			return

		if child.tag == "sr":
			with hf.element("div", **{"class": child.tag}):
				self.writeChildren(hf, child)
			return

		if child.tag == "ex":
			self.writeExample(hf, child)
			return

		if child.tag == "mrkd":
			if not child.text:
				return
			with hf.element("span", **{"class": child.tag}):
				with hf.element("b"):
					hf.write(child.text)
			return

		if child.tag in ("pos", "abr"):
			with hf.element("span", **{"class": child.tag}):
				with hf.element("font", color="green"):
					with hf.element("i"):
						self.writeChildren(hf, child)  # NESTED 5
			return

		if child.tag in ("dtrn", "co"):
			self.writeChildren(hf, child)
			return

		if child.tag == "c":
			color = child.attrib.get("c", "green")
			with hf.element("font", color=color):
				self.writeChildren(hf, child)
			return

		if child.tag == "kref":
			if not child.text:
				log.warning(f"kref with no text: {self.tostring(child)}")
				return
			with hf.element("a", **{
				"class": "kref",
				"href": f"bword://{child.attrib.get('k', child.text)}",
			}):
				hf.write(child.text)
			return

		if child.tag == "iref":
			self.writeIRef(hf, child)
			return

		if child.tag == "rref":
			if not child.text:
				log.warning(f"rref with no text: {self.tostring(child)}")
				return

		if child.tag == "def":
			# TODO: create a list (ol / ul) unless it has one item only
			# like FreeDict reader
			with hf.element("div"):
				self.writeChildren(hf, child)
			return

		if child.tag == "deftext":
			self.writeChildren(hf, child)
			return

		if child.tag == "span":
			with hf.element("span"):
				self.writeChildren(hf, child)
			return

		if child.tag == "abbr_def":
			# _type = child.attrib.get("type", "")
			# {"": "", "grm": "grammatical", "stl": "stylistical",
			#  "knl": "area/field of knowledge", "aux": "subsidiary"
			#  "oth": "others"}[_type]
			self.writeChildren(hf, child)
			return

		if child.tag in ("gr", "pos"):
			with hf.element("font", color=self._gram_color):
				hf.write(child.text)
			hf.write(ET.Element("br"))
			return

		if child.tag == "ex_orig":
			with hf.element("i"):
				self.writeChildren(hf, child)
			return

		if child.tag == "ex_transl" and prev.tag == "ex_orig":
			if child.text != prev.text:
				with hf.element("i"):
					self.writeChildren(hf, child)
			return

		if child.tag == "categ":  # Category
			with hf.element("span", style="background-color: green;"):
				self.writeChildren(hf, child)
			return

		if child.tag == "opt":
			if child.text:
				hf.write(" (")
				hf.write(child.text)
				hf.write(")")
			return

		if child.tag == "img":
			with hf.element("img", **child.attrib):
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
		self.writeChildren(hf, child)

	def shouldAddSep(
		self,
		child: "Union[str, lxml.etree.Element]",
		prev: "Union[str, lxml.etree.Element]",
	):
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

	def shouldAddNewline(
		self,
		state: IterationState,
	) -> bool:
		if state.lastOpaqueElem is None:
			return False

		if state.lastOpaqueTag in block_tags:
			return True

		tag = state.tag

		# This may add newline after opening a visual tag, for example:
		# <gr>verb</gr><i><br/>something</i>
		# instead of
		# <gr>verb</gr><br/><i>something</i>
		# but I don't have a clean solution for it now
		if tag in transparent_tags:
			return False

		if tag in block_tags:
			return True

		if state.parentTag == "sr" and "kref" in (tag, state.lastOpaqueTag):
			return True

		# Add a newline between two directly adjacent "ex" tags, <ex>...</ex><ex>...</ex>
		if tag == "ex" and state.lastTag == "ex":
			return True

		return False

	def writeChildren(
		self,
		hf: "lxml.etree.htmlfile",
		elem: "lxml.etree.Element",
	):
		state = IterationState()
		state.open(elem)
		self.writeChildrenRec(hf, elem, state)
		state.close()

	def writeChildrenRec(
		self,
		hf: "lxml.etree.htmlfile",
		elem: "lxml.etree.Element",
		state: "IterationState",
	):
		from lxml import etree as ET

		for index, child in enumerate(elem.xpath("child::node()")):
			state.open(child)
			tag = getTag(child)
			if self.shouldAddNewline(state):
				hf.write(ET.Element("br"))
			self.writeChild(hf, child, elem, state.lastElem)
			state.close()


	def transform(self, article: "lxml.etree.Element") -> str:
		from lxml import etree as ET
		# encoding = self._encoding
		f = BytesIO()
		with ET.htmlfile(f, encoding="utf-8") as hf:
			with hf.element("div", **{"class": "article"}):
				self.writeChildren(hf, article)

		text = f.getvalue().decode("utf-8")
		text = text.replace("<br>", "<br/>")  # for compatibility
		return text

	def transformByInnerString(self, articleInnerStr: str) -> str:
		from lxml import etree as ET
		return self.transform(
			ET.fromstring(f"<ar>{articleInnerStr}</ar>")
		)
