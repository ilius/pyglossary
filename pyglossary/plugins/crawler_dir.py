from formats_common import *
from hashlib import sha1
from os.path import dirname
from os import makedirs, listdir
from pyglossary.text_utils import (
	escapeNTB,
	splitByBarUnescapeNTB,
)
from pyglossary.compression import (
	compressionOpenFunc,
)

enable = True
format = "CrawlerDir"
description = "Crawler Directory"
extensions = (".crawler",)
singleFile = True
optionsProp = {
	"compression": StrOption(
		values=["", "gz", "bz2", "lzma"],
		comment="Compression Algorithm",
	),
}


class Writer(object):
	_compression: str = ""

	def __init__(self, glos: GlossaryType) -> None:
		self._glos = glos
		self._filename = None

	def finish(self):
		pass

	def open(self, filename: str):
		self._filename = filename
		if not isdir(filename):
			makedirs(filename)

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

	def write(self, ):
		from collections import OrderedDict as odict
		from pyglossary.json_utils import dataToPrettyJson

		filename = self._filename

		wordCount = 0
		compression = self._compression
		c_open = compressionOpenFunc(compression)
		if not c_open:
			raise ValueError(f"invalid compression {c!r}")
		while True:
			entry = yield
			if entry is None:
				break
			if entry.isData():
				continue
			fpath = join(filename, self.filePathFromWord(entry.b_word))
			if compression:
				fpath = f"{fpath}.{compression}"
			parentDir = dirname(fpath)
			if not isdir(parentDir):
				makedirs(parentDir)
			if isfile(fpath):
				log.warn(f"file exists: {fpath}")
				fpath += f"-{sha1(entry.b_defi).hexdigest()[:4]}"
			with c_open(fpath, "wt", encoding="utf-8") as _file:
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
		_, ext = splitext(fpath)
		c_open = compressionOpenFunc(ext.lstrip("."))
		if not c_open:
			log.error(f"invalid extention {ext}")
			c_open = open
		with c_open(fpath, "rt", encoding="utf-8") as _file:
			words = splitByBarUnescapeNTB(_file.readline().rstrip("\n"))
			defi = _file.read()
			return self._glos.newEntry(words, defi)

	def _listdirSortKey(self, name):
		name_nox, ext = splitext(name)
		if ext == ".d":
			return name
		return name_nox

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
		children.sort(key=self._listdirSortKey)
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
