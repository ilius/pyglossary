# -*- coding: utf-8 -*-

from formats_common import *
from pyglossary.file_utils import fileCountLines

enable = True
format = "DictOrg"
description = "DICT.org file format (.index)"
extensions = (".index",)
optionsProp = {
	"dictzip": BoolOption(),
	"install": BoolOption(),
}
depends = {}
sortOnWrite = DEFAULT_YES

# https://en.wikipedia.org/wiki/DICT#DICT_file_format
tools = [
	{
		"name": "Dictd",
		"web": "https://directory.fsf.org/wiki/Dictd",
		"platforms": ["Linux"],
		"license": "GPL",
	},
	{
		"name": "GNOME Dictionary",
		"web": "https://wiki.gnome.org/Apps/Dictionary",
		"platforms": ["Linux"],
		"license": "GPL",
	},
	{
		"name": "Xfce4 Dictionary",
		"web": "https://docs.xfce.org/apps/xfce4-dict/start",
		"platforms": ["linux"],
		"license": "GPL",
	},
]

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
	dbListPath = join(targetDir, "db.list")
	if not isfile(dbListPath):
		log.error(
			f"{dbListPath} file not found"
			f", you may create it and try again"
			f"\nfailed to install to DICTD server directory: {targetDir}"
		)
		return

	log.info(f"Installing {filename!r} to DICTD server directory: {targetDir}")

	if os.path.isfile(filename + ".dict.dz"):
		dictExt = ".dict.dz"
	elif os.path.isfile(filename + ".dict"):
		dictExt = ".dict"
	else:
		log.error(f"No .dict file, could not install dictd file {filename!r}")
		return

	if not filename.startswith(targetDir):
		shutil.copy(filename + ".index", targetDir)
		shutil.copy(filename + dictExt, targetDir)

	fname = split(filename)[1]
	if not title:
		title = fname
	dataPath = join(targetDir, fname + dictExt)
	indexPath = join(targetDir, fname + ".index")
	dbInfo = f"""
database {title}
{{
  data {dataPath}
  index {indexPath}
}}
"""
	with open(dbListPath, "a") as dbFile:
		dbFile.write(dbInfo)


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
	dictzip: bool = False,
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
		word = entry.b_word
		defi = entry.b_defi
		lm = len(defi)
		indexFd.write(
			word + b"\t" +
			intToIndexStr(dictMark) + b"\t" +
			intToIndexStr(lm) + b"\n"
		)  # FIXME
		dictFd.write(defi)
		dictMark += lm
	indexFd.close()
	dictFd.close()
	# for key, value in glos.iterInfo():
	#	if not value:
	#		continue
	#	pass  # FIXME
	if dictzip:
		# FIXME: does not seem to work
		# dictd does not start
		# when try to start manually, gives this error:
		# :E: /usr/share/dictd/test.dict is not readable (data file)
		runDictzip(filename)
	if install:
		installToDictd(filename, glos.getInfo("name").replace(" ", "_"))
