"""
Write glossaries as a directory of HTML files.

Generates one HTML page per entry (or grouped layout) plus index pages — a
simple static website view of a dictionary.
"""

from __future__ import annotations

# mypy: ignore-errors
import html
import os
import re
import time
from functools import lru_cache
from os.path import isdir, isfile, join
from typing import IO, TYPE_CHECKING

from pyglossary.core import log
from pyglossary.utils.text_utils import (
	escapeNTB,
	unescapeNTB,
)

if TYPE_CHECKING:
	import io
	from collections.abc import Generator
	from re import Pattern

	from pyglossary.stubs.glossary_types import (
		EntryType,
		WriterGlossaryType,
	)

__all__ = ["Writer"]

_nbsp = "\xa0"
# _nbsp = "&nbsp;"

_fixedLinkPattern = re.compile(
	r'<a (?:[^<>]*? )?href="#([^<>"]+?)">[^<>]+?</a>',
	re.IGNORECASE,
)

_darkStyle = """
body {{
	background-color: #373737;
	color: #eee;
}}
a {{ color: #aaaaff; }}
a.broken {{ color: #e0c0c0; }}
a.no_ul {{ text-decoration: none; }}
b.headword {{ font-size: 1.5em; color: #c7ffb9; }}
h1 {{ font-size: 1.5em; color: #c7ffb9;}}
h2 {{ font-size: 1.3em;}}
h3 {{ font-size: 1.0em;}}
h4 {{ font-size: 1.0em;}}
h5 {{ font-size: 1.0em;}}
h6 {{ font-size: 1.0em;}}
"""


