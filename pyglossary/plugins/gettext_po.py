# -*- coding: utf-8 -*-

from formats_common import *

enable = True
format = "GettextPo"
description = "Gettext Source (po)"
extensions = [".po"]
optionsProp = {
	"resources": BoolOption(),
}
depends = {
	"polib": "polib",
}


class Reader(object):
	def __init__(self, glos: GlossaryType):
		self._glos = glos
		self.clear()

	def clear(self):
		self._filename = ""
		self._file = None
		self._wordCount = None
		self._resDir = ""
		self._resFileNames = []

	def open(self, filename):
		self._filename = filename
		self._file = open(filename)
		self._resDir = filename + "_res"
		if isdir(self._resDir):
			self._resFileNames = os.listdir(self._resDir)
		else:
			self._resDir = ""
			self._resFileNames = []

	def close(self):
		if self._file:
			self._file.close()
		self.clear()

	def __len__(self):
		from pyglossary.file_utils import fileCountLines
		if self._wordCount is None:
			log.debug("Try not to use len(reader) as it takes extra time")
			self._wordCount = fileCountLines(
				self._filename,
				newline="\nmsgid",
			)
		return self._wordCount

	def __iter__(self):
		try:
			from polib import unescape as po_unescape
		except ModuleNotFoundError as e:
			e.msg += ", run `sudo pip3 install polib` to install"
			raise e
		word = ""
		defi = ""
		msgstr = False
		wordCount = 0
		for line in self._file:
			line = line.strip()
			if not line:
				continue
			if line.startswith("#"):
				continue
			if line.startswith("msgid "):
				if word:
					yield self._glos.newEntry(word, defi)
					wordCount += 1
					word = ""
					defi = ""
				else:
					pass
					# TODO: parse defi and set glos info?
					# but this should be done in self.open
				word = po_unescape(line[6:])
				msgstr = False
			elif line.startswith("msgstr "):
				if msgstr:
					log.error("msgid omitted!")
				defi = po_unescape(line[7:])
				msgstr = True
			else:
				if msgstr:
					defi += po_unescape(line)
				else:
					word += po_unescape(line)
		if word:
			yield self._glos.newEntry(word, defi)
			wordCount += 1
		self._wordCount = wordCount


def write(glos: GlossaryType, filename: str, resources: bool = True):
	try:
		from polib import escape as po_escape
	except ModuleNotFoundError as e:
		e.msg += ", run `sudo pip3 install polib` to install"
		raise e
	with open(filename, "w") as toFile:
		toFile.write('#\nmsgid ""\nmsgstr ""\n')
		for key, value in glos.iterInfo():
			toFile.write(f'"{key}: {value}\\n"\n')
		for entry in glos:
			if entry.isData():
				if resources:
					entry.save(filename + "_res")
				continue
			word = entry.getWord()
			defi = entry.getDefi()
			toFile.write(
				f"msgid {po_escape(word)}\n"
				f"msgstr {po_escape(defi)}\n\n"
			)
