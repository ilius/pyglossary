# -*- coding: utf-8 -*-

import gzip
import os
import re
import typing
from collections import Counter
from collections.abc import Generator, Iterator, Sequence
from os.path import (
	dirname,
	getsize,
	isdir,
	isfile,
	join,
	realpath,
	split,
	splitext,
)
from pprint import pformat
from time import time as now
from typing import (
	TYPE_CHECKING,
	Any,
	Callable,
	Literal,
	Protocol,
	TypeVar,
)

if TYPE_CHECKING:
	import io
	import sqlite3

	from pyglossary.langs import Lang


from pyglossary.core import log
from pyglossary.flags import ALWAYS, DEFAULT_YES
from pyglossary.glossary_types import EntryType, GlossaryType
from pyglossary.option import (
	BoolOption,
	Option,
	StrOption,
)
from pyglossary.text_utils import (
	uint32FromBytes,
	uint32ToBytes,
	uint64FromBytes,
	uint64ToBytes,
)

enable = True
lname = "stardict"
format = "Stardict"
description = "StarDict (.ifo)"
extensions = (".ifo",)
extensionCreate = "-stardict/"

sortOnWrite = ALWAYS
sortKeyName = "stardict"
sortEncoding = "utf-8"

kind = "directory"
wiki = "https://en.wikipedia.org/wiki/StarDict"
website = (
	"http://huzheng.org/stardict/",
	"huzheng.org/stardict",
)
# https://github.com/huzheng001/stardict-3/blob/master/dict/doc/StarDictFileFormat
optionsProp: "dict[str, Option]" = {
	"large_file": BoolOption(
		comment="Use idxoffsetbits=64 bits, for large files only",
	),
	"stardict_client": BoolOption(
		comment="Modify html entries for StarDict 3.0",
	),
	"dictzip": BoolOption(
		comment="Compress .dict file to .dict.dz",
	),
	"sametypesequence": StrOption(
		values=["", "h", "m", "x", None],
		comment="Definition format: h=html, m=plaintext, x=xdxf",
	),
	"merge_syns": BoolOption(
		comment="Write alternates to .idx instead of .syn",
	),
	"xdxf_to_html": BoolOption(
		comment="Convert XDXF entries to HTML",
	),
	"xsl": BoolOption(
		comment="Use XSL transformation",
	),
	"unicode_errors": StrOption(
		values=[
			"strict",  # raise a UnicodeDecodeError exception
			"ignore",  # just leave the character out
			"replace",  # use U+FFFD, REPLACEMENT CHARACTER
			"backslashreplace",  # insert a \xNN escape sequence
		],
		comment="What to do with Unicode decoding errors",
	),
	"audio_goldendict": BoolOption(
		comment="Convert audio links for GoldenDict (desktop)",
	),
	"audio_icon": BoolOption(
		comment="Add glossary's audio icon",
	),
	"sqlite": BoolOption(
		comment="Use SQLite to limit memory usage",
	),
}

if os.getenv("PYGLOSSARY_STARDICT_NO_FORCE_SORT") == "1":
	sortOnWrite = DEFAULT_YES

infoKeys = (
	"bookname",
	"author",
	"email",
	"website",
	"description",
	"date",
)


# re_newline = re.compile("[\n\r]+")
re_newline = re.compile("\n\r?|\r\n?")


def newlinesToSpace(text: str) -> str:
	return re_newline.sub(" ", text)


def newlinesToBr(text: str) -> str:
	return re_newline.sub("<br>", text)


def verifySameTypeSequence(s: str) -> bool:
	if not s:
		return True
	# maybe should just check it's in ("h", "m", "x")
	if not s.isalpha():
		return False
	if len(s) > 1:
		return False
	return True


class XdxfTransformerType(Protocol):
	def transformByInnerString(self, text: str) -> str:
		...


class SupportsDunderLT(Protocol):
	def __lt__(self, __other: Any) -> bool:
		...


class SupportsDunderGT(Protocol):
	def __gt__(self, __other: Any) -> bool:
		...


T_SDListItem = TypeVar("T_SDListItem", contravariant=True)


class T_SdList(Protocol[T_SDListItem]):
	def append(self, x: T_SDListItem) -> None:
		...

	def __len__(self) -> int:
		...

	def __iter__(self) -> "Iterator[Any]":
		...

	def sort(self) -> None:
		...