class Writer:
	"""Write glossary files in Html Dir format."""

	_encoding: str = "utf-8"
	_resources: bool = True
	_max_file_size: int = 102400
	_filename_format: str = "{n:05d}.html"
	_escape_defi: bool = False
	_dark: bool = True
	_css: str = ""
	_word_title: bool = True

	@staticmethod
	def stripFullHtmlError(entry: EntryType, error: str) -> None:
		log.error(f"error in stripFullHtml: {error}, terms={entry.l_term!r}")

	def __init__(self, glos: WriterGlossaryType) -> None:
		self._glos = glos
		self._filename = ""
		self._fileObj: io.IOBase | None = None
		self._encoding = "utf-8"
		self._filename_format = "{n:05d}.html"
		self._tail = "</body></html>"
		self._filenameList: list[str] = []
		glos.stripFullHtml(errorHandler=self.stripFullHtmlError)

		self._resSrcPattern = re.compile(' src="([^"]*)"')

	def open(self, filename: str) -> None:
		self._filename = filename
		self._resDir = resDir = join(filename, "res")
		if not isdir(filename):
			os.mkdir(filename)
		if not isdir(resDir):
			os.mkdir(resDir)
		if self._css:
			self.copyCSS(self._css)

	def copyCSS(self, cssPath: str) -> None:
		import shutil

		shutil.copy(cssPath, join(self._filename, "style.css"))

	def finish(self) -> None:
		pass

	def getNextFilename(self) -> str:
		return self._filename_format.format(
			n=len(self._filenameList),
		)

	def nextFile(self) -> io.TextIOBase:
		if self._fileObj:
			self._fileObj.write(self._tail)
			self._fileObj.close()
		filename = self.getNextFilename()
		self._filenameList.append(filename)
		self._fileObj = open(
			join(
				self._filename,
				filename,
			),
			mode="w",
			encoding=self._encoding,
		)
		return self._fileObj

	@staticmethod
	def _fixLinkItem(
		re_href: Pattern[bytes],
		entry_url_fmt: str,
		inFile: IO[bytes],
		outFile: IO[bytes],
		linkLine: str,
	) -> None:
		outFile.flush()
		b_x_start, b_x_size, b_target = linkLine.rstrip(b"\n").split(b"\t")
		outFile.write(inFile.read(int(b_x_start, 16) - inFile.tell()))
		curLink = inFile.read(int(b_x_size, 16))

		if b_target:
			outFile.write(
				re_href.sub(
					b' href="./' + b_target + b'"',
					curLink,
				),
			)
			return

		if not entry_url_fmt:
			outFile.write(
				curLink.replace(
					b' href="#',
					b' class="broken" href="#',
				),
			)
			return

		st = curLink.decode("utf-8")
		i = st.find('href="#')
		j = st.find('"', i + 7)
		term = st[i + 7 : j]
		url = entry_url_fmt.format(word=term)
		outFile.write(
			(st[:i] + f'class="broken" href="{url}"' + st[j + 1 :]).encode("utf-8"),
		)

	def fixLinks(self, linkTargetSet: set[str]) -> None:  # noqa: PLR0912
		import gc

		gc.collect()
		dirn = self._filename

		filenameList = self._filenameList

		fileByTerm: dict[str, list[tuple[str, int]]] = {}
		for line in open(join(dirn, "index.txt"), encoding="utf-8"):
			line = line.rstrip("\n")  # noqa: PLW2901
			if not line:
				continue
			entryIndexStr, termEscaped, filename, _ = line.split("\t")
			entryIndex = int(entryIndexStr)
			# entryId = f"entry{entryIndex}"
			term = unescapeNTB(termEscaped)
			if term not in linkTargetSet:
				continue
			if term in fileByTerm:
				fileByTerm[term].append((filename, entryIndex))
			else:
				fileByTerm[term] = [(filename, entryIndex)]

		# with open(join(dirn, "fileByTerm.json"), "w") as fileByTermFile:
		# 	json.dump(fileByTerm, fileByTermFile, ensure_ascii=False, indent="\t")

		@lru_cache(maxsize=10)
		def getLinksByFile(fileIndex: int) -> io.TextIOBase:
			return open(
				join(dirn, f"links{fileIndex}"),
				mode="a",
				encoding="utf-8",
			)

		log.info("")
		for line in open(join(dirn, "links.txt"), encoding="utf-8"):
			line = line.rstrip("\n")  # noqa: PLW2901
			if not line:
				continue
			target, fileIndexStr, x_start, x_size = line.split("\t")
			target = unescapeNTB(target)
			if target not in fileByTerm:
				targetNew = ""
			else:
				targetFilename, targetEntryIndex = fileByTerm[target][0]
				targetNew = f"{targetFilename}#entry{targetEntryIndex}"
			file = getLinksByFile(int(fileIndexStr))
			file.write(
				f"{x_start}\t{x_size}\t{targetNew}\n",
			)
			file.flush()

		linkTargetSet.clear()
		del fileByTerm, linkTargetSet
		gc.collect()

		if os.sep == "\\":
			time.sleep(0.1)

		entry_url_fmt = self._glos.getInfo("entry_url")

		re_href = re.compile(
			b' href="[^<>"]*?"',
			re.IGNORECASE,
		)

		for fileIndex, filename in enumerate(filenameList):
			if not isfile(join(dirn, f"links{fileIndex}")):
				continue
			with open(join(dirn, filename), mode="rb") as inFile:
				with open(join(dirn, f"{filename}.new"), mode="wb") as outFile:
					for linkLine in open(join(dirn, f"links{fileIndex}"), "rb"):
						self._fixLinkItem(
							re_href,
							entry_url_fmt,
							inFile,
							outFile,
							linkLine,
						)
					outFile.write(inFile.read())

			os.remove(join(dirn, filename))
			os.rename(join(dirn, f"{filename}.new"), join(dirn, filename))
			os.remove(join(dirn, f"links{fileIndex}"))

	def writeInfo(self, filename: str, header: str) -> None:
		glos = self._glos
		title = glos.getInfo("name")
		customStyle = (
			"table, th, td {border: 1px solid black; "
			"border-collapse: collapse; padding: 5px;}"
		)
		infoHeader = header.format(
			pageTitle=f"Info: {title}",
			customStyle=customStyle,
		)
		with open(
			join(filename, "info.html"),
			mode="w",
			encoding=self._encoding,
		) as file:
			file.write(
				infoHeader + "<table>"
				"<tr>"
				'<th width="%10">Key</th>'
				'<th width="%90">Value</th>'
				"</tr>\n",
			)
			file.writelines(
				f"<tr><td>{key}</td><td>{value}</td></tr>\n"
				for key, value in glos.iterInfo()
			)
			file.write("</table></body></html>")

	@staticmethod
	def _subResSrc(m: re.Match) -> str:
		url = m.group(1)
		if "://" in url:
			return m.group(0)
		url = "res/" + url
		return f' src="{url}"'

	def _getEntryWebLink(self, entry: EntryType) -> str:
		entry_url_fmt = self._glos.getInfo("entry_url")
		if not entry_url_fmt:
			return ""
		url = entry_url_fmt.format(word=html.escape(entry.l_term[0]))
		return f'{_nbsp}<a class="no_ul" href="{url}">&#127759;</a>'

	def _formatEntry(self, entry: EntryType, entryIndex: int, title: str) -> str:
		termSep = ' <font color="red">|</font> '

		entry.detectDefiFormat()
		defi = entry.defi
		defiFormat = entry.defiFormat

		if defi.startswith("<!DOCTYPE html>") and defiFormat != "h":
			log.error(f"bad {defiFormat=}")
			defiFormat = "h"

		if defiFormat == "m":
			defi = html.escape(defi)
			if "\n" in defi:
				# could be markdown or unformatted plaintext
				# FIXME: this changes the font to a monospace
				defi = f"<pre>{defi}</pre>"
		elif defiFormat == "h":
			defi = self._resSrcPattern.sub(self._subResSrc, defi)
			if self._escape_defi:
				defi = html.escape(defi)

		entryId = f"entry{entryIndex}"

		if self._word_title:
			terms = [html.escape(term) for term in entry.l_term]
			title = self._glos.wordTitleStr(
				termSep.join(terms),
				sample=entry.l_term[0],
				class_="headword",
			)

		if not title:
			title = f"Entry {entryIndex}"

		# entry_link_sym = "&#182;"
		entry_link_sym = "&#128279;"
		return (
			f'<div id="{entryId}">{title}{_nbsp}{_nbsp}'
			f'<a class="no_ul" class="entry_link" href="#{entryId}">'
			f"{entry_link_sym}</a>"
			f"{self._getEntryWebLink(entry)}"
			f"<br>\n{defi}"
			"</div>\n"
			"<hr>\n"
		)

	@staticmethod
	def _replaceBword(text: str) -> str:
		return text.replace(
			' href="bword://',
			' href="#',
		)

	def _addLinks(
		self,
		text: str,
		pos: int,
		linksTxtFileObj: io.TextIOBase,
		linkTargetSet: set[str],
	) -> None:
		encoding = self._encoding
		for m in _fixedLinkPattern.finditer(text):
			if ' class="entry_link"' in m.group(0):
				continue
			if m.group(0).count("href=") != 1:
				log.error(f"unexpected match: {m.group(0)}")
			target = html.unescape(m.group(1))
			linkTargetSet.add(target)
			start = m.start()
			b_start = len(text[:start].encode(encoding))
			b_size = len(text[start : m.end()].encode(encoding))
			linksTxtFileObj.write(
				f"{escapeNTB(target)}\t"
				f"{len(self._filenameList) - 1}\t"
				f"{pos + b_start:x}\t"
				f"{b_size:x}\n",
			)
			linksTxtFileObj.flush()

	def _makeHeader(self) -> str:
		style = _darkStyle if self._dark else ""
		cssLink = '<link rel="stylesheet" href="style.css" />' if self._css else ""
		return (
			"<!DOCTYPE html>\n"
			"<html><head>"
			"<title>{pageTitle}</title>"
			f'<meta charset="{self._encoding}">'
			f'<style type="text/css">{style}{{customStyle}}</style>{cssLink}'
			"</meta></head><body>\n"
		)

	@staticmethod
	def _pageHeader(header: str, title: str, n: int) -> str:
		return header.format(
			pageTitle=f"Page {n} of {title}",
			customStyle="",
		)

	def _navBar(self) -> str:
		links: list[str] = []
		if len(self._filenameList) > 1:
			links.append(f'<a href="./{self._filenameList[-2]}">&#9664;</a>')
		links.extend(
			[
				f'<a href="./{self.getNextFilename()}">&#9654;</a>',
				'<a href="./info.html">ℹ️</a></div>',  # noqa: RUF001
			],
		)
		return (
			'<nav style="text-align: center; font-size: 2.5em;">'
			+ f"{_nbsp}{_nbsp}{_nbsp}".join(links)
			+ "</nav>"
		)

	def write(self) -> Generator[None, EntryType, None]:
		encoding = self._encoding
		resources = self._resources
		max_file_size = self._max_file_size

		initFileSizeMax = 100

		glos = self._glos
		filename = self._filename

		indexTxtFileObj = open(
			join(filename, "index.txt"),
			mode="w",
			encoding="utf-8",
		)
		linksTxtFileObj = open(
			join(filename, "links.txt"),
			mode="w",
			encoding="utf-8",
		)

		title = glos.getInfo("name")
		header = self._makeHeader()

		tailSize = len(self._tail.encode(encoding))

		if max_file_size < len(header) + tailSize:
			raise ValueError(f"{max_file_size=} is too small")

		max_file_size -= tailSize

		if not isdir(filename):
			os.mkdir(filename)

		self._fileObj = self.nextFile()
		self._fileObj.write(self._pageHeader(header, title, 0))
		self._fileObj.write(self._navBar())

		linkTargetSet: set[str] = set()

		self.writeInfo(filename, header)

		entryIndex = -1
		while True:
			entryIndex += 1
			entry = yield
			if entry is None:
				break
			if entry.isData():
				if resources:
					entry.save(self._resDir)
				continue

			text = self._formatEntry(entry, entryIndex, title)
			pos = self._fileObj.tell()
			if pos > initFileSizeMax and pos > max_file_size - len(
				text.encode(encoding),
			):
				self._fileObj = self.nextFile()
				self._fileObj.write(
					self._pageHeader(
						header,
						title,
						len(self._filenameList) - 1,
					),
				)
				self._fileObj.write(self._navBar())
			pos = self._fileObj.tell()
			tmpFilename = escapeNTB(self._filenameList[-1])
			indexTxtFileObj.writelines(
				f"{entryIndex}\t{escapeNTB(term)}\t{tmpFilename}\t{pos}\n"
				for term in entry.l_term
			)
			del tmpFilename
			text = self._replaceBword(text)
			self._addLinks(text, pos, linksTxtFileObj, linkTargetSet)
			self._fileObj.write(text)

		self._fileObj.close()
		self._fileObj = None
		indexTxtFileObj.close()

		linksTxtFileObj.close()

		if linkTargetSet:
			log.info(f"{len(linkTargetSet)} link targets found")
			log.info("Fixing links, please wait...")
			self.fixLinks(linkTargetSet)

		os.remove(join(filename, "links.txt"))
