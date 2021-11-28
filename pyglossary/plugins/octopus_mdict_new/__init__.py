# -*- coding: utf-8 -*-
# Read Octopus MDict dictionary format, mdx(dictionary)/mdd(data)
#
# Copyright © 2013 Xiaoqiang Wang <xiaoqiangwang AT gmail DOT com>
# Copyright © 2013-2020 Saeed Rasooli <saeed.gnu@gmail.com>
#
# This program is a free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# You can get a copy of GNU General Public License along this program
# But you can always get it from http://www.gnu.org/licenses/gpl.txt
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

from formats_common import *

import os
import sys
import gc
from os.path import splitext, isfile, isdir, extsep, basename, dirname

enable = True
lname = "octopus_mdict"
format = "OctopusMdict"
description = "Octopus MDict (.mdx)"
extensions = (".mdx",)
extensionCreate = ""
singleFile = False
kind = "binary"
wiki = ""
website = (
	"https://www.mdict.cn/wp/?page_id=5325&lang=en",
	"Download | MDict.cn",
)
optionsProp = {
	"encoding": EncodingOption(),
	"substyle": BoolOption(
		comment="Enable substyle",
	),
	"same_dir_data_files": BoolOption(
		comment="Read data files from same directory",
	),
	"audio": BoolOption(
		comment="Enable audio objects",
	),
}

extraDocs = [
	(
		"`python-lzo` is required for **some** MDX glossaries.",
		"""First try converting your MDX file, if failed (`AssertionError` probably),
then try to install [LZO library and Python binding](./doc/lzo.md)."""
	),
]


class Reader(object):
	_encoding: str = ""
	_substyle: bool = True
	_same_dir_data_files: bool = False
	_audio: bool = False

	def __init__(self, glos):
		self._glos = glos
		self.clear()
		self._re_internal_link = re.compile('href=(["\'])(entry://|[dx]:)')
		self._re_audio_link = re.compile(
			'<a (type="sound" )?([^<>]*? )?href="sound://([^<>"]+)"( .*?)?>(.*?)</a>'
		)

	def clear(self):
		self._filename = ""
		self._mdx = None
		self._mdd = []
		self._wordCount = 0
		self._dataEntryCount = 0

		# dict of mainWord -> newline-separated alternatives
		self._linksDict = {}  # type: Dict[str, str]

	def open(self, filename):
		from pyglossary.plugin_lib.readmdict import MDX, MDD
		self._filename = filename
		self._mdx = MDX(filename, self._encoding, self._substyle)

		"""
			multiple MDD files are supported with this naming schema:
				FILE.mdx
				FILE.mdd
				FILE.1.mdd
				FILE.2.mdd
				FILE.3.mdd
		"""

		filenameNoExt, ext = splitext(self._filename)
		mddBase = "".join([filenameNoExt, extsep])
		for fname in (f"{mddBase}mdd", f"{mddBase}1.mdd"):
			if isfile(fname):
				self._mdd.append(MDD(fname))
		mddN = 2
		while isfile(f"{mddBase}{mddN}.mdd"):
			self._mdd.append(MDD(f"{mddBase}{mddN}.mdd"))
			mddN += 1

		dataEntryCount = 0
		for mdd in self._mdd:
			dataEntryCount += len(mdd)
		self._dataEntryCount = dataEntryCount
		log.info(f"Found {len(self._mdd)} mdd files with {dataEntryCount} entries")

		log.debug("mdx.header = " + pformat(self._mdx.header))
		# for key, value in self._mdx.header.items():
		# 	key = key.lower()
		# 	self._glos.setInfo(key, value)
		try:
			title = self._mdx.header[b"Title"]
		except KeyError:
			pass
		else:
			title = title.strip()
			if title:
				self._glos.setInfo("name", title)
		desc = self._mdx.header.get(b"Description", "")
		if desc:
			self._glos.setInfo("description", desc)

		self.loadLinks()

	def loadLinks(self):
		from pyglossary.plugin_lib.readmdict import MDX
		log.info("extracting links...")
		linksDict = {}
		word = ""
		wordCount = 0
		for b_word, b_defi in self._mdx.items():
			word = b_word.decode("utf-8")
			defi = b_defi.decode("utf-8").strip()
			if defi.startswith("@@@LINK="):
				if not word:
					log.warn(f"unexpected defi: {defi}")
					continue
				mainWord = defi[8:]
				if mainWord in linksDict:
					linksDict[mainWord] += "\n" + word
				else:
					linksDict[mainWord] = word
				continue
			wordCount += 1

		log.info(
			"extracting links done, "
			f"sizeof(linksDict)={sys.getsizeof(linksDict)}"
		)
		log.info(f"wordCount = {wordCount}")
		self._linksDict = linksDict
		self._wordCount = wordCount
		self._mdx = MDX(self._filename, self._encoding, self._substyle)

	def fixDefi(self, defi: str) -> str:
		defi = self._re_internal_link.sub(r'href=\1bword://', defi)
		defi = defi.replace(' src="file://', ' src=".')

		if self._audio:
			# \5 is the possible elements between <a ...> and </a>
			# but anything between <audio...> and </audio> is completely
			# ignored by Aaard2 Web and browser
			# and there is no point adding it after </audio>
			# which makes it shown after audio controls

			# GoldenDict acts completely different, so must use
			# audio_goldendict=True option in StarDict writer instead.

			defi = self._re_audio_link.sub(
				r'<audio controls src="\3"></audio>',
				defi,
			)

		return defi

	def __iter__(self):
		if self._mdx is None:
			log.error("trying to iterate on a closed MDX file")
			return

		glos = self._glos
		linksDict = self._linksDict
		for b_word, b_defi in self._mdx.items():
			word = b_word.decode("utf-8")
			defi = b_defi.decode("utf-8").strip()
			if defi.startswith("@@@LINK="):
				continue
			defi = self.fixDefi(defi)
			words = word
			altsStr = linksDict.get(word, "")
			if altsStr:
				words = [word] + altsStr.split("\n")
			yield glos.newEntry(words, defi)

		self._mdx = None
		del linksDict
		self._linksDict = {}
		gc.collect()

		if self._same_dir_data_files:
			dirPath = dirname(self._filename)
			for fname in os.listdir(dirPath):
				ext = splitext(fname)[1].lower()
				if ext in (".mdx", ".mdd"):
					continue
				fpath = join(dirPath, fname)
				with open(fpath, mode="rb") as _file:
					b_data = _file.read()
				yield glos.newDataEntry(fname, b_data)

		for mdd in self._mdd:
			try:
				for b_fname, b_data in mdd.items():
					fname = toStr(b_fname)
					fname = fname.replace("\\", os.sep).lstrip(os.sep)
					yield glos.newDataEntry(fname, b_data)
			except Exception as e:
				log.exception(f"Error reading {mdd.filename}")
		self._mdd = []

	def __len__(self):
		return self._wordCount + self._dataEntryCount

	def close(self):
		self.clear()