class MemSdList:
	def __init__(self) -> None:
		self._l: "list[Any]" = []

	def append(self, x: Any) -> None:
		self._l.append(x)

	def __len__(self) -> int:
		return len(self._l)

	def __iter__(self) -> "Iterator[Any]":
		return iter(self._l)

	def sortKey(self, item: "tuple[bytes, Any]") -> "tuple[bytes, bytes]":
		return (
			item[0].lower(),
			item[0],
		)

	def sort(self) -> None:
		self._l.sort(key=self.sortKey)


class BaseSqList:
	def __init__(
		self,
		filename: str,
	) -> None:
		from sqlite3 import connect

		if isfile(filename):
			log.warning(f"Renaming {filename} to {filename}.bak")
			os.rename(filename, filename + "bak")

		self._filename = filename

		self._con: "sqlite3.Connection | None" = connect(filename)
		self._cur: "sqlite3.Cursor | None" = self._con.cursor()

		if not filename:
			raise ValueError(f"invalid {filename=}")

		self._orderBy = "word_lower, word"
		self._sorted = False
		self._len = 0

		columns = self._columns = [
			("word_lower", "TEXT"),
			("word", "TEXT"),
		] + self.getExtraColumns()

		self._columnNames = ",".join(
			col[0] for col in columns
		)

		colDefs = ",".join(
			f"{col[0]} {col[1]}"
			for col in columns
		)
		self._con.execute(
			f"CREATE TABLE data ({colDefs})",
		)
		self._con.execute(
			f"CREATE INDEX sortkey ON data({self._orderBy});",
		)
		self._con.commit()

	def getExtraColumns(self) -> "list[tuple[str, str]]":
		# list[(columnName, dataType)]
		return []

	def __len__(self) -> int:
		return self._len

	def append(self, item: "Sequence") -> None:
		if self._cur is None or self._con is None:
			raise RuntimeError("db is closed")
		self._len += 1
		extraN = len(self._columns) - 1
		self._cur.execute(
			f"insert into data({self._columnNames})"
			f" values (?{', ?' * extraN})",
			[item[0].lower()] + list(item),
		)
		if self._len % 1000 == 0:
			self._con.commit()

	def sort(self) -> None:
		pass

	def close(self) -> None:
		if self._cur is None or self._con is None:
			return
		self._con.commit()
		self._cur.close()
		self._con.close()
		self._con = None
		self._cur = None

	def __del__(self) -> None:
		try:
			self.close()
		except AttributeError as e:
			log.error(str(e))

	def __iter__(self) -> "Iterator[EntryType]":
		if self._cur is None:
			raise RuntimeError("db is closed")
		query = f"SELECT * FROM data ORDER BY {self._orderBy}"
		self._cur.execute(query)
		for row in self._cur:
			yield row[1:]


class IdxSqList(BaseSqList):
	def getExtraColumns(self) -> "list[tuple[str, str]]":
		# list[(columnName, dataType)]
		return [
			("idx_block", "BLOB"),
		]


class SynSqList(BaseSqList):
	def getExtraColumns(self) -> "list[tuple[str, str]]":
		# list[(columnName, dataType)]
		return [
			("entry_index", "INTEGER"),
		]


