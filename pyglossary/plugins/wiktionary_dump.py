# -*- coding: utf-8 -*-

from time import time as now
import re
import html

from formats_common import *

enable = True
format = "WiktionaryDump"
description = "Wiktionary Dump (.xml)"
extensions = (".xml",)
optionsProp = {
	"encoding": EncodingOption(),
}


class Reader(object):
	def __init__(self, glos):
		self._glos = glos
		self._buff = b""
		self._filename = ""
		self._file = None
		self._fileSize = 0
		# self._alts = {}
		# { word => alts }
		# where alts is str (one word), or list of strs
		# we can't recognize alternates unless we keep all data in memory
		# or scan the whole file and read all entries twice
		self.compilePatterns()

	def _readUntil(self, sub: bytes) -> bytes:
		for line in self._file:
			if sub in line:
				return line
			self._buff += line

	def _readSiteInfo(self) -> bytes:
		self._buff = self._readUntil(b"<siteinfo>")
		self._readUntil(b"</siteinfo>")
		siteinfoBytes = self._buff + b"</siteinfo>"
		self._buff = b""
		return siteinfoBytes

	def open(self, filename):
		try:
			from lxml import etree as ET
		except ModuleNotFoundError as e:
			e.msg += f", run `{pip} install lxml` to install"
			raise e

		self._filename = filename
		self._file = open(filename, mode="rb")
		self._fileSize = os.path.getsize(filename)
		log.info(f"fileSize = {self._fileSize}")

		siteinfoBytes = self._readSiteInfo()
		siteinfoStr = siteinfoBytes.decode("utf-8")

		siteinfo = ET.fromstring(siteinfoStr)

		sitename = ", ".join(siteinfo.xpath("sitename/text()"))
		dbname = ", ".join(siteinfo.xpath("dbname/text()"))
		generator = ", ".join(siteinfo.xpath("generator/text()"))

		self._glos.setInfo("title", f"{dbname} ({sitename})")
		self._glos.setInfo("input_file_size", f"{self._fileSize}")

		base = siteinfo.xpath("base/text()")
		if base:
			wiki_url = "/".join(base[0].rstrip("/").split("/")[:-1])
			self._glos.setInfo("website", wiki_url)
			self._glos.setInfo("entry_url", f"{wiki_url}/{{word}}")

		self._glos.setInfo("generator", generator)

		namespaces = siteinfo.find("namespaces")
		if namespaces is not None:
			self._glos.setInfo("namespaces", ET.tostring(namespaces))

	def close(self):
		self._filename = ""
		self._file.close()
		# self._alts = {}

	def __len__(self):
		return 0

	def _readPage(self) -> "lxml.etree.Element":
		from lxml import etree as ET
		pageEnd = self._readUntil(b"</page>")
		if pageEnd is None:
			return
		page = ET.fromstring(self._buff + pageEnd)
		self._buff = b""
		return page

	def __iter__(self) -> "Iterator[BaseEntry]":
		from lxml import etree as ET
		if not self._filename:
			raise RuntimeError("iterating over a reader while it's not open")
		while True:
			page = self._readPage()
			if page is None:
				break
			yield self._getEntryFromPage(page)

	def _sub_internal_link(self, m: "re.Match") -> str:
		ref = m.group(1)
		return f'<a href="bword://{html.escape(ref)}">{ref}</a>'

	def compilePatterns(self):
		self._re_comment = re.compile(
			"<!--.*?-->",
		)
		self._re_internal_link = re.compile(
			r"\[\[(.+?)\]\]",
			re.MULTILINE,
		)
		self._re_translationHeader = re.compile(
			r"^[;*]?\s?{{(.+?)}}:\s*(.+)$",
			re.MULTILINE,
		)
		self._re_listItemEmpty = re.compile(
			r"^[#*]\s*$",
			re.MULTILINE,
		)
		# ideally '# ...'  should become <ol>, and '* ...' become <ul>
		# but that's hard, so we just replace both with '⚫︎ ...'
		self._re_listItem = re.compile(
			r"^[#*] ?(.*)",
			re.MULTILINE,
		)
		self._re_h2 = re.compile(
			r"^==(\{\{\{\d+\|)?([^={}]+?)(\}\}\})?==$",
			re.MULTILINE,
		)
		self._re_h3 = re.compile(
			r"^===(\{\{\{\d+\|)?([^={}]+?)(\}\}\})?===$",
			re.MULTILINE,
		)
		self._re_h4 = re.compile(
			r"^={4,5}([^=]+?)={4,5}$",
			re.MULTILINE,
		)
		self._re_template = re.compile(
			r"^\{\{(...+?\|...+?)\}\}$",
			re.MULTILINE,
		)
		self._re_qualifier = re.compile(
			r"\{\{qualifier\|(.+?)\}\}",
		)
		self._re_lastLineLink = re.compile(
			"\\n(<a href=[^<>]*>.*</a>)\\s*$",
		)
		self._re_remainDoubleCurlyBraces = re.compile(
			r"\{\{([^{}]+?)\}\}",
			re.MULTILINE,
		)
		self._re_nonTaggedLine = re.compile(
			r"^([^<\s].+?[^>\s])$",
			re.MULTILINE,
		)
		#self._re_emptyCircledLines = re.compile(
		#	r"^\s*⚫︎\s*$",
		#	re.MULTILINE | re.UNICODE,
		#)

	def fixText(self, text: str) -> str:
		text = self._re_comment.sub("", text)
		text = self._re_listItemEmpty.sub("", text)
		text = self._re_internal_link.sub(self._sub_internal_link, text)
		text = self._re_translationHeader.sub(
			r"<h3>\1</h3>\n⚫︎ \2<br>",
			text,
		)
		text = self._re_listItem.sub(r"⚫︎ \1<br>", text)
		text = self._re_h2.sub(r"<h2>\2</h2>", text)
		text = self._re_h3.sub(r"<h3>\2</h3>", text)
		text = self._re_h4.sub(r"<h4>\1</h4>", text)
		text = self._re_template.sub(r"<i>Template: \1</i><br>", text)
		text = self._re_qualifier.sub(r"<i>(\1)</i>", text)
		text = self._re_lastLineLink.sub("\n<br><br>\\1", text)
		text = self._re_remainDoubleCurlyBraces.sub(r"<i>\1</i><br>", text)
		text = self._re_nonTaggedLine.sub(r"\1<br>", text)
		# text = self._re_emptyCircledLines.sub("", text)
		return text

	def _getEntryFromPage(self, page: "lxml.etree.Element") -> "BaseEntry":
		titleElem = page.find(".//title")
		if titleElem is None:
			return
		title = titleElem.text
		if not title:
			return
		textElem = page.find(".//text")
		if textElem is None:
			return
		text = textElem.text
		if not text:
			return
		text = self.fixText(text)
		byteProgress = (self._file.tell(), self._fileSize)
		return self._glos.newEntry(title, text, byteProgress=byteProgress)
