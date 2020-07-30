# -*- coding: utf-8 -*-

from formats_common import *
from pyglossary.text_utils import escapeNTB, unescapeNTB
import html
import os

enable = True
format = "HtmlDir"
description = "HTML Directory"
extensions = ()
singleFile = False
optionsProp = {
	"encoding": EncodingOption(),
	"resources": BoolOption(),
	"max_file_size": IntOption(),
	"filename_format": StrOption(),
	"escape_defi": BoolOption(),
	"dark": BoolOption(),
}


darkStyle = """
body {{
	background-color: #373737;
	color: #eee;
}}
a {{ color: #aaaaff; }}
a.broken {{ color: #e0c0c0; }}
h1 {{ font-size: 1.5em; color: #c7ffb9;}}
h2 {{ font-size: 1.3em;}}
h3 {{ font-size: 1.0em;}}
h4 {{ font-size: 1.0em;}}
h5 {{ font-size: 1.0em;}}
h6 {{ font-size: 1.0em;}}
"""


class Writer(object):
	def __init__(self, glos: GlossaryType):
		self._glos = glos
		self._filename = None
		self._fileObj = None
		self._encoding = "utf-8"
		self._fileIndex = 0
		self._filename_format = "{n:05d}.html"
		self._currentFilename = None
		self._tail = "</body></html>"

	def nextFile(self):
		if self._fileObj:
			self._fileObj.write(self._tail)
			self._fileObj.close()
		self._currentFilename = self._filename_format.format(n=self._fileIndex)
		self._fileObj = open(
			join(
				self._filename,
				self._currentFilename,
			),
			mode="w",
			encoding=self._encoding,
		)
		self._fileIndex += 1
		return self._fileObj

	def fixCrossFileLinks(self, linkTargetSet):
		import gc

		gc.collect()
		dirn = self._filename

		brokenLinksFile = open(
			join(dirn, "broken-links.txt"),
			mode="w",
			encoding="utf-8",
		)

		fileByWord = {}
		for line in open(join(dirn, "index.txt"), encoding="utf-8"):
			line = line.rstrip("\n")
			if not line:
				continue
			word, filename, _ = line.split("\t")
			word = unescapeNTB(word)
			if word not in linkTargetSet:
				continue
			fileByWord[word] = filename

		linksByFile = {}
		log.info("")
		for line in open(join(dirn, "links.txt"), encoding="utf-8"):
			line = line.rstrip("\n")
			if not line:
				continue
			parts = line.split("\t")
			if len(parts) != 5:
				log.error(f"invalid link line, {len(parts)} parts: {parts}")
				continue
			target, _, filename, b_start, b_size = parts
			target = unescapeNTB(target)
			if target not in fileByWord:
				brokenLinksFile.write("{target}\n")
				targetFilename = None
			else:
				targetFilename = fileByWord[target]
				if targetFilename == filename:
					continue
				targetFilename = targetFilename.encode(self._encoding)
			linkTuple = (
				int(b_start),
				int(b_size),
				targetFilename,
			)
			if filename in linksByFile:
				linksByFile[filename].append(linkTuple)
			else:
				linksByFile[filename] = [linkTuple]

		brokenLinksFile.close()
		linkTargetSet.clear()
		del fileByWord, linkTargetSet
		gc.collect()

		for filename, linkTuples in linksByFile.items():
			linkTuples.sort()
			with open(join(dirn, filename), mode="rb") as fileObj:
				data = fileObj.read()
			dataPos = 0
			with open(join(dirn, filename), mode="wb") as fileObj:
				for linkTuple in linkTuples:
					start, size, targetFilename = linkTuple
					fileObj.write(data[dataPos:start])
					end = start + size
					if targetFilename is None:
						fileObj.write(data[start:end].replace(
							b' href="#',
							b' class="broken" href="#',
						))
					else:
						fileObj.write(data[start:end].replace(
							b' href="#',
							b' href="./' + targetFilename + b'#',
						))
					dataPos = end
				fileObj.write(data[dataPos:])

	def write(
		self,
		filename: str,
		encoding: str = "utf-8",
		resources: bool = True,
		max_file_size: int = 102400,
		filename_format: str = "{n:05d}.html",
		escape_defi: bool = False,
		dark: bool = True,
	) -> Generator[None, "BaseEntry", None]:

		initFileSizeMax = 100

		glos = self._glos
		resDir = filename + "_res"
		if not isdir(resDir):
			os.mkdir(resDir)

		if not isdir(filename):
			os.mkdir(filename)

		self._filename = filename
		self._encoding = encoding
		self._filename_format = filename_format

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
		if dark:
			style = f'<style type="text/css">{darkStyle}</style>'
		header = (
			'<!DOCTYPE html>\n'
			'<html><head>'
			f'<title>Page {{n}} of {title}</title>'
			f'<meta charset="{encoding}">'
			f'{style}'
			'</head><body>\n'
		)

		tailSize = len(self._tail.encode(encoding))

		if max_file_size < len(header) + tailSize:
			raise ValueError(f"max_file_size={max_file_size} is too small")

		max_file_size -= tailSize

		if not isdir(self._filename):
			os.mkdir(self._filename)

		fileObj = self.nextFile()
		fileObj.write(header.format(n=0))

		re_fixed_link = re.compile(
			r'<a (?:.*? )?href="#([^<>"]*?)">.+?</a>',
			re.I,
		)

		linkTargetSet = set()

		def fixLinks(text) -> str:
			return text.replace(
				' href="bword://',
				' href="#',
			)

		def addLinks(s_word: str, text: str, pos: int) -> str:
			for m in re_fixed_link.finditer(text):
				target = html.unescape(m.group(1))
				linkTargetSet.add(target)
				start = m.start()
				b_start = len(text[:start].encode(encoding))
				b_size = len(text[start:m.end()].encode(encoding))
				linksTxtFileObj.write(
					f"{escapeNTB(target)}\t"
					f"{escapeNTB(s_word)}\t"
					f"{escapeNTB(self._currentFilename)}\t"
					f"{pos + b_start}\t"
					f"{b_size}\n"
				)

		while True:
			entry = yield
			if entry is None:
				break
			if entry.isData():
				if resources:
					entry.save(resDir)
				continue
			words = entry.l_word
			words_str = ' <font color="red">|</font> '.join([
				html.escape(w) for w in words
			])
			defi = entry.defi
			if escape_defi:
				defi = html.escape(defi)
			text = (
				f'<h1 id="{html.escape(words_str)}">{words_str}</h1>'
				f"<br>\n{defi}\n<hr>\n"
			)
			pos = fileObj.tell()
			if pos > initFileSizeMax:
				if pos > max_file_size - len(text.encode(encoding)):
					fileObj = self.nextFile()
					fileObj.write(header.format(n=self._fileIndex - 1))
			s_word = entry.s_word
			pos = fileObj.tell()
			indexTxtFileObj.write(
				f"{escapeNTB(s_word)}\t"
				f"{escapeNTB(self._currentFilename)}\t"
				f"{pos}\n"
			)
			text = fixLinks(text)
			addLinks(s_word, text, pos)
			fileObj.write(text)

		fileObj.close()
		self._fileObj = None
		indexTxtFileObj.close()

		if linkTargetSet:
			self.fixCrossFileLinks(linkTargetSet)

		os.remove(join(filename, "links.txt"))