class Reader:
	_xdxf_to_html: bool = True
	_xsl: bool = False
	_unicode_errors: str = "strict"

	def __init__(self, glos: GlossaryType) -> None:

		self._glos = glos
		self.clear()

		self._xdxfTr: "XdxfTransformerType | None" = None
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

	def xdxf_setup(self) -> "XdxfTransformerType":
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
		self._dictFile: "io.IOBase | None" = None
		self._filename = ""  # base file path, no extension
		self._indexData: "list[tuple[bytes, int, int]]" = []
		self._synDict: "dict[int, list[str]]" = {}
		self._sametypesequence = ""
		self._resDir = ""
		self._resFileNames: "list[str]" = []
		self._wordCount: "int | None" = None

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
				line = line.strip()
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

	def readIdxFile(self) -> "list[tuple[bytes, int, int]]":
		if isfile(self._filename + ".idx.gz"):
			with gzip.open(self._filename + ".idx.gz") as g_file:
				idxBytes = g_file.read()
		else:
			with open(self._filename + ".idx", "rb") as _file:
				idxBytes = _file.read()

		indexData = []
		pos = 0

		if self._large_file:
			def getOffset() -> "tuple[int, int]":
				return uint64FromBytes(idxBytes[pos:pos + 8]), pos + 8
		else:
			def getOffset() -> "tuple[int, int]":
				return uint32FromBytes(idxBytes[pos:pos + 4]), pos + 4

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
			size = uint32FromBytes(idxBytes[pos:pos + 4])
			pos += 4
			indexData.append((b_word, offset, size))

		return indexData

	def decodeRawDefiPart(
		self,
		b_defiPart: bytes,
		i_type: int,
		unicode_errors: str,
	) -> "tuple[str, str]":
		_type = chr(i_type)

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

		_format = {
			"m": "m",
			"t": "m",
			"y": "m",
			"g": "h",
			"h": "h",
			"x": "x",
		}.get(_type, "")

		if not _format:
			log.warning(f"Definition type {_type!r} is not supported")

		_defi = b_defiPart.decode("utf-8", errors=unicode_errors)

		# log.info(f"{_type}->{_format}: {_defi}".replace("\n", "")[:120])

		if _format == "x" and self._xdxf_to_html:
			_defi = self.xdxf_transform(_defi)
			_format = "h"

		return _format, _defi

	def renderRawDefiList(
		self,
		rawDefiList: "list[tuple[bytes, int]]",
		unicode_errors: str,
	) -> "tuple[str, str]":
		if len(rawDefiList) == 1:
			b_defiPart, i_type = rawDefiList[0]
			_format, _defi = self.decodeRawDefiPart(
				b_defiPart=b_defiPart,
				i_type=i_type,
				unicode_errors=unicode_errors,
			)
			return _defi, _format

		defiFormatSet = set()
		defisWithFormat = []
		for b_defiPart, i_type in rawDefiList:
			_format, _defi = self.decodeRawDefiPart(
				b_defiPart=b_defiPart,
				i_type=i_type,
				unicode_errors=unicode_errors,
			)
			defisWithFormat.append((_defi, _format))
			defiFormatSet.add(_format)

		if len(defiFormatSet) == 1:
			defis = [_defi for _defi, _ in defisWithFormat]
			_format = defiFormatSet.pop()
			if _format == "h":
				return "\n<hr>".join(defis), _format
			return "\n".join(defis), _format

		if not defiFormatSet:
			log.error(f"empty defiFormatSet, {rawDefiList=}")
			return "", ""

		# convert plaintext or xdxf to html
		defis = []
		for _defi, _format in defisWithFormat:
			if _format == "m":
				_defi = _defi.replace("\n", "<br/>")
				_defi = f"<pre>{_defi}</pre>"
			elif _format == "x":
				_defi = self.xdxf_transform(_defi)
			defis.append(_defi)
		return "\n<hr>\n".join(defis), "h"

	def __iter__(self) -> "Iterator[EntryType]":
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

			word: "str | list[str]"
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

	def readSynFile(self) -> "dict[int, list[str]]":
		"""Return synDict, a dict { entryIndex -> altList }."""
		if self._wordCount is None:
			raise RuntimeError("self._wordCount is None")

		unicode_errors = self._unicode_errors

		synBytes = b''
		if isfile(self._filename + ".syn"):
			with open(self._filename + ".syn", mode="rb") as _file:
				synBytes = _file.read()
		elif isfile(self._filename + ".syn.dz"):
			with gzip.open(self._filename + ".syn.dz", mode="rb") as _zfile:
				synBytes = _zfile.read()
		else:
			return {}

		synBytesLen = len(synBytes)
		synDict: "dict[int, list[str]]" = {}
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
			entryIndex = uint32FromBytes(synBytes[pos:pos + 4])
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

	def parseDefiBlockCompact(
		self,
		b_block: bytes,
		sametypesequence: str,
	) -> "list[tuple[bytes, int]] | None":
		"""
		Parse definition block when sametypesequence option is specified.

		Return a list of (b_defi, defiFormatCode) tuples
			where b_defi is a bytes instance
			and defiFormatCode is int, so: defiFormat = chr(defiFormatCode)
		"""
		b_sametypesequence = sametypesequence.encode("utf-8")
		if not b_sametypesequence:
			raise ValueError(f"{b_sametypesequence = }")
		res = []
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
				size = uint32FromBytes(b_block[i:i + 4])
				i += 4
				if i + size > len(b_block):
					return None
				res.append((b_block[i:i + size], t))
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

	def parseDefiBlockGeneral(
		self,
		b_block: bytes,
	) -> "list[tuple[bytes, int]] | None":
		"""
		Parse definition block when sametypesequence option is not specified.

		Return a list of (b_defi, defiFormatCode) tuples
			where b_defi is a bytes instance
			and defiFormatCode is int, so: defiFormat = chr(defiFormatCode)
		"""
		res = []
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
				size = uint32FromBytes(b_block[i:i + 4])
				i += 4
				if i + size > len(b_block):
					return None
				res.append((b_block[i:i + size], t))
				i += size
		return res

	# def readResources(self):
	# 	if not isdir(self._resDir):
	# 		resInfoPath = join(baseDirPath, "res.rifo")
	# 		if isfile(resInfoPath):
	# 			log.warning(
	# 				"StarDict resource database is not supported. Skipping"
	# 			)


