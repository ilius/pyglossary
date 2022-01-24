# -*- coding: utf-8 -*-
# glossary_utils.py
#
# Copyright © 2008-2022 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
# This file is part of PyGlossary project, https://github.com/ilius/pyglossary
#
# This program is a free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. Or on Debian systems, from /usr/share/common-licenses/GPL
# If not, see <http://www.gnu.org/licenses/gpl.txt>.

import os
from os.path import (
	split,
	isdir,
	isfile,
	splitext,
)
import subprocess
import logging
import gc

from .compression import (
	compressionOpenFunc,
	stdCompressions,
)
from .entry import Entry

log = logging.getLogger("pyglossary")


class EntryList(object):
	def __init__(self, glos):
		self._l = []
		self._glos = glos
		self._sortKey = None

	def append(self, entry):
		self._l.append(entry.getRaw(self._glos))

	def insert(self, pos, entry):
		self._l.insert(pos, entry.getRaw(self._glos))

	def clear(self):
		self._l.clear()

	def __len__(self):
		return len(self._l)

	def __iter__(self):
		glos = self._glos
		for index, rawEntry in enumerate(self._l):
			if index & 0x7f == 0:  # 0x3f, 0x7f, 0xff
				gc.collect()
			yield Entry.fromRaw(
				glos, rawEntry,
				defaultDefiFormat=glos._defaultDefiFormat,
			)

	def setSortKey(self, sortKey, sampleItem):
		self._sortKey = Entry.getRawEntrySortKey(self._glos, sortKey)

	def sort(self):
		if self._sortKey is None:
			raise ValueError("EntryList.sort: sortKey is not set")
		self._l.sort(key=self._sortKey)

	def close(self):
		pass


def _zipFileAdd(zf, filename):
	if isfile(filename):
		zf.write(filename)
		return
	if not isdir(filename):
		raise OSError(f"Not a file or directory: {filename}")
	for subFname in os.listdir(filename):
		_zipFileAdd(zf, join(filename, subFname))


def zipFileOrDir(glos: "GlossaryType", filename: str) -> "Optional[str]":
	import zipfile
	import shutil
	from .os_utils import indir

	zf = zipfile.ZipFile(f"{filename}.zip", mode="w")

	if isdir(filename):
		dirn, name = split(filename)
		with indir(filename):
			for subFname in os.listdir(filename):
				_zipFileAdd(zf, subFname)

		shutil.rmtree(filename)
		return

	dirn, name = split(filename)
	files = [name]

	if isdir(f"{filename}_res"):
		files.append(f"{name}_res")

	with indir(dirn):
		for fname in files:
			_zipFileAdd(zf, fname)


def compress(glos: "GlossaryType", filename: str, compression: str) -> str:
	"""
	filename is the existing file path
	supported compressions: "gz", "bz2", "lzma", "zip"
	"""
	import shutil
	log.info(f"Compressing {filename!r} with {compression!r}")

	compFilename = f"{filename}.{compression}"
	if compression in stdCompressions:
		with compressionOpenFunc(compression)(compFilename, mode="wb") as dest:
			with open(filename, mode="rb") as source:
				shutil.copyfileobj(source, dest)
		return compFilename

	if compression == "zip":
		try:
			os.remove(compFilename)
		except OSError:
			pass
		try:
			error = zipFileOrDir(glos, filename)
		except Exception as e:
			log.error(
				f"{e}\nFailed to compress file \"{filename}\""
			)
	else:
		raise ValueError(f"unexpected compression={compression!r}")

	if isfile(compFilename):
		return compFilename
	else:
		return filename


def uncompress(srcFilename: str, dstFilename: str, compression: str) -> None:
	"""
	filename is the existing file path
	supported compressions: "gz", "bz2", "lzma"
	"""
	import shutil
	log.info(f"Uncompressing {srcFilename!r} to {dstFilename!r}")

	if compression in stdCompressions:
		with compressionOpenFunc(compression)(srcFilename, mode="rb") as source:
			with open(dstFilename, mode="wb") as dest:
				shutil.copyfileobj(source, dest)
		return

	# TODO: if compression == "zip":
	raise ValueError(f"unexpected compression={compression!r}")


def splitFilenameExt(
	filename: str = "",
) -> "Tuple[str, str, str]":
	"""
	returns (filenameNoExt, ext, compression)
	"""
	compression = ""
	filenameNoExt, ext = splitext(filename)
	ext = ext.lower()

	if not ext and len(filenameNoExt) < 5:
		filenameNoExt, ext = "", filenameNoExt

	if not ext:
		return filename, filename, "", ""

	if ext[1:] in stdCompressions + ("zip", "dz"):
		compression = ext[1:]
		filename = filenameNoExt
		filenameNoExt, ext = splitext(filename)
		ext = ext.lower()

	return filenameNoExt, filename, ext, compression
