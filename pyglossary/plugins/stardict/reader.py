# -*- coding: utf-8 -*-
from __future__ import annotations

import gzip
import os
from os.path import (
	dirname,
	isdir,
	isfile,
	join,
	realpath,
	splitext,
)
from typing import (
	TYPE_CHECKING,
	Protocol,
)

if TYPE_CHECKING:
	import io
	from collections.abc import Iterator

	from pyglossary.glossary_types import EntryType, GlossaryType


from pyglossary.core import log
from pyglossary.text_utils import (
	uint32FromBytes,
	uint64FromBytes,
)

__all__ = ["Reader"]


def verifySameTypeSequence(s: str) -> bool:
	if not s:
		return True
	# maybe should just check it's in ("h", "m", "x")
	if not s.isalpha():
		return False
	return len(s) == 1


class XdxfTransformerType(Protocol):
	def transformByInnerString(self, text: str) -> str: ...


class Reader:
	_xdxf_to_html: bool = True
	_xsl: bool = False
	_unicode_errors: str = "strict"

	def __init__(self, glos: GlossaryType) -> None:
		self._glos = glos
		self.clear()

		self._xdxfTr: XdxfTransformerType | None = None
		self._large_file = False

		"""
		indexData format
		indexData[i] - i-th record in index file,
						a tuple (previously a list) of length 3
		indexData[i][0] - b_word (bytes)
		indexData[i][1] - definition block offset in dict file (int)
		indexData[i][2] - definition block size in dict file (int)
		REMOVED:
			indexData[i][3] - list of definitions
			indexData[i][3][j][0] - definition data
			indexData[i][3][j][1] - definition type - "h", "m" or "x"
			indexData[i][4] - list of synonyms (strings)

		synDict:
			a dict { entryIndex -> altList }
		"""

	def xdxf_setup(self) -> XdxfTransformerType:
		if self._xsl:
			from pyglossary.xdxf.xsl_transform import XslXdxfTransformer

			return XslXdxfTransformer(encoding="utf-8")
		from pyglossary.xdxf.transform import XdxfTransformer

		return XdxfTransformer(encoding="utf-8")

	def xdxf_transform(self, text: str) -> str:
		if self._xdxfTr is None:
			self._xdxfTr = self.xdxf_setup()
		return self._xdxfTr.transformByInnerString(text)

	def close(self) -> None:
		if self._dictFile:
			self._dictFile.close()
		self.clear()

	def clear(self) -> None:
		self._dictFile: io.IOBase | None = None
		self._filename = ""  # base file path, no extension
		self._indexData: list[tuple[bytes, int, int]] = []
		self._synDict: dict[int, list[str]] = {}
		self._sametypesequence = ""
		self._resDir = ""
		self._resFileNames: list[str] = []
		self._wordCount: int | None = None

	def open(self, filename: str) -> None:
		if splitext(filename)[1].lower() == ".ifo":
			filename = splitext(filename)[0]
		elif isdir(filename):
			filename = join(filename, filename)
		self._filename = filename
		self._filename = realpath(self._filename)
		self.readIfoFile()
		sametypesequence = self._glos.getInfo("sametypesequence")
		if not verifySameTypeSequence(sametypesequence):
			raise LookupError(f"Invalid {sametypesequence = }")
		self._indexData = self.readIdxFile()
		self._wordCount = len(self._indexData)
		self._synDict = self.readSynFile()
		self._sametypesequence = sametypesequence
		if isfile(self._filename + ".dict.dz"):
			self._dictFile = gzip.open(self._filename + ".dict.dz", mode="rb")
		else:
			self._dictFile = open(self._filename + ".dict", mode="rb")
		self._resDir = join(dirname(self._filename), "res")
		if isdir(self._resDir):
			self._resFileNames = os.listdir(self._resDir)
		else:
			self._resDir = ""
			self._resFileNames = []
		# self.readResources()

	def __len__(self) -> int:
		if self._wordCount is None:
			raise RuntimeError(
				"StarDict: len(reader) called while reader is not open",
			)
		return self._wordCount + len(self._resFileNames)

	def readIfoFile(self) -> None:
		""".ifo file is a text file in utf-8 encoding."""
		with open(
			self._filename + ".ifo",
			mode="rb",
		) as ifoFile:
			for line in ifoFile:
				line = line.strip()  # noqa: PLW2901
				if not line:
					continue
				if line == b"StarDict's dict ifo file":
					continue
				b_key, _, b_value = line.partition(b"=")
				if not (b_key and b_value):
					continue
				try:
					key = b_key.decode("utf-8")
					value = b_value.decode("utf-8", errors=self._unicode_errors)
				except UnicodeDecodeError:
					log.error(f"ifo line is not UTF-8: {line!r}")
					continue
				self._glos.setInfo(key, value)

		idxoffsetbits = self._glos.getInfo("idxoffsetbits")
		if idxoffsetbits:
			if idxoffsetbits == "32":
				self._large_file = False
			elif idxoffsetbits == "64":
				self._large_file = True
			else:
				raise ValueError(f"invalid {idxoffsetbits = }")

	def readIdxFile(self) -> list[tuple[bytes, int, int]]:
		if isfile(self._filename + ".idx.gz"):
			with gzip.open(self._filename + ".idx.gz") as g_file:
				idxBytes = g_file.read()
		else:
			with open(self._filename + ".idx", "rb") as _file:
				idxBytes = _file.read()

		indexData: list[tuple[bytes, int, int]] = []
		pos = 0

		if self._large_file:

			def getOffset() -> tuple[int, int]:
				return uint64FromBytes(idxBytes[pos : pos + 8]), pos + 8
		else:

			def getOffset() -> tuple[int, int]:
				return uint32FromBytes(idxBytes[pos : pos + 4]), pos + 4

		while pos < len(idxBytes):
			beg = pos
			pos = idxBytes.find(b"\x00", beg)
			if pos < 0:
				log.error("Index file is corrupted")
				break
			b_word = idxBytes[beg:pos]
			pos += 1
			if pos + 8 > len(idxBytes):
				log.error("Index file is corrupted")
				break
			offset, pos = getOffset()
			size = uint32FromBytes(idxBytes[pos : pos + 4])
			pos += 4
			indexData.append((b_word, offset, size))

		return indexData

	def decodeRawDefiPart(
		self,
		b_defiPart: bytes,
		i_type: int,
		unicode_errors: str,
	) -> tuple[str, str]:
		type_ = chr(i_type)

		"""
		_type: 'r'
		https://github.com/huzheng001/stardict-3/blob/master/dict/doc/StarDictFileFormat#L431
		Resource file list.
		The content can be:
		img:pic/example.jpg	// Image file
		snd:apple.wav		// Sound file
		vdo:film.avi		// Video file
		att:file.bin		// Attachment file
		More than one line is supported as a list of available files.
		StarDict will find the files in the Resource Storage.
		The image will be shown, the sound file will have a play button.
		You can "save as" the attachment file and so on.
		The file list must be a utf-8 string ending with '\0'.
		Use '\n' for separating new lines.
		Use '/' character as directory separator.
		"""

		format_ = {
			"m": "m",
			"t": "m",
			"y": "m",
			"g": "h",
			"h": "h",
			"x": "x",
		}.get(type_, "")

		if not format_:
			log.warning(f"Definition type {type_!r} is not supported")

		defi = b_defiPart.decode("utf-8", errors=unicode_errors)

		# log.info(f"{_type}->{_format}: {_defi}".replace("\n", "")[:120])

		if format_ == "x" and self._xdxf_to_html:
			defi = self.xdxf_transform(defi)
			format_ = "h"

		return format_, defi

	def renderRawDefiList(
		self,
		rawDefiList: list[tuple[bytes, int]],
		unicode_errors: str,
	) -> tuple[str, str]:
		if len(rawDefiList) == 1:
			b_defiPart, i_type = rawDefiList[0]
			format_, defi = self.decodeRawDefiPart(
				b_defiPart=b_defiPart,
				i_type=i_type,
				unicode_errors=unicode_errors,
			)
			return defi, format_

		defiFormatSet: set[str] = set()
		defisWithFormat: list[tuple[str, str]] = []
		for b_defiPart, i_type in rawDefiList:
			format_, defi = self.decodeRawDefiPart(
				b_defiPart=b_defiPart,
				i_type=i_type,
				unicode_errors=unicode_errors,
			)
			defisWithFormat.append((defi, format_))
			defiFormatSet.add(format_)

		if len(defiFormatSet) == 1:
			format_ = defiFormatSet.pop()
			if format_ == "h":
				return "\n<hr>".join([defi for defi, _ in defisWithFormat]), format_
			return "\n".join([defi for defi, _ in defisWithFormat]), format_

		if not defiFormatSet:
			log.error(f"empty defiFormatSet, {rawDefiList=}")
			return "", ""

		# convert plaintext or xdxf to html
		defis: list[str] = []
		for defi_, format_ in defisWithFormat:
			defi = defi_
			if format_ == "m":
				defi = defi.replace("\n", "<br/>")
				defi = f"<pre>{defi}</pre>"
			elif format_ == "x":
				defi = self.xdxf_transform(defi)
			defis.append(defi)
		return "\n<hr>\n".join(defis), "h"

	def __iter__(self) -> Iterator[EntryType]:  # noqa: PLR0912
		indexData = self._indexData
		synDict = self._synDict
		sametypesequence = self._sametypesequence
		dictFile = self._dictFile
		unicode_errors = self._unicode_errors

		if not dictFile:
			raise RuntimeError("iterating over a reader while it's not open")

		if not indexData:
			log.warning("indexData is empty")
			return

		for entryIndex, (b_word, defiOffset, defiSize) in enumerate(indexData):
			if not b_word:
				continue

			dictFile.seek(defiOffset)
			if dictFile.tell() != defiOffset:
				log.error(f"Unable to read definition for word {b_word!r}")
				continue

			b_defiBlock = dictFile.read(defiSize)

			if len(b_defiBlock) != defiSize:
				log.error(f"Unable to read definition for word {b_word!r}")
				continue

			if sametypesequence:
				rawDefiList = self.parseDefiBlockCompact(
					b_defiBlock,
					sametypesequence,
				)
			else:
				rawDefiList = self.parseDefiBlockGeneral(b_defiBlock)

			if rawDefiList is None:
				log.error(f"Data file is corrupted. Word {b_word!r}")
				continue

			word: str | list[str]
			word = b_word.decode("utf-8", errors=unicode_errors)
			try:
				alts = synDict[entryIndex]
			except KeyError:  # synDict is dict
				pass
			else:
				word = [word] + alts

			defi, defiFormat = self.renderRawDefiList(
				rawDefiList,
				unicode_errors,
			)

			# FIXME:
			# defi = defi.replace(' src="./res/', ' src="./')
			yield self._glos.newEntry(word, defi, defiFormat=defiFormat)

		if isdir(self._resDir):
			for fname in os.listdir(self._resDir):
				fpath = join(self._resDir, fname)
				with open(fpath, "rb") as _file:
					yield self._glos.newDataEntry(
						fname,
						_file.read(),
					)

	def readSynFile(self) -> dict[int, list[str]]:
		"""Return synDict, a dict { entryIndex -> altList }."""
		if self._wordCount is None:
			raise RuntimeError("self._wordCount is None")

		unicode_errors = self._unicode_errors

		synBytes = b""
		if isfile(self._filename + ".syn"):
			with open(self._filename + ".syn", mode="rb") as _file:
				synBytes = _file.read()
		elif isfile(self._filename + ".syn.dz"):
			with gzip.open(self._filename + ".syn.dz", mode="rb") as _zfile:
				synBytes = _zfile.read()
		else:
			return {}

		synBytesLen = len(synBytes)
		synDict: dict[int, list[str]] = {}
		pos = 0
		while pos < synBytesLen:
			beg = pos
			pos = synBytes.find(b"\x00", beg)
			if pos < 0:
				log.error("Synonym file is corrupted")
				break
			b_alt = synBytes[beg:pos]  # b_alt is bytes
			pos += 1
			if pos + 4 > len(synBytes):
				log.error("Synonym file is corrupted")
				break
			entryIndex = uint32FromBytes(synBytes[pos : pos + 4])
			pos += 4
			if entryIndex >= self._wordCount:
				log.error(
					"Corrupted synonym file. "
					f"Word {b_alt!r} references invalid item",
				)
				continue

			s_alt = b_alt.decode("utf-8", errors=unicode_errors)
			# s_alt is str
			try:
				synDict[entryIndex].append(s_alt)
			except KeyError:
				synDict[entryIndex] = [s_alt]

		return synDict

	@staticmethod
	def parseDefiBlockCompact(
		b_block: bytes,
		sametypesequence: str,
	) -> list[tuple[bytes, int]] | None:
		"""
		Parse definition block when sametypesequence option is specified.

		Return a list of (b_defi, defiFormatCode) tuples
			where b_defi is a bytes instance
			and defiFormatCode is int, so: defiFormat = chr(defiFormatCode)
		"""
		b_sametypesequence = sametypesequence.encode("utf-8")
		if not b_sametypesequence:
			raise ValueError(f"{b_sametypesequence = }")
		res: list[tuple[bytes, int]] = []
		i = 0
		for t in b_sametypesequence[:-1]:
			if i >= len(b_block):
				return None
			if bytes([t]).islower():
				beg = i
				i = b_block.find(b"\x00", beg)
				if i < 0:
					return None
				res.append((b_block[beg:i], t))
				i += 1
			else:
				# assert bytes([t]).isupper()
				if i + 4 > len(b_block):
					return None
				size = uint32FromBytes(b_block[i : i + 4])
				i += 4
				if i + size > len(b_block):
					return None
				res.append((b_block[i : i + size], t))
				i += size

		if i >= len(b_block):
			return None
		t = b_sametypesequence[-1]
		if bytes([t]).islower():
			if 0 in b_block[i:]:
				return None
			res.append((b_block[i:], t))
		else:
			# assert bytes([t]).isupper()
			res.append((b_block[i:], t))

		return res

	@staticmethod
	def parseDefiBlockGeneral(
		b_block: bytes,
	) -> list[tuple[bytes, int]] | None:
		"""
		Parse definition block when sametypesequence option is not specified.

		Return a list of (b_defi, defiFormatCode) tuples
			where b_defi is a bytes instance
			and defiFormatCode is int, so: defiFormat = chr(defiFormatCode)
		"""
		res: list[tuple[bytes, int]] = []
		i = 0
		while i < len(b_block):
			t = b_block[i]
			if not bytes([t]).isalpha():
				return None
			i += 1
			if bytes([t]).islower():
				beg = i
				i = b_block.find(b"\x00", beg)
				if i < 0:
					return None
				res.append((b_block[beg:i], t))
				i += 1
			else:
				# assert bytes([t]).isupper()
				if i + 4 > len(b_block):
					return None
				size = uint32FromBytes(b_block[i : i + 4])
				i += 4
				if i + size > len(b_block):
					return None
				res.append((b_block[i : i + size], t))
				i += size
		return res

	# def readResources(self):
	# 	if not isdir(self._resDir):
	# 		resInfoPath = join(baseDirPath, "res.rifo")
	# 		if isfile(resInfoPath):
	# 			log.warning(
	# 				"StarDict resource database is not supported. Skipping"
	# 			)
