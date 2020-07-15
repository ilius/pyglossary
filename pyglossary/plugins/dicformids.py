# -*- coding: utf-8 -*-
import re

from tabfile import Reader as TabfileReader
from formats_common import *

enable = True
format = "Dicformids"
description = "DictionaryForMIDs"
extensions = (".mids",)
tools = [
	{
		"name": "DictionaryForMIDs",
		"web": "http://dictionarymid.sourceforge.net/",
		"platforms": ["Android", "Web", "Windows", "Linux", "Mac"],
		# PC version is Java-based
		"license": "GPL",
	},
]
optionsProp = {}
depends = {}


PROP_TEMPLATE = """#DictionaryForMIDs property file
infoText={name}, author: {author}
indexFileMaxSize={indexFileMaxSize}\n
language1IndexNumberOfSourceEntries={wordCount}
language1DictionaryUpdateClassName=de.kugihan.dictionaryformids.dictgen.DictionaryUpdate
indexCharEncoding=ISO-8859-1
dictionaryFileSeparationCharacter='\\t'
language2NormationClassName=de.kugihan.dictionaryformids.translation.Normation
language2DictionaryUpdateClassName=de.kugihan.dictionaryformids.dictgen.DictionaryUpdate
logLevel=0
language1FilePostfix={directoryPostfix}
dictionaryCharEncoding=UTF-8
numberOfAvailableLanguages=2
language1IsSearchable=true
language2GenerateIndex=false
dictionaryFileMaxSize={dicMaxSize}
language2FilePostfix={language2FilePostfix}
searchListFileMaxSize=20000
language2IsSearchable=false
fileEncodingFormat=plain_format1
language1HasSeparateDictionaryFile=true
searchListCharEncoding=ISO-8859-1
searchListFileSeparationCharacter='\t'
indexFileSeparationCharacter='\t'
language1DisplayText={sourceLang}
language2HasSeparateDictionaryFile=false
dictionaryGenerationInputCharEncoding=UTF-8
language1GenerateIndex=true
language2DisplayText={targetLang}
language1NormationClassName=de.kugihan.dictionaryformids.translation.NormationEng
"""


class Reader(object):
	re_number = re.compile(r"\d+")

	def __init__(self, glos):
		self._glos = glos
		self._tabFileNames = []
		self._tabFileReader = None

	def open(self, dirname):
		self._dirname = dirname
		dicFiles = []
		orderFileNames = []
		for fname in os.listdir(dirname):
			if not fname.startswith("directory"):
				continue
			try:
				num = self.re_number.findall(fname)[-1]
			except IndexError:
				pass
			else:
				orderFileNames.append((num, fname))
		orderFileNames.sort(
			key=lambda x: x[0],
			reverse=True,
		)
		self._tabFileNames = [x[1] for x in orderFileNames]
		self.nextTabFile()

	def __len__(self):  # FIXME
		raise NotImplementedError

	def __iter__(self):
		return self

	def __next__(self):
		for _ in range(10):
			try:
				return next(self._tabFileReader)
			except StopIteration:
				self._tabFileReader.close()
				self.nextTabFile()

	def nextTabFile(self):
		try:
			tabFileName = self._tabFileNames.pop()
		except IndexError:
			raise StopIteration
		self._tabFileReader = TabfileReader(self._glos, hasInfo=False)
		self._tabFileReader.open(join(self._dirname, tabFileName))

	def close(self):
		if self._tabFileReader:
			try:
				self._tabFileReader.close()
			except:
				pass
		self._tabFileReader = None
		self._tabFileNames = []


class Writer(object):
	def __init__(self, glos):
		self._glos = glos
		self.linesPerDirectoryFile = 500  # 200
		self.indexFileMaxSize = 32722  # 30000
		self.directoryPostfix = ""
		self.indexPostfix = "Eng"
		self.dirname = ""

	def writeGetIndexGen(self):
		dicMaxSize = 0
		wordCount = 0
		for dicIndex, entryList in enumerate(
			self._glos.iterEntryBuckets(
				self.linesPerDirectoryFile
			)
		):
			# assert len(entryList) == 200
			dicFp = open(join(
				self.dirname,
				f"directory{self.directoryPostfix}{dicIndex+1}.csv",
			), "w")
			for entry in entryList:
				if entry.isData():
					# FIXME
					continue

				wordCount += 1
				word = entry.s_word
				defi = entry.defi
				dicLine = word + "\t" + defi + "\n"
				dicPos = dicFp.tell()
				dicFp.write(dicLine)
				yield word, dicIndex+1, dicPos

			dicMaxSize = max(dicMaxSize, dicFp.tell())
			dicFp.close()
		self.dicMaxSize = dicMaxSize
		self.wordCount = wordCount

	def writeProbs(self):
		glos = self._glos
		with open(join(
			self.dirname,
			"DictionaryForMIDs.properties",
		), "w") as fileObj:
			fileObj.write(PROP_TEMPLATE.format(
				name=glos.getInfo("name"),
				author=glos.getAuthor(),
				indexFileMaxSize=self.indexFileMaxSize,
				wordCount=self.wordCount,
				directoryPostfix=self.directoryPostfix,
				dicMaxSize=self.dicMaxSize+1,
				language2FilePostfix="fa",  # FIXME
				sourceLang=glos.getInfo("sourceLang"),
				targetLang=glos.getInfo("targetLang"),
			))
#			open(join(
#				self.dirname,
#				f"searchlist{self.directoryPostfix}.csv"
#			), "w")  # FIXME

	def nextIndex(self):
		try:
			self.indexFp.close()
		except AttributeError:
			self.indexIndex = 0

		self.indexIndex += 1
		fname = f"index{self.indexPostfix}{self.indexIndex}.csv"
		fpath = join(self.dirname, fname)
		self.indexFp = open(fpath, "w")

	def write(self, dirname: str):
		self.dirname = dirname
		if not os.path.isdir(dirname):
			os.mkdir(dirname)
		self.nextIndex()
		for word, dicIndex, dicPos in self.writeGetIndexGen():
			indexLine = f"{word}\t{dicIndex+1}-{dicPos}-B\n"
			if (
				self.indexFp.tell() + len(indexLine)
			) > self.indexFileMaxSize - 10:
				self.nextIndex()
			self.indexFp.write(indexLine)
		self.indexFp.close()
		self.writeProbs()

	# def close(self):
	#	pass

