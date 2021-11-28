# -*- coding: utf-8 -*-

import re
from formats_common import *
from pyglossary.file_utils import fileCountLines
from pyglossary.plugin_lib.dictdlib import DictDB

enable = True
lname = "dict_org"
format = "DictOrg"
description = "DICT.org file format (.index)"
extensions = (".index",)
optionsProp = {
	"dictzip": BoolOption(comment="Compress .dict file to .dict.dz"),
	"install": BoolOption(comment="Install dictionary to /usr/share/dictd/"),
}
sortOnWrite = DEFAULT_NO
kind = "directory"
wiki = "https://en.wikipedia.org/wiki/DICT#DICT_file_format"
website = (
	"http://dict.org/bin/Dict",
	"The DICT Development Group",
)


def installToDictd(filename: str, dictzip: bool, title: str = "") -> None:
	"""
	filename is without extension (neither .index or .dict or .dict.dz)
	"""
	import shutil
	import subprocess
	targetDir = "/usr/share/dictd/"
	if filename.startswith(targetDir):
		return

	if not isdir(targetDir):
		log.warning(f"Directory {targetDir!r} does not exist, skipping install")
		return

	log.info(f"Installing {filename!r} to DICTD server directory: {targetDir}")

	if dictzip and os.path.isfile(filename + ".dict.dz"):
		dictExt = ".dict.dz"
	elif os.path.isfile(filename + ".dict"):
		dictExt = ".dict"
	else:
		log.error(f"No .dict file, could not install dictd file {filename!r}")
		return

	if not filename.startswith(targetDir):
		shutil.copy(filename + ".index", targetDir)
		shutil.copy(filename + dictExt, targetDir)

	# update /var/lib/dictd/db.list
	if subprocess.call(["/usr/sbin/dictdconfig", "-w"]) != 0:
		log.error(
			"failed to update /var/lib/dictd/db.list file"
			", try manually runing: sudo /usr/sbin/dictdconfig -w"
		)

	log.info("don't forget to restart dictd server")


class Reader(object):
	def __init__(self, glos: GlossaryType):
		self._glos = glos
		self._filename = ""
		self._dictdb = None  # type: Optional[DictDB]

		# regular expression patterns used to prettify definition text
		self._re_newline_in_braces = re.compile(
			r'\{(?P<left>.*?)\n(?P<right>.*?)?\}',
		)
		self._re_words_in_braces = re.compile(
			r'\{(?P<word>.+?)\}',
		)

	def open(self, filename: str) -> None:
		import gzip
		if filename.endswith(".index"):
			filename = filename[:-6]
		self._filename = filename
		self._dictdb = DictDB(filename, "read", 1)

	def close(self) -> None:
		if self._dictdb is not None:
			self._dictdb.indexfile.close()
			self._dictdb.dictfile.close()
			# self._dictdb.finish()
			self._dictdb = None

	def prettifyDefinitionText(self, defi: str) -> str:
		# Handle words in {}
		# First, we remove any \n in {} pairs
		defi = self._re_newline_in_braces.sub(r'{\g<left>\g<right>}', defi)

		# Then, replace any {words} into <a href="bword://words">words</a>,
		# so it can be rendered as link correctly
		defi = self._re_words_in_braces.sub(
			r'<a href="bword://\g<word>">\g<word></a>',
			defi,
		)

		# Use <br /> so it can be rendered as newline correctly
		defi = defi.replace("\n", "<br />")
		return defi

	def __len__(self) -> int:
		if self._dictdb is None:
			return 0
		return len(self._dictdb.indexentries)

	def __iter__(self) -> "Iterator[BaseEntry]":
		if self._dictdb is None:
			raise RuntimeError("iterating over a reader while it's not open")
		dictdb = self._dictdb
		for word in dictdb.getdeflist():
			b_defi = b"\n\n<hr>\n\n".join(dictdb.getdef(word))
			try:
				defi = b_defi.decode("utf_8", 'ignore')
				defi = self.prettifyDefinitionText(defi)
			except Exception as e:
				log.error(f"b_defi = {b_defi}")
				raise e
			yield self._glos.newEntry(word, defi)


class Writer(object):
	_dictzip: bool = False
	_install: bool = True

	def __init__(self, glos: GlossaryType) -> None:
		self._glos = glos
		self._filename = None
		self._dictdb = None

	def finish(self):
		from pyglossary.os_utils import runDictzip
		self._dictdb.finish(dosort=1)
		if self._dictzip:
			runDictzip(f"{self._filename}.dict")
		if self._install:
			installToDictd(
				self._filename,
				self._dictzip,
				self._glos.getInfo("name").replace(" ", "_"),
			)
		self._filename = None

	def open(self, filename: str):
		filename_nox, ext = splitext(filename)
		if ext.lower() == ".index":
			filename = filename_nox
		self._dictdb = DictDB(filename, "write", 1)
		self._filename = filename

	def write(self) -> "Generator[None, BaseEntry, None]":
		dictdb = self._dictdb
		while True:
			entry = yield
			if entry is None:
				break
			if entry.isData():
				# does dictd support resources? and how? FIXME
				continue
			dictdb.addentry(entry.b_defi, entry.l_word)
