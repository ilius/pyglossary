# -*- coding: utf-8 -*-

from formats_common import *
from pyglossary.text_utils import (
	escapeNTB,
	unescapeNTB,
)
import html
import os
import json

enable = True
lname = "html_dir"
format = "HtmlDir"
description = "HTML Directory"
extensions = (".hdir",)
extensionCreate = ".hdir/"
singleFile = False
kind = "directory"
wiki = ""
website = None
optionsProp = {
	"encoding": EncodingOption(),
	"resources": BoolOption(
		comment="Enable resources / data files",
	),
	"max_file_size": IntOption(
		comment="Maximum file size in bytes",
	),
	"filename_format": StrOption(
		comment="Filename format, default: {n:05d}.html",
	),
	"escape_defi": BoolOption(
		comment="Escape definitions",
	),
	"dark": BoolOption(
		comment="Use dark style",
	),
	"css": StrOption(
		comment="Path to css file",
	),
	"word_title": BoolOption(
		comment="Add headwords title to begining of definition",
	),
}

nbsp = "\xa0"
# nbsp = "&nbsp;"

darkStyle = """
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


class Writer(object):
	depends = {
		"cachetools": "cachetools",
	}

	_encoding: str = "utf-8"
	_resources: bool = True
	_max_file_size: int = 102400
	_filename_format: str = "{n:05d}.html"
	_escape_defi: bool = False
	_dark: bool = True
	_css: str = ""
	_word_title: bool = True

	def __init__(self, glos: GlossaryType):
		self._glos = glos
		self._filename = None
		self._fileObj = None
		self._encoding = "utf-8"
		self._filename_format = "{n:05d}.html"
		self._tail = "</body></html>"
		self._filenameList = []

	def open(self, filename: str):
		from cachetools import LRUCache

		self._filename = filename
		self._resDir = resDir = join(filename, "res")
		if not isdir(filename):
			os.mkdir(filename)
		if not isdir(resDir):
			os.mkdir(resDir)
		if self._css:
			self.copyCSS(self._css)

	def copyCSS(self, cssPath):
		import shutil
		shutil.copy(self._css, join(self._filename, "style.css"))

	def finish(self):
		pass

	def getNextFilename(self):
		return self._filename_format.format(
			n=len(self._filenameList)
		)

	def nextFile(self):
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

	def fixLinks(self, linkTargetSet):
		import gc
		from cachetools import LRUCache

		gc.collect()
		dirn = self._filename

		filenameList = self._filenameList

		fileByWord = {}
		for line in open(join(dirn, "index.txt"), encoding="utf-8"):
			line = line.rstrip("\n")
			if not line:
				continue
			entryIndex, wordEsc, filename, _ = line.split("\t")
			entryIndex = int(entryIndex)
			# entryId = f"entry{entryIndex}"
			word = unescapeNTB(wordEsc)
			if word not in linkTargetSet:
				continue
			if word in fileByWord:
				# log.info(f'fileByWord[{word}]={fileByWord[word]}, filename={filename}')
				fileByWord[word].append((filename, entryIndex))
			else:
				fileByWord[word] = [(filename, entryIndex)]

		linksByFile = LRUCache(maxsize=100)

		# with open(join(dirn, "fileByWord.json"), "w") as fileByWordFile:
		# 	json.dump(fileByWord, fileByWordFile, ensure_ascii=False, indent="\t")

		def getLinksByFile(fileIndex):
			_file = linksByFile.get(fileIndex)
			if _file is not None:
				return _file
			_file = open(
				join(dirn, f"links{fileIndex}"),
				mode="a",
				encoding="utf-8",
			)
			linksByFile[fileIndex] = _file
			return _file

		log.info("")
		for line in open(join(dirn, "links.txt"), encoding="utf-8"):
			line = line.rstrip("\n")
			if not line:
				continue
			target, fileIndex, x_start, x_size = line.split("\t")
			target = unescapeNTB(target)
			if target not in fileByWord:
				targetNew = ""
			else:
				targetFilename, targetEntryIndex = fileByWord[target][0]
				if targetFilename == filename:
					continue
				targetNew = f"{targetFilename}#entry{targetEntryIndex}"
			_file = getLinksByFile(int(fileIndex))
			_file.write(
				f"{x_start}\t{x_size}\t{targetNew}\n"
			)
			_file.flush()

		for _, _file in linksByFile.items():
			_file.close()
		del linksByFile

		linkTargetSet.clear()
		del fileByWord, linkTargetSet
		gc.collect()

		entry_url_fmt = self._glos.getInfo("entry_url")

		re_href = re.compile(
			b' href="[^<>"]*?"',
			re.I,
		)

		for fileIndex, filename in enumerate(filenameList):
			if not isfile(join(dirn, f"links{fileIndex}")):
				continue
			with open(join(dirn, filename), mode="rb") as inFile:
				with open(join(dirn, f"{filename}.new"), mode="wb") as outFile:
					for linkLine in open(join(dirn, f"links{fileIndex}"), "rb"):
						outFile.flush()
						linkLine = linkLine.rstrip(b"\n")
						x_start, x_size, target = linkLine.split(b"\t")
						outFile.write(inFile.read(
							int(x_start, 16) - inFile.tell()
						))
						curLink = inFile.read(int(x_size, 16))

						if target:
							outFile.write(re_href.sub(
								b' href="./' + target + b'"',
								curLink,
							))
							continue

						if not entry_url_fmt:
							outFile.write(curLink.replace(
								b' href="#',
								b' class="broken" href="#',
							))
							continue

						_st = curLink.decode("utf-8")
						i = _st.find('href="#')
						j = _st.find('"', i + 7)
						word = _st[i + 7:j]
						url = entry_url_fmt.format(word=word)
						outFile.write((
							_st[:i] +
							f'class="broken" href="{url}"' +
							_st[j + 1:]
						).encode("utf-8"))

					outFile.write(inFile.read())

			os.rename(join(dirn, f"{filename}.new"), join(dirn, filename))
			os.remove(join(dirn, f"links{fileIndex}"))

	def writeInfo(self, filename, header):
		glos = self._glos
		title = glos.getInfo("name")
		encoding = self._encoding
		customStyle = (
			'table, th, td {border: 1px solid black; '
			'border-collapse: collapse; padding: 5px;}'
		)
		infoHeader = header.format(
			pageTitle=f"Info: {title}",
			customStyle=customStyle,
		)
		with open(
			join(filename, "info.html"),
			mode="w",
			encoding="utf-8",
		) as _file:
			_file.write(
				infoHeader +
				'<table>'
				'<tr>'
				'<th width="%10">Key</th>'
				'<th width="%90">Value</th>'
				'</tr>\n'
			)
			for key, value in glos.iterInfo():
				_file.write(
					f'<tr><td>{key}</td><td>{value}</td></tr>\n'
				)
			_file.write("</table></body></html>")

	def write(self) -> "Generator[None, BaseEntry, None]":

		encoding = self._encoding
		resources = self._resources
		max_file_size = self._max_file_size
		filename_format = self._filename_format
		escape_defi = self._escape_defi

		wordSep = ' <font color="red">|</font> '

		initFileSizeMax = 100

		glos = self._glos

		filename = self._filename
		self._encoding = encoding
		self._filename_format = filename_format

		entry_url_fmt = glos.getInfo("entry_url")

		def getEntryWebLink(entry) -> str:
			if not entry_url_fmt:
				return ""
			url = entry_url_fmt.format(word=html.escape(entry.l_word[0]))
			return f'{nbsp}<a class="no_ul" href="{url}">&#127759;</a>'

		# from math import log2, ceil
		# maxPosHexLen = int(ceil(log2(max_file_size) / 4))

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
		style = ""
		if self._dark:
			style = darkStyle

		if self._css:
			cssLink = '<link rel="stylesheet" href="style.css" />'
		else:
			cssLink = ""

		header = (
			'<!DOCTYPE html>\n'
			'<html><head>'
			f'<title>{{pageTitle}}</title>'
			f'<meta charset="{encoding}">'
			f'<style type="text/css">{style}{{customStyle}}</style>{cssLink}'
			'</meta></head><body>\n'
		)

		def pageHeader(n: int):
			return header.format(
				pageTitle=f"Page {n} of {title}",
				customStyle="",
			)

		def navBar() -> str:
			links = []
			if len(self._filenameList) > 1:
				links.append(f'<a href="./{self._filenameList[-2]}">&#9664;</a>')
			links.append(f'<a href="./{self.getNextFilename()}">&#9654;</a>')
			links.append(f'<a href="./info.html">ℹ️</a></div>')
			return (
				'<nav style="text-align: center; font-size: 2.5em;">' +
				f'{nbsp}{nbsp}{nbsp}'.join(links) +
				'</nav>'
			)

		tailSize = len(self._tail.encode(encoding))

		if max_file_size < len(header) + tailSize:
			raise ValueError(f"max_file_size={max_file_size} is too small")

		max_file_size -= tailSize

		if not isdir(self._filename):
			os.mkdir(self._filename)

		fileObj = self.nextFile()
		fileObj.write(pageHeader(0))
		fileObj.write(navBar())

		re_fixed_link = re.compile(
			r'<a (?:[^<>]*? )?href="#([^<>"]+?)">[^<>]+?</a>',
			re.I,
		)

		linkTargetSet = set()

		def replaceBword(text) -> str:
			return text.replace(
				' href="bword://',
				' href="#',
			)

		def addLinks(text: str, pos: int) -> str:
			for m in re_fixed_link.finditer(text):
				if ' class="entry_link"' in m.group(0):
					continue
				if m.group(0).count("href=") != 1:
					log.error(f"unexpected match: {m.group(0)}")
				target = html.unescape(m.group(1))
				linkTargetSet.add(target)
				start = m.start()
				b_start = len(text[:start].encode(encoding))
				b_size = len(text[start:m.end()].encode(encoding))
				linksTxtFileObj.write(
					f"{escapeNTB(target)}\t"
					f"{len(self._filenameList)-1}\t"
					f"{hex(pos+b_start)[2:]}\t"
					f"{hex(b_size)[2:]}\n"
				)
				linksTxtFileObj.flush()

		self.writeInfo(filename, header)

		_word_title = self._word_title

		resDir = self._resDir
		entryIndex = -1
		while True:
			entryIndex += 1
			entry = yield
			if entry is None:
				break
			if entry.isData():
				if resources:
					entry.save(resDir)
				continue

			if entry.defi.startswith('<!DOCTYPE html>') and defiFormat != "h":
				log.error(f"bad defiFormat={defiFormat}")
				defiFormat = "h"

			entry.detectDefiFormat()
			entry.stripFullHtml()
			defi = entry.defi
			defiFormat = entry.defiFormat

			if defiFormat == "m":
				defi = html.escape(defi)
				if "\n" in defi:
					# could be markdown or unformatted plaintext
					# FIXME: this changes the font to a monospace
					defi = f'<pre>{defi}</pre>'
			elif defiFormat == "h":
				if escape_defi:
					defi = html.escape(defi)
				defi = defi.replace(' src="./', ' src="./res/')

			entryId = f"entry{entryIndex}"

			if _word_title:
				words = [
					html.escape(word)
					for word in entry.l_word
				]
				title = glos.wordTitleStr(
					wordSep.join(words),
					sample=entry.l_word[0],
					_class="headword",
				)

			if not title:
				title = f'Entry {entryIndex}'

			# entry_link_sym = "&#182;"
			entry_link_sym = "&#128279;"
			text = (
				f'<div id="{entryId}">{title}{nbsp}{nbsp}'
				f'<a class="no_ul" class="entry_link" href="#{entryId}">'
				f'{entry_link_sym}</a>'
				f'{getEntryWebLink(entry)}'
				f"<br>\n{defi}"
				'</div>\n'
				'<hr>\n'
			)
			pos = fileObj.tell()
			if pos > initFileSizeMax:
				if pos > max_file_size - len(text.encode(encoding)):
					fileObj = self.nextFile()
					fileObj.write(pageHeader(
						len(self._filenameList) - 1
					))
					fileObj.write(navBar())
			pos = fileObj.tell()
			tmpFilename = escapeNTB(self._filenameList[-1])
			for word in entry.l_word:
				indexTxtFileObj.write(
					f"{entryIndex}\t"
					f"{escapeNTB(word)}\t"
					f"{tmpFilename}\t"
					f"{pos}\n"
				)
			del tmpFilename
			text = replaceBword(text)
			addLinks(text, pos)
			fileObj.write(text)

		fileObj.close()
		self._fileObj = None
		indexTxtFileObj.close()

		if linkTargetSet:
			log.info(f"{len(linkTargetSet)} link targets found")
			log.info("Fixing links, please wait...")
			self.fixLinks(linkTargetSet)

		os.remove(join(filename, "links.txt"))