class Writer:
	_large_file: bool = False
	_dictzip: bool = True
	_sametypesequence: "Literal['', 'h', 'm', 'x'] | None" = ""
	_stardict_client: bool = False
	_merge_syns: bool = False
	_audio_goldendict: bool = False
	_audio_icon: bool = True
	_sqlite: bool = False

	def __init__(self, glos: GlossaryType) -> None:
		self._glos = glos
		self._filename = ""
		self._resDir = ""
		self._sourceLang: "Lang | None" = None
		self._targetLang: "Lang | None" = None
		self._p_pattern = re.compile(
			'<p( [^<>]*?)?>(.*?)</p>',
			re.DOTALL,
		)
		self._br_pattern = re.compile(
			"<br[ /]*>",
			re.IGNORECASE,
		)
		self._re_audio_link = re.compile(
			'<a (type="sound" )?([^<>]*? )?href="sound://([^<>"]+)"( .*?)?>(.*?)</a>',
		)

	def finish(self) -> None:
		self._filename = ""
		self._resDir = ""
		self._sourceLang = None
		self._targetLang = None

	def open(self, filename: str) -> None:
		log.debug(f"open: {filename = }")
		fileBasePath = filename
		##
		if splitext(filename)[1].lower() == ".ifo":
			fileBasePath = splitext(filename)[0]
		elif filename.endswith(os.sep):
			if not isdir(filename):
				os.makedirs(filename)
			fileBasePath = join(filename, split(filename[:-1])[-1])
		elif isdir(filename):
			fileBasePath = join(filename, split(filename)[-1])

		parentDir = split(fileBasePath)[0]
		if not isdir(parentDir):
			log.info(f"Creating directory {parentDir}")
			os.mkdir(parentDir)
		##
		if fileBasePath:
			fileBasePath = realpath(fileBasePath)
		self._filename = fileBasePath
		self._resDir = join(dirname(fileBasePath), "res")
		self._sourceLang = self._glos.sourceLang
		self._targetLang = self._glos.targetLang
		if self._sametypesequence:
			log.debug(f"Using write option sametypesequence={self._sametypesequence}")
		elif self._sametypesequence is not None:
			stat = self._glos.collectDefiFormat(100)
			log.debug(f"defiFormat stat: {stat}")
			if stat:
				if stat["m"] > 0.97:
					log.info("Auto-selecting sametypesequence=m")
					self._sametypesequence = "m"
				elif stat["h"] > 0.5:
					log.info("Auto-selecting sametypesequence=h")
					self._sametypesequence = "h"

	def write(self) -> "Generator[None, EntryType, None]":
		from pyglossary.os_utils import runDictzip
		if self._sametypesequence:
			if self._merge_syns:
				yield from self.writeCompactMergeSyns(self._sametypesequence)
			else:
				yield from self.writeCompact(self._sametypesequence)
		else:
			if self._merge_syns:
				yield from self.writeGeneralMergeSyns()
			else:
				yield from self.writeGeneral()
		if self._dictzip:
			runDictzip(f"{self._filename}.dict")
			syn_file = f"{self._filename}.syn"
			if not self._merge_syns and os.path.exists(syn_file):
				runDictzip(syn_file)

	def fixDefi(self, defi: str, defiFormat: str) -> str:
		# for StarDict 3.0:
		if self._stardict_client and defiFormat == "h":
			defi = self._p_pattern.sub("\\2<br>", defi)
			# if there is </p> left without opening, replace with <br>
			defi = defi.replace("</p>", "<br>")
			defi = self._br_pattern.sub("<br>", defi)

		if self._audio_goldendict:
			if self._audio_icon:
				defi = self._re_audio_link.sub(
					r'<audio src="\3">\5</audio>',
					defi,
				)
			else:
				defi = self._re_audio_link.sub(
					r'<audio src="\3"></audio>',
					defi,
				)

		# FIXME:
		# defi = defi.replace(' src="./', ' src="./res/')
		return defi

	def newIdxList(self) -> "T_SdList":
		if not self._sqlite:
			return MemSdList()
		return IdxSqList(join(self._glos.tmpDataDir, "stardict-idx.db"))

	def newSynList(self) -> "T_SdList":
		if not self._sqlite:
			return MemSdList()
		return SynSqList(join(self._glos.tmpDataDir, "stardict-syn.db"))

	def dictMarkToBytesFunc(self) -> "tuple[Callable, int]":
		if self._large_file:
			return uint64ToBytes, 0xffffffffffffffff

		return uint32ToBytes, 0xffffffff

	def writeCompact(self, defiFormat: str) -> "Generator[None, EntryType, None]":
		"""
		Build StarDict dictionary with sametypesequence option specified.
		Every item definition consists of a single article.
		All articles have the same format, specified in defiFormat parameter.

		defiFormat: format of article definition: h - html, m - plain text
		"""
		log.debug(f"writeCompact: {defiFormat=}")
		dictMark = 0
		altIndexList = self.newSynList()

		dictFile = open(self._filename + ".dict", "wb")
		idxFile = open(self._filename + ".idx", "wb")

		dictMarkToBytes, dictMarkMax = self.dictMarkToBytesFunc()

		t0 = now()
		wordCount = 0
		if not isdir(self._resDir):
			os.mkdir(self._resDir)

		entryIndex = -1
		while True:
			entry = yield
			if entry is None:
				break
			if entry.isData():
				entry.save(self._resDir)
				continue
			entryIndex += 1

			words = entry.l_word  # list of strs
			word = words[0]  # str
			defi = self.fixDefi(entry.defi, defiFormat)
			# defi is str

			for alt in words[1:]:
				altIndexList.append((alt.encode("utf-8"), entryIndex))

			b_dictBlock = defi.encode("utf-8")
			dictFile.write(b_dictBlock)
			blockLen = len(b_dictBlock)

			b_idxBlock = word.encode("utf-8") + b"\x00" + \
				dictMarkToBytes(dictMark) + \
				uint32ToBytes(blockLen)
			idxFile.write(b_idxBlock)

			dictMark += blockLen
			wordCount += 1

			if dictMark > dictMarkMax:
				log.error(
					f"StarDict: {dictMark = } is too big, "
					f"set option large_file=true",
				)
				break

		dictFile.close()
		idxFile.close()
		if not os.listdir(self._resDir):
			os.rmdir(self._resDir)
		log.info(f"Writing dict file took {now()-t0:.2f} seconds")

		self.writeSynFile(altIndexList)
		self.writeIfoFile(
			wordCount,
			len(altIndexList),
			defiFormat=defiFormat,
		)

	def writeGeneral(self) -> "Generator[None, EntryType, None]":
		"""
		Build StarDict dictionary in general case.
		Every item definition may consist of an arbitrary number of articles.
		sametypesequence option is not used.
		"""
		log.debug("writeGeneral")
		dictMark = 0
		altIndexList = self.newSynList()

		dictFile = open(self._filename + ".dict", "wb")
		idxFile = open(self._filename + ".idx", "wb")

		t0 = now()
		wordCount = 0
		defiFormatCounter: "typing.Counter[str]" = Counter()
		if not isdir(self._resDir):
			os.mkdir(self._resDir)

		dictMarkToBytes, dictMarkMax = self.dictMarkToBytesFunc()

		entryIndex = -1
		while True:
			entry = yield
			if entry is None:
				break
			if entry.isData():
				entry.save(self._resDir)
				continue
			entryIndex += 1

			entry.detectDefiFormat()  # call no more than once
			defiFormat = entry.defiFormat
			defiFormatCounter[defiFormat] += 1
			if defiFormat not in ("h", "m", "x"):
				log.error(f"invalid {defiFormat=}, using 'm'")
				defiFormat = "m"

			words = entry.l_word  # list of strs
			word = words[0]  # str
			defi = self.fixDefi(entry.defi, defiFormat)
			# defi is str

			for alt in words[1:]:
				altIndexList.append((alt.encode("utf-8"), entryIndex))

			b_dictBlock = (defiFormat + defi).encode("utf-8") + b"\x00"
			dictFile.write(b_dictBlock)
			blockLen = len(b_dictBlock)

			b_idxBlock = word.encode("utf-8") + b"\x00" + \
				dictMarkToBytes(dictMark) + \
				uint32ToBytes(blockLen)
			idxFile.write(b_idxBlock)

			dictMark += blockLen
			wordCount += 1

			if dictMark > dictMarkMax:
				log.error(
					f"StarDict: {dictMark = } is too big, "
					f"set option large_file=true",
				)
				break

		dictFile.close()
		idxFile.close()
		if not os.listdir(self._resDir):
			os.rmdir(self._resDir)
		log.info(f"Writing dict file took {now()-t0:.2f} seconds")
		log.debug("defiFormatsCount = " + pformat(defiFormatCounter.most_common()))

		self.writeSynFile(altIndexList)
		self.writeIfoFile(
			wordCount,
			len(altIndexList),
			defiFormat="",
		)

	def writeSynFile(self, altIndexList: "T_SdList[tuple[bytes, int]]") -> None:
		"""Build .syn file."""
		if not altIndexList:
			return

		log.info(f"Sorting {len(altIndexList)} synonyms...")
		t0 = now()

		altIndexList.sort()
		# 28 seconds with old sort key (converted from custom cmp)
		# 0.63 seconds with my new sort key
		# 0.20 seconds without key function (default sort)

		log.info(
			f"Sorting {len(altIndexList)} synonyms took {now()-t0:.2f} seconds",
		)
		log.info(f"Writing {len(altIndexList)} synonyms...")
		t0 = now()
		with open(self._filename + ".syn", "wb") as synFile:
			synFile.write(b"".join(
				b_alt + b"\x00" + uint32ToBytes(entryIndex)
				for b_alt, entryIndex in altIndexList
			))
		log.info(
			f"Writing {len(altIndexList)} synonyms took {now()-t0:.2f} seconds",
		)

	def writeCompactMergeSyns(
		self,
		defiFormat: str,
	) -> "Generator[None, EntryType, None]":
		"""
		Build StarDict dictionary with sametypesequence option specified.
		Every item definition consists of a single article.
		All articles have the same format, specified in defiFormat parameter.

		defiFormat - format of article definition: h - html, m - plain text
		"""
		log.debug(f"writeCompactMergeSyns: {defiFormat=}")
		dictMark = 0

		idxBlockList = self.newIdxList()
		altIndexList = self.newSynList()

		dictFile = open(self._filename + ".dict", "wb")

		t0 = now()
		if not isdir(self._resDir):
			os.mkdir(self._resDir)

		dictMarkToBytes, dictMarkMax = self.dictMarkToBytesFunc()

		entryIndex = -1
		while True:
			entry = yield
			if entry is None:
				break
			if entry.isData():
				entry.save(self._resDir)
				continue
			entryIndex += 1

			words = entry.l_word  # list of strs
			word = words[0]  # str
			defi = self.fixDefi(entry.defi, defiFormat)
			# defi is str

			b_dictBlock = defi.encode("utf-8")
			dictFile.write(b_dictBlock)
			blockLen = len(b_dictBlock)

			blockData = dictMarkToBytes(dictMark) + uint32ToBytes(blockLen)
			for word in words:
				idxBlockList.append((word.encode("utf-8"), blockData))

			dictMark += blockLen

			if dictMark > dictMarkMax:
				log.error(
					f"StarDict: {dictMark = } is too big, "
					f"set option large_file=true",
				)
				break

		wordCount = self.writeIdxFile(idxBlockList)

		dictFile.close()
		if not os.listdir(self._resDir):
			os.rmdir(self._resDir)
		log.info(f"Writing dict file took {now()-t0:.2f} seconds")

		self.writeIfoFile(
			wordCount,
			len(altIndexList),
			defiFormat=defiFormat,
		)

	def writeGeneralMergeSyns(self) -> "Generator[None, EntryType, None]":
		"""
		Build StarDict dictionary in general case.
		Every item definition may consist of an arbitrary number of articles.
		sametypesequence option is not used.
		"""
		log.debug("writeGeneralMergeSyns")
		dictMark = 0
		idxBlockList = self.newIdxList()
		altIndexList = self.newSynList()

		dictFile = open(self._filename + ".dict", "wb")

		t0 = now()
		wordCount = 0
		defiFormatCounter: "typing.Counter[str]" = Counter()
		if not isdir(self._resDir):
			os.mkdir(self._resDir)

		dictMarkToBytes, dictMarkMax = self.dictMarkToBytesFunc()

		entryIndex = -1
		while True:
			entry = yield
			if entry is None:
				break
			if entry.isData():
				entry.save(self._resDir)
				continue
			entryIndex += 1

			entry.detectDefiFormat()  # call no more than once
			defiFormat = entry.defiFormat
			defiFormatCounter[defiFormat] += 1
			if defiFormat not in ("h", "m", "x"):
				log.error(f"invalid {defiFormat=}, using 'm'")
				defiFormat = "m"

			words = entry.l_word  # list of strs
			word = words[0]  # str
			defi = self.fixDefi(entry.defi, defiFormat)
			# defi is str

			b_dictBlock = (defiFormat + defi).encode("utf-8") + b"\x00"
			dictFile.write(b_dictBlock)
			blockLen = len(b_dictBlock)

			blockData = dictMarkToBytes(dictMark) + uint32ToBytes(blockLen)
			for word in words:
				idxBlockList.append((word.encode("utf-8"), blockData))

			dictMark += blockLen

			if dictMark > dictMarkMax:
				log.error(
					f"StarDict: {dictMark = } is too big, "
					f"set option large_file=true",
				)
				break

		wordCount = self.writeIdxFile(idxBlockList)

		dictFile.close()
		if not os.listdir(self._resDir):
			os.rmdir(self._resDir)
		log.info(f"Writing dict file took {now()-t0:.2f} seconds")
		log.debug("defiFormatsCount = " + pformat(defiFormatCounter.most_common()))

		self.writeIfoFile(
			wordCount,
			len(altIndexList),
			defiFormat="",
		)

	def writeIdxFile(self, indexList: "T_SdList[tuple[bytes, bytes]]") -> int:
		filename = self._filename + ".idx"
		if not indexList:
			return 0

		log.info(f"Sorting {len(indexList)} items...")
		t0 = now()

		indexList.sort()
		log.info(
			f"Sorting {len(indexList)} {filename} took {now()-t0:.2f} seconds",
		)
		log.info(f"Writing {len(indexList)} index entries...")
		t0 = now()
		with open(filename, mode="wb") as indexFile:
			indexFile.write(b"".join(
				key + b"\x00" + value
				for key, value in indexList
			))
		log.info(
			f"Writing {len(indexList)} {filename} took {now()-t0:.2f} seconds",
		)
		return len(indexList)

	def writeIfoFile(
		self,
		wordCount: int,
		synWordCount: int,
		defiFormat: str = "",
	) -> None:
		"""Build .ifo file."""
		glos = self._glos
		bookname = newlinesToSpace(glos.getInfo("name"))
		indexFileSize = getsize(self._filename + ".idx")

		sourceLang = self._sourceLang
		targetLang = self._targetLang
		if sourceLang and targetLang:
			langs = f"{sourceLang.code}-{targetLang.code}"
			if langs not in bookname.lower():
				bookname = f"{bookname} ({langs})"
			log.info(f"bookname: {bookname}")

		ifo: "list[tuple[str, str]]" = [
			("version", "3.0.0"),
			("bookname", bookname),
			("wordcount", str(wordCount)),
			("idxfilesize", str(indexFileSize)),
		]
		if self._large_file:
			ifo.append(("idxoffsetbits", "64"))
		if defiFormat:
			ifo.append(("sametypesequence", defiFormat))
		if synWordCount > 0:
			ifo.append(("synwordcount", str(synWordCount)))

		desc = glos.getInfo("description")
		_copyright = glos.getInfo("copyright")
		if _copyright:
			desc = f"{_copyright}\n{desc}"
		publisher = glos.getInfo("publisher")
		if publisher:
			desc = f"Publisher: {publisher}\n{desc}"

		for key in infoKeys:
			if key in (
				"bookname",
				"description",
			):
				continue
			value = glos.getInfo(key)
			if value == "":
				continue
			value = newlinesToSpace(value)
			ifo.append((key, value))

		ifo.append(("description", newlinesToBr(desc)))

		ifoStr = "StarDict's dict ifo file\n"
		for key, value in ifo:
			ifoStr += f"{key}={value}\n"
		with open(
			self._filename + ".ifo",
			mode="w",
			encoding="utf-8",
			newline="\n",
		) as ifoFile:
			ifoFile.write(ifoStr)
