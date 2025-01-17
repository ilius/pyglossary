# mypy: ignore-errors
from __future__ import annotations

from hashlib import sha1
from os import makedirs
from os.path import dirname, isdir, isfile, join
from typing import TYPE_CHECKING

from pyglossary.compression import (
	compressionOpenFunc,
)
from pyglossary.core import log
from pyglossary.text_utils import (
	escapeNTB,
)

if TYPE_CHECKING:
	from pyglossary.glossary_types import WriterGlossaryType

__all__ = ["Writer"]


class Writer:
	_compression: str = ""

	def __init__(self, glos: WriterGlossaryType) -> None:
		self._glos = glos
		self._filename = None

	def finish(self) -> None:
		pass

	def open(self, filename: str) -> None:
		self._filename = filename
		if not isdir(filename):
			makedirs(filename)

	@staticmethod
	def filePathFromWord(b_word: bytes) -> str:
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
			info = {}
			info["name"] = self._glos.getInfo("name")
			info["wordCount"] = wordCount
			info |= self._glos.getExtraInfos(["name", "wordCount"])

			infoFile.write(dataToPrettyJson(info))
