# -*- coding: utf-8 -*-
# mypy: ignore-errors
from __future__ import annotations

import os
import re
from os.path import join
from typing import TYPE_CHECKING

from pyglossary.core import log

if TYPE_CHECKING:
	from collections.abc import Generator

	from pyglossary.glossary_types import EntryType, WriterGlossaryType

__all__ = ["Writer"]

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


class Writer:
	def __init__(self, glos: WriterGlossaryType) -> None:
		self._glos = glos
		self.linesPerDirectoryFile = 500  # 200
		self.indexFileMaxSize = 32722  # 30000
		self.directoryPostfix = ""
		self.indexPostfix = ""
		self._dirname = ""
		# looks like we need to remove tabs, because app gives error
		# but based on the java code, all punctuations should be removed
		# as well, including '|'
		self.re_punc = re.compile(
			r"""[!"$§%&/()=?´`\\{}\[\]^°+*~#'\-_.:,;<>@|]*""",  # noqa: RUF001
		)
		self.re_spaces = re.compile(" +")
		self.re_tabs = re.compile("\t+")

	def normateWord(self, word: str) -> str:
		word = word.strip()
		word = self.re_punc.sub("", word)
		word = self.re_spaces.sub(" ", word)
		word = self.re_tabs.sub(" ", word)
		word = word.lower()
		return word  # noqa: RET504

	def writeProbs(self) -> None:
		glos = self._glos
		probsPath = join(
			self._dirname,
			"DictionaryForMIDs.properties",
		)
		with open(probsPath, mode="w", newline="\n", encoding="utf-8") as fileObj:
			fileObj.write(
				PROP_TEMPLATE.format(
					name=glos.getInfo("name"),
					author=glos.author,
					indexFileMaxSize=self.indexFileMaxSize,
					wordCount=self.wordCount,
					directoryPostfix=self.directoryPostfix,
					dicMaxSize=self.dicMaxSize + 1,
					language2FilePostfix="fa",  # FIXME
					sourceLang=glos.sourceLangName,
					targetLang=glos.targetLangName,
				),
			)

	def nextIndex(self) -> None:
		try:
			self.indexFp.close()
		except AttributeError:
			self.indexIndex = 0

		self.indexIndex += 1
		fname = f"index{self.indexPostfix}{self.indexIndex}.csv"
		fpath = join(self._dirname, fname)
		self.indexFp = open(fpath, mode="w", encoding="utf-8", newline="\n")

	def finish(self) -> None:
		pass

	def open(self, dirname: str) -> None:
		self._dirname = dirname
		if not os.path.isdir(dirname):
			os.mkdir(dirname)

	def write(self) -> Generator[None, EntryType, None]:
		self.nextIndex()

		dicMaxSize = 0
		indexData: list[tuple[str, int, int]] = []

		def writeBucket(dicIndex: int, entryList: list[EntryType]) -> None:
			nonlocal dicMaxSize
			log.debug(
				f"{dicIndex=}, {len(entryList)=}, {dicMaxSize=}",
			)
			dicFp = open(
				join(
					self._dirname,
					f"directory{self.directoryPostfix}{dicIndex + 1}.csv",
				),
				mode="w",
				encoding="utf-8",
				newline="\n",
			)
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
		entryList: list[EntryType] = []  # aka bucket
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
			entryList = []

		self.dicMaxSize = dicMaxSize
		self.wordCount = wordCount

		langSearchListFp = open(
			join(
				self._dirname,
				f"searchlist{self.directoryPostfix}.csv",
			),
			mode="w",
			newline="\n",
			encoding="utf-8",
		)

		langSearchListFp.write(f"{indexData[0][0]}\t{self.indexIndex}\n")

		for word, dicIndex, dicPos in indexData:
			indexLine = f"{word}\t{dicIndex}-{dicPos}-B\n"
			if (self.indexFp.tell() + len(indexLine)) > self.indexFileMaxSize - 10:
				self.nextIndex()
				langSearchListFp.write(f"{word}\t{self.indexIndex}\n")
			self.indexFp.write(indexLine)

		self.indexFp.close()
		langSearchListFp.close()

		self.writeProbs()
