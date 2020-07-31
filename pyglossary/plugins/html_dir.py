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
b.headword {{ font-size: 1.5em; color: #c7ffb9; }}
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
		self._filename_format = "{n:05d}.html"
		self._tail = "</body></html>"
		self._filenameList = []

	def nextFile(self):
		if self._fileObj:
			self._fileObj.write(self._tail)
			self._fileObj.close()
		currentFilename = self._filename_format.format(
			n=len(self._filenameList)
		)
		self._filenameList.append(currentFilename)
		self._fileObj = open(
			join(
				self._filename,
				currentFilename,
			),
			mode="w",
			encoding=self._encoding,
		)
		return self._fileObj

	def fixCrossFileLinks(self, linkTargetSet):
		import gc

		gc.collect()
		dirn = self._filename

		filenameList = self._filenameList

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

		linksByFile = [
			open(join(dirn, f"links{i}"), "w", encoding="utf-8")
			for i in range(len(filenameList))
		]
		log.info("")
		for line in open(join(dirn, "links.txt"), encoding="utf-8"):
			line = line.rstrip("\n")
			if not line:
				continue
			target, fileIndex, x_start, x_size = line.split("\t")
			target = unescapeNTB(target)
			if target not in fileByWord:
				targetFilename = ""
			else:
				targetFilename = fileByWord[target]
				if targetFilename == filename:
					continue
			_file = linksByFile[int(fileIndex)]
			_file.write(
				f"{x_start}\t{x_size}\t{targetFilename}\n"
			)
			_file.flush()

		for _file in linksByFile:
			_file.close()
		del linksByFile

		linkTargetSet.clear()
		del fileByWord, linkTargetSet
		gc.collect()

		for fileIndex, filename in enumerate(filenameList):
			with open(join(dirn, filename), mode="rb") as inFile:
				with open(join(dirn, f"{filename}.new"), mode="wb") as outFile:
					for linkLine in open(join(dirn, f"links{fileIndex}"), "rb"):
						linkLine = linkLine.rstrip(b"\n")
						x_start, x_size, targetFilename = linkLine.split(b"\t")
						outFile.write(inFile.read(
							int(x_start, 16) - inFile.tell()
						))
						curLink = inFile.read(int(x_size, 16))
						if not targetFilename:
							outFile.write(curLink.replace(
								b' href="#',
								b' class="broken" href="#',
							))
						else:
							outFile.write(curLink.replace(
								b' href="#',
								b' href="./' + targetFilename + b'#',
							))
						outFile.flush()
					outFile.write(inFile.read())
			os.rename(join(dirn, f"{filename}.new"), join(dirn, filename))
			os.remove(join(dirn, f"links{fileIndex}"))

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
					f"{len(self._filenameList)-1}\t"
					f"{hex(pos+b_start)[2:]}\t"
					f"{hex(b_size)[2:]}\n"
				)
				linksTxtFileObj.flush()

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
			words_escaped = html.escape(words_str)
			text = (
				f'<div id="{words_escaped}">'
				f'<b class="headword">{words_str}</b>'
				'&nbsp;&nbsp;'
				f'<a href="#{words_escaped}">&#128279;</a>'
				f"<br>\n{defi}"
				'</div>\n'
				'<hr>\n'
			)
			pos = fileObj.tell()
			if pos > initFileSizeMax:
				if pos > max_file_size - len(text.encode(encoding)):
					fileObj = self.nextFile()
					fileObj.write(header.format(
						n=len(self._filenameList) - 1
					))
			s_word = entry.s_word
			pos = fileObj.tell()
			indexTxtFileObj.write(
				f"{escapeNTB(s_word)}\t"
				f"{escapeNTB(self._filenameList[-1])}\t"
				f"{pos}\n"
			)
			text = fixLinks(text)
			addLinks(s_word, text, pos)
			fileObj.write(text)

		fileObj.close()
		self._fileObj = None
		indexTxtFileObj.close()

		if linkTargetSet:
			log.info(f"\n{len(linkTargetSet)} link targets found")
			log.info("Fixing cross-file links, please wait...")
			self.fixCrossFileLinks(linkTargetSet)

		os.remove(join(filename, "links.txt"))
