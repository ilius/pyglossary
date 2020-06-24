# -*- coding: utf-8 -*-
# http://www.octopus-studio.com/download.en.htm

from formats_common import *
from collections import OrderedDict

enable = True
format = "OctopusMdictSource"
description = "Octopus MDict Source"
extensions = (".mtxt",)
singleFile = True
optionsProp = {
	"encoding": EncodingOption(),
	"links": BoolOption(),
	"resources": BoolOption(),
}
depends = {}


class Reader(object):
	def __init__(self, glos):
		self._glos = glos
		self._filename = ""
		self._encoding = "utf-8"
		self._file = None
		self._wordCount = 0

		# dict of mainWord -> newline-separated altenatives
		self._linksDict = {}  # type: Dict[str, str]

	def __len__(self):
		return self._wordCount

	def close(self):
		if self._file:
			self._file.close()
		self._file = None

	def open(
		self,
		filename,
		encoding="utf-8",
	):
		self._filename = filename
		self._encoding = encoding
		self._file = open(filename, encoding=encoding)
		self.loadLinks()

	def loadLinks(self):
		linksDict = {}
		word = ""
		wordCount = 0
		for line in self._file:
			line = line.strip()
			if line == "</>":
				word = ""
				continue
			if line.startswith("@@@LINK="):
				if not word:
					log.warn(f"unexpected line: {line}")
					continue
				mainWord = line[8:]
				if mainWord in linksDict:
					linksDict[mainWord] += "\n" + word
				else:
					linksDict[mainWord] = word
				continue
			if not word:
				word = line
			else:
				wordCount += 1

		log.info(f"wordCount = {wordCount}")
		self._linksDict = linksDict
		self._wordCount = wordCount
		self._file = open(self._filename, encoding=self._encoding)

	def __iter__(self):
		linksDict = self._linksDict
		word, defi = "", ""
		glos = self._glos

		def newEntry():
			words = word
			altsStr = linksDict.get(word, "")
			if altsStr:
				words = [word] + altsStr.split("\n")
			return glos.newEntry(words, defi)

		for line in self._file:
			line = line.strip()
			if line == "</>":
				if defi:
					yield newEntry()
				word, defi = "", ""
				continue
			if line.startswith("@@@LINK="):
				continue
			if word:
				defi = line
			else:
				word = line

		if word:
			yield newEntry()


def writeEntryGen(glos):
	for entry in glos:
		words = entry.getWords()
		defis = entry.getDefis()

		yield glos.newEntry(words[0], defis)

		for alt in words[1:]:
			yield glos.newEntry(
				alt,
				"@@@LINK=" + words[0],
			)


def write(
	glos,
	filename,
	resources=True,
):
	glos.writeTxt(
		"\n",
		"\n</>\n",
		filename=filename,
		writeInfo=False,
		rplList=[
			("bword://", "entry://"),
		],
		ext=".mtxt",
		head="",
		iterEntries=writeEntryGen(glos),
		newline="\r\n",
		resources=resources,
	)
