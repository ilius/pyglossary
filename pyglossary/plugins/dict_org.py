# -*- coding: utf-8 -*-

from formats_common import *
from pyglossary.file_utils import fileCountLines

enable = True
format = "DictOrg"
description = "DICT.org file format (.index)"
extensions = [".index"]
optionsProp = {
	"dictzip": BoolOption(),
	"install": BoolOption(),
}
depends = {}
sortOnWrite = DEFAULT_YES


b64_chars = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
b64_chars_ord = {c: i for i, c in enumerate(b64_chars)}


def intToIndexStr(n: int) -> bytes:
	chars = []
	while True:
		chars.append(b64_chars[n & 0x3f])
		n >>= 6
		if n == 0:
			break
	return bytes(reversed(chars))


def indexStrToInt(st: str) -> int:
	n = 0
	for i, c in enumerate(reversed(list(st))):
		k = b64_chars_ord[c]
		assert 0 <= k < 64
		n |= (k << 6*i)
		# += is safe
		# |= is probably a little faster
		# |= is also safe because n has lesser that 6*i bits. why? ## FIXME
	return n


def installToDictd(filename: str, title: str = "") -> None:
	"""
	filename is without extension (neither .index or .dict or .dict.dz)
	"""
	import shutil
	targetDir = "/usr/share/dictd/"
	log.info("Installing %r to DICTD server", filename)

	if os.path.isfile(filename + ".dict.dz"):
		dictPostfix = ".dict.dz"
	elif os.path.isfile(filename + ".dict"):
		dictPostfix = ".dict"
	else:
		log.error("No .dict file, could not install dictd file %r", filename)
		return

	if not filename.startswith(targetDir):
		shutil.copy(filename + ".index", targetDir)
		shutil.copy(filename + dictPostfix, targetDir)

	fname = split(filename)[1]
	if not title:
		title = fname
	open("/var/lib/dictd/db.list", "a").write("""
database %s
{
  data %s
  index %s
}
""" % (
	title,
	join(targetDir, fname + dictPostfix),
	join(targetDir, fname + ".index"),
))


class Reader(object):
	def __init__(self, glos: GlossaryType):
		self._glos = glos
		self._filename = ""
		self._indexFp = None
		self._dictFp = None
		self._leadingLinesCount = 0
		self._len = None

	def open(self, filename: str) -> None:
		import gzip
		if filename.endswith(".index"):
			filename = filename[:-6]
		self._filename = filename
		self._indexFp = open(filename+".index", "rb")
		if os.path.isfile(filename+".dict.dz"):
			self._dictFp = gzip.open(filename+".dict.dz")
		else:
			self._dictFp = open(filename+".dict", "rb")

	def close(self) -> None:
		if self._indexFp is not None:
			try:
				self._indexFp.close()
			except:
				log.exception("error while closing index file")
			self._indexFp = None
		if self._dictFp is not None:
			try:
				self._dictFp.close()
			except:
				log.exception("error while closing dict file")
			self._dictFp = None
	def __len__(self) -> int:
		if self._len is None:
			log.debug("Try not to use len(reader) as it takes extra time")
			self._len = fileCountLines(
				self._filename + ".index"
			) - self._leadingLinesCount
		return self._len

	def __iter__(self) -> Iterator[BaseEntry]:
		if not self._indexFp:
			log.error("reader is not open, can not iterate")
			raise StopIteration
		# read info from header of dict file # FIXME
		word = ""
		sumLen = 0
		wrongSortedN = 0
		wordCount = 0
		# __________________ IMPORTANT PART __________________ #
		for line in self._indexFp:
			line = line.strip()
			if not line:
				continue
			parts = line.split(b"\t")
			assert len(parts) == 3
			word = parts[0].replace(b"<BR>", b"\\n")\
						   .replace(b"<br>", b"\\n")
			sumLen2 = indexStrToInt(parts[1])
			if sumLen2 != sumLen:
				wrongSortedN += 1
			sumLen = sumLen2
			defiLen = indexStrToInt(parts[2])
			self._dictFp.seek(sumLen)
			defi = self._dictFp.read(defiLen)
			defi = defi.replace(b"<BR>", b"\n").replace(b"<br>", b"\n")
			sumLen += defiLen
			yield self._glos.newEntry(toStr(word), toStr(defi))
			wordCount += 1
		# ____________________________________________________ #

		if wrongSortedN > 0:
			log.warning("Warning: wrong sorting count: %d", wrongSortedN)
		self._len = wordCount


def write(
	glos: GlossaryType,
	filename: str,
	dictzip: bool = True,
	install: bool = True,
) -> None:
	from pyglossary.text_utils import runDictzip
	(filename_nox, ext) = splitext(filename)
	if ext.lower() == ".index":
		filename = filename_nox
	indexFd = open(filename+".index", "wb")
	dictFd = open(filename+".dict", "wb")
	dictMark = 0
	for entry in glos:
		if entry.isData():
			# does dictd support resources? and how? FIXME
			continue
		word = toBytes(entry.getWord())
		defi = toBytes(entry.getDefi())
		lm = len(defi)
		indexFd.write(
			word + b"\t" +
			intToIndexStr(dictMark) + b"\t" +
			intToIndexStr(lm) + b"\n"
		)  # FIXME
		dictFd.write(toBytes(defi))
		dictMark += lm
	indexFd.close()
	dictFd.close()
	# for key, value in glos.iterInfo():
	#	if not value:
	#		continue
	#	pass  # FIXME
	if dictzip:
		runDictzip(filename)
	if install:
		installToDictd(filename, glos.getInfo("name").replace(" ", "_"))
