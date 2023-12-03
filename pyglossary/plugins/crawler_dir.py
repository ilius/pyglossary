# mypy: ignore-errors

from collections.abc import Generator, Iterator
from hashlib import sha1
from os import listdir, makedirs
from os.path import dirname, isdir, isfile, join, splitext

from pyglossary.compression import (
	compressionOpenFunc,
)
from pyglossary.core import log
from pyglossary.glossary_types import EntryType, GlossaryType
from pyglossary.option import (
	Option,
	StrOption,
)
from pyglossary.text_utils import (
	escapeNTB,
	splitByBarUnescapeNTB,
)

enable = True
lname = "crawler_dir"
format = "CrawlerDir"
description = "Crawler Directory"
extensions = (".crawler",)
extensionCreate = ".crawler/"
singleFile = True
kind = "directory"
wiki = ""
website = None
optionsProp: "dict[str, Option]" = {
	"compression": StrOption(
		values=["", "gz", "bz2", "lzma"],
		comment="Compression Algorithm",
	),
}


class Writer:
	_compression: str = ""

	def __init__(self, glos: GlossaryType) -> None:
		self._glos = glos
		self._filename = None

	def finish(self) -> None:
		pass

	def open(self, filename: str) -> None:
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
			bw[4:8].hex() + "-" + sha1(b_word).hexdigest()[:8],  # noqa: S324
		)

	def write(self) -> None:
		from collections import OrderedDict as odict

		from pyglossary.json_utils import dataToPrettyJson

		filename = self._filename

		wordCount = 0
		compression = self._compression
		c_open = compressionOpenFunc(compression)
		if not c_open:
			raise ValueError(f"invalid compression {compression!r}")
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
				log.warning(f"file exists: {fpath}")
				fpath += f"-{sha1(entry.b_defi).hexdigest()[:4]}"  # noqa: S324
			with c_open(fpath, "wt", encoding="utf-8") as _file:
				_file.write(
					f"{escapeNTB(entry.s_word)}\n{entry.defi}",
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


class Reader:
	def __init__(self, glos: GlossaryType) -> None:
		self._glos = glos
		self._filename = None
		self._wordCount = 0

	def open(self, filename: str) -> None:
		from pyglossary.json_utils import jsonToOrderedData

		self._filename = filename

		with open(join(filename, "info.json"), encoding="utf-8") as infoFp:
			info = jsonToOrderedData(infoFp.read())
		self._wordCount = info.pop("wordCount")
		for key, value in info.items():
			self._glos.setInfo(key, value)

	def close(self) -> None:
		pass

	def __len__(self) -> int:
		return self._wordCount

	def _fromFile(self, fpath: str) -> "EntryType":
		_, ext = splitext(fpath)
		c_open = compressionOpenFunc(ext.lstrip("."))
		if not c_open:
			log.error(f"invalid extension {ext}")
			c_open = open
		with c_open(fpath, "rt", encoding="utf-8") as _file:
			words = splitByBarUnescapeNTB(_file.readline().rstrip("\n"))
			defi = _file.read()
			return self._glos.newEntry(words, defi)

	def _listdirSortKey(self, name: str) -> str:
		name_nox, ext = splitext(name)
		if ext == ".d":
			return name
		return name_nox

	def _readDir(
		self,
		dpath: str,
		exclude: "set[str] | None",
	) -> "Generator[None, EntryType, None]":
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

	def __iter__(self) -> "Iterator[EntryType]":
		yield from self._readDir(
			self._filename,
			{
				"info.json",
			},
		)
