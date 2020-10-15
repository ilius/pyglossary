# -*- coding: utf-8 -*-
import re

from tabfile import Reader as TabfileReader
from formats_common import *

enable = True
format = "Dicformids"
description = "DictionaryForMIDs"
extensions = (".mids",)
sortOnWrite = ALWAYS

tools = [
	{
		"name": "DictionaryForMIDs",
		"web": "http://dictionarymid.sourceforge.net/",
		# https://sourceforge.net/projects/dictionarymid/
		"platforms": ["Android", "Web", "Windows", "Linux", "Mac"],
		# PC version is Java-based
		"license": "GPL",
		# android last commit:	2015/02/09
		# android last release:	2015/02/09 - version 1.0.1
	},
]

optionsProp = {}


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
			except Exception:
				pass
		self._tabFileReader = None
		self._tabFileNames = []


class Writer(object):
	def __init__(self, glos):
		self._glos = glos
		self.linesPerDirectoryFile = 500  # 200
		self.indexFileMaxSize = 32722  # 30000
		self.directoryPostfix = ""
		self.indexPostfix = ""
		self._dirname = ""
		self.re_punc = re.compile(
			r"[!\"$§$%&/()=?´`\\{}\[\]^°+*~#'-_.:,;<>@]*",
			# FIXME: |
		)
		self.re_spaces = re.compile(" +")
		self.re_tabs = re.compile("\t+")

	def normateWord(self, word: str) -> str:
		word = word.strip()
		# looks like we need to remove tabs, because app gives error
		# but based on the java code, all punctuations should be removed
		# as well, including '|' which is used to separate alternate words
		# FIXME
		# word = word.replace("|", " ")
		word = self.re_punc.sub("", word)
		word = self.re_spaces.sub(" ", word)
		word = self.re_tabs.sub(" ", word)
		word = word.lower()
		return word

	def sortKey(self, b_word: bytes) -> "Any":
		# DO NOT change method name
		# FIXME: confirm
		word = b_word.decode("utf-8")
		return self.normateWord(word)

	def writeProbs(self):
		glos = self._glos
		with open(join(
			self._dirname,
			"DictionaryForMIDs.properties",
		), "w") as fileObj:
			fileObj.write(PROP_TEMPLATE.format(
				name=glos.getInfo("name"),
				author=glos.getAuthor(),
				indexFileMaxSize=self.indexFileMaxSize,
				wordCount=self.wordCount,
				directoryPostfix=self.directoryPostfix,
				dicMaxSize=self.dicMaxSize + 1,
				language2FilePostfix="fa",  # FIXME
				sourceLang=glos.sourceLangName,
				targetLang=glos.targetLangName,
			))

	def nextIndex(self):
		try:
			self.indexFp.close()
		except AttributeError:
			self.indexIndex = 0

		self.indexIndex += 1
		fname = f"index{self.indexPostfix}{self.indexIndex}.csv"
		fpath = join(self._dirname, fname)
		self.indexFp = open(fpath, mode="w", encoding="utf-8")

	def finish(self):
		pass

	def open(self, dirname: str):
		self._dirname = dirname
		if not os.path.isdir(dirname):
			os.mkdir(dirname)

	def write(self):
		self.nextIndex()

		dicMaxSize = 0
		indexData = []

		def writeBucket(dicIndex: int, entryList: "List[BaseEntry]"):
			nonlocal dicMaxSize
			log.debug(
				f"dicIndex={dicIndex}, len(entryList)={len(entryList)}"
				f", dicMaxSize={dicMaxSize}"
			)
			dicFp = open(join(
				self._dirname,
				f"directory{self.directoryPostfix}{dicIndex+1}.csv",
			), mode="w", encoding="utf-8")
			for entry in entryList:
				word = entry.s_word
				n_word = self.normateWord(word)
				defi = entry.defi
				dicLine = word + "\t" + defi + "\n"
				dicPos = dicFp.tell()
				dicFp.write(dicLine)
				indexData.append((n_word, dicIndex + 1, dicPos))

			dicMaxSize = max(dicMaxSize, dicFp.tell())
			dicFp.close()

		bucketSize = self.linesPerDirectoryFile
		wordCount = 0
		dicIndex = 0
		entryList = []  # aka bucket
		while True:
			entry = yield
			if entry is None:
				break
			if entry.isData():
				# FIXME
				continue
			wordCount += 1
			entryList.append(entry)
			if len(entryList) >= bucketSize:
				writeBucket(dicIndex, entryList)
				dicIndex += 1
				entryList = []

		if entryList:
			writeBucket(dicIndex, entryList)
			entryList = None

		self.dicMaxSize = dicMaxSize
		self.wordCount = wordCount

		langSearchListFp = open(join(
			self._dirname,
			f"searchlist{self.directoryPostfix}.csv"
		), mode="w", encoding="utf-8")

		langSearchListFp.write(f"{indexData[0][0]}\t{self.indexIndex}\n")

		for word, dicIndex, dicPos in indexData:
			indexLine = f"{word}\t{dicIndex}-{dicPos}-B\n"
			if (
				self.indexFp.tell() + len(indexLine)
			) > self.indexFileMaxSize - 10:
				self.nextIndex()
				langSearchListFp.write(f"{word}\t{self.indexIndex}\n")
			self.indexFp.write(indexLine)

		self.indexFp.close()
		langSearchListFp.close()

		self.writeProbs()

	# def close(self):
	#	pass
