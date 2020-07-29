# -*- coding: utf-8 -*-

from formats_common import *
from pyglossary.text_utils import escapeNTB
import html

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
}


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

	def write(
		self,
		filename: str,
		encoding: str = "utf-8",
		resources: bool = True,
		max_file_size: int = 102400,
		filename_format: str = "{n:05d}.html",
		escape_defi: bool = False,
	) -> Generator[None, "BaseEntry", None]:
		if max_file_size < 100:
			raise ValueError(f"max_file_size={max_file_size} is too small")

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

		title = glos.getInfo("name")
		header = (
			'<!DOCTYPE html>\n'
			'<html><head>'
			f'<title>Page {{n}} of {title}</title>'
			f'<meta charset="{encoding}">'
			'</head><body>\n'
		)

		tailSize = len(self._tail.encode(encoding))
		max_file_size -= tailSize

		if not isdir(self._filename):
			os.mkdir(self._filename)

		fileObj = self.nextFile()
		fileObj.write(header.format(n=0))

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
			text = f"<b>{words_str}</b><br>\n{defi}\n<hr>\n"
			pos = fileObj.tell()
			if pos > initFileSizeMax:
				if pos > max_file_size - len(text.encode(encoding)):
					fileObj = self.nextFile()
					fileObj.write(header.format(n=self._fileIndex - 1))
			indexTxtFileObj.write(
				f"{escapeNTB(entry.s_word)}\t"
				f"{self._currentFilename}\t"
				f"{fileObj.tell()}\n"
			)
			fileObj.write(text)

		fileObj.close()
		self._fileObj = None
		indexTxtFileObj.close()
