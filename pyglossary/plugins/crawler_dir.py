from formats_common import *
from hashlib import sha1
from os.path import dirname
from os import makedirs, listdir
from pyglossary.text_utils import (
	escapeNTB,
	splitByBarUnescapeNTB,
)

enable = True
format = "CrawlerDir"
description = "Crawler Directory"
extensions = (".crawler",)
singleFile = True
optionsProp = {
}


class Writer(object):
	def __init__(self, glos: GlossaryType) -> None:
		self._glos = glos

	def filePathFromWord(self, b_word: bytes) -> str:
		bw = b_word.lower()
		if len(bw) <= 2:
			return bw.hex()
		if len(bw) <= 4:
			return join(
				bw[:2].hex() + ".d",
				bw[2:].hex(),
			)
		return join(
			bw[:2].hex() + ".d",
			bw[2:4].hex() + ".d",
			bw[4:8].hex() + "-" + sha1(b_word).hexdigest()[:8],
		)

	def write(self, filename: str):
		from collections import OrderedDict as odict
		from pyglossary.json_utils import dataToPrettyJson

		if not isdir(filename):
			makedirs(filename)

		wordCount = 0
		while True:
			entry = yield
			if entry is None:
				break
			if entry.isData():
				continue
			fpath = join(filename, self.filePathFromWord(entry.b_word))
			parentDir = dirname(fpath)
			if not isdir(parentDir):
				makedirs(parentDir)
			if isfile(fpath):
				log.warn(f"file exists: {fpath}")
				fpath += f"-{sha1(entry.b_defi).hexdigest()[:4]}"
			with open(fpath, "w", encoding="utf-8") as _file:
				_file.write(
					f"{escapeNTB(entry.s_word)}\n{entry.defi}"
				)
			wordCount += 1

		with open(
			join(filename, "info.json"),
			mode="w",
			encoding="utf-8",
		) as infoFile:
			info = odict()
			info["name"] = self._glos.getInfo("name")
			info["wordCount"] = wordCount
			for key, value in self._glos.getExtraInfos((
				"name",
				"wordCount",
			)).items():
				info[key] = value
			infoFile.write(dataToPrettyJson(info))


class Reader(object):
	def __init__(self, glos: GlossaryType) -> None:
		self._glos = glos
		self._filename = None
		self._wordCount = 0

	def open(self, filename: str):
		from pyglossary.json_utils import jsonToOrderedData

		self._filename = filename

		with open(join(filename, "info.json"), "r", encoding="utf-8") as infoFp:
			info = jsonToOrderedData(infoFp.read())
		self._wordCount = info.pop("wordCount")
		for key, value in info.items():
			self._glos.setInfo(key, value)

	def close(self):
		pass

	def __len__(self):
		return self._wordCount

	def _fromFile(self, fpath):
		with open(fpath, "r", encoding="utf-8") as _file:
			words = splitByBarUnescapeNTB(_file.readline().rstrip("\n"))
			defi = _file.read()
			return self._glos.newEntry(words, defi)

	def _readDir(
		self,
		dpath: str,
		exclude: "Optional[Set[str]]",
	):
		children = listdir(dpath)
		if exclude:
			children = [
				name for name in children
				if name not in exclude
			]
		children.sort()
		for name in children:
			cpath = join(dpath, name)
			if isfile(cpath):
				yield self._fromFile(cpath)
				continue
			if isdir(cpath):
				yield from self._readDir(cpath, None)
				continue
			log.error(f"Not a file nor a directory: {cpath}")

	def __iter__(self):
		yield from self._readDir(
			self._filename,
			{
				"info.json",
			},
		)
