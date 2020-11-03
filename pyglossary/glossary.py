# -*- coding: utf-8 -*-
# glossary.py
#
# Copyright © 2008-2020 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
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

import logging

import sys

import os
from os.path import (
	split,
	join,
	splitext,
	isfile,
	isdir,
	dirname,
	abspath,
)

from time import time as now
import re

from collections import OrderedDict as odict

import io
import gc

import gzip

from .flags import *
from . import core
from .core import userPluginsDir, cacheDir
from .entry_base import BaseEntry
from .entry import Entry, DataEntry
from .plugin_prop import PluginProp

from .langs import LangDict, Lang

from .text_utils import (
	fixUtf8,
)
from .compression import stdCompressions
from .glossary_type import GlossaryType

homePage = "https://github.com/ilius/pyglossary"
log = logging.getLogger("pyglossary")

langDict = LangDict()

file = io.BufferedReader


def get_ext(path: str) -> str:
	return splitext(path)[1].lower()


"""
sortKeyType = Optional[
	Callable[
		[bytes],
		"Tuple[bytes, bytes]",
	]
]
"""


class Glossary(GlossaryType):
	"""
	Direct access to glos.data is droped
	Use `glos.addEntryObj(glos.newEntry(word, defi, [defiFormat]))`
		where both word and defi can be list (including alternates) or string
	See help(glos.addEntryObj)

	Use `for entry in glos:` to iterate over entries (glossary data)
	See help(pyglossary.entry.Entry) for details

	"""

	# Should be changed according to plugins? FIXME
	infoKeysAliasDict = {
		"title": "name",
		"bookname": "name",
		"dbname": "name",
		##
		"sourcelang": "sourceLang",
		"inputlang": "sourceLang",
		"origlang": "sourceLang",
		##
		"targetlang": "targetLang",
		"outputlang": "targetLang",
		"destlang": "targetLang",
		##
		"license": "copyright",
		##
		# do not map "publisher" to "author"
		##
		# are there alternatives to "creationTime"
		# and "lastUpdated"?
	}

	plugins = {}  # type: Dict[str, PluginProp]
	pluginByExt = {}  # type: Dict[str, PluginProp]

	formatsReadOptions = {}  # type: Dict[str, OrderedDict[str, Any]]
	formatsWriteOptions = {}  # type: Dict[str, OrderedDict[str, Any]]
	# for example formatsReadOptions[format][optName] gives you the default value

	readFormats = []  # type: List[str]
	writeFormats = []  # type: List[str]

	@classmethod
	def loadPlugins(cls: "ClassVar", directory: str) -> None:
		import pkgutil
		"""
		executed on startup.  as name implies, loads plugins from directory
		"""
		# log.debug(f"Loading plugins from directory: {directory!r}")
		if not isdir(directory):
			log.error(f"Invalid plugin directory: {directory!r}")
			return

		sys.path.append(directory)
		pluginNames = [
			pluginName
			for _, pluginName, _ in pkgutil.iter_modules([directory])
		]
		pluginNames.sort()
		for pluginName in pluginNames:
			cls.loadPlugin(pluginName)
		sys.path.pop()

	@classmethod
	def loadPlugin(cls: "ClassVar", pluginName: str) -> None:
		try:
			plugin = __import__(pluginName)
		except ModuleNotFoundError as e:
			log.warning(f"Module {e.name!r} not found, skipping plugin {pluginName!r}")
			return
		except Exception as e:
			log.exception(f"Error while importing plugin {pluginName}")
			return

		if (not hasattr(plugin, "enable")) or (not plugin.enable):
			# log.debug(f"Plugin disabled or not a plugin: {pluginName}")
			return

		format = plugin.format

		extensions = plugin.extensions
		if not isinstance(extensions, tuple):
			msg = f"{format} plugin: extensions must be tuple"
			if isinstance(extensions, list):
				extensions = tuple(extensions)
				log.error(msg)
			else:
				raise ValueError(msg)

		if hasattr(plugin, "description"):
			desc = plugin.description
		else:
			desc = f"{format} ({extensions[0]})"

		prop = PluginProp(plugin)

		cls.plugins[format] = prop

		for ext in extensions:
			if ext.lower() != ext:
				log.error(f"non-lowercase extension={ext!r} in {pluginName} plugin")
			cls.pluginByExt[ext.lstrip(".")] = prop
			cls.pluginByExt[ext] = prop

		Reader = prop.readerClass
		if Reader is not None:
			options = prop.getReadOptions()
			cls.formatsReadOptions[format] = options
			cls.readFormats.append(format)
			Reader.formatName = format

		Writer = prop.writerClass
		if Writer is not None:
			options = prop.getWriteOptions()
			cls.formatsWriteOptions[format] = options
			cls.writeFormats.append(format)

		if not (Reader or Writer):
			log.warning(f"plugin {format} has no Reader nor Writer")

		if hasattr(plugin, "write"):
			log.error(
				f"plugin {format} has write function, "
				f"must migrate to Writer class"
			)

		return plugin

	@classmethod
	def detectInputFormat(
		cls,
		filename: str,
		format: str = "",
		quiet: bool = False,
	) -> "Optional[Tuple[str, str, str]]":
		"""
			returns (filename, format, compression) or None
		"""

		def error(msg: str) -> None:
			if not quiet:
				log.error(msg)
			return None

		filenameOrig = filename
		filenameNoExt, filename, ext, compression = cls.splitFilenameExt(filename)

		plugin = None
		if format:
			plugin = cls.plugins[format]
		else:
			plugin = cls.pluginByExt.get(ext)
			if not plugin:
				plugin = cls.findPlugin(filename)
				if not plugin:
					return error("Unable to detect write format!")

		if not plugin.canRead:
			return error(f"plugin {plugin.name} does not support reading")

		if compression in getattr(plugin.readerClass, "compressions", []):
			compression = ""
			filename = filenameOrig

		return filename, plugin.name, compression

	def clear(self) -> None:
		self._info = odict()

		self._data.clear()  # type: List[RawEntryType]

		readers = getattr(self, "_readers", [])
		for reader in readers:
			try:
				reader.close()
			except Exception:
				log.exception("")
		self._readers = []
		self._readersOpenArgs = {}

		self._iter = None
		self._entryFilters = []
		self._entryFiltersName = set()
		self._sort = False
		self._sortKey = None
		self._sortCacheSize = 0

		self._filename = ""
		self._defaultDefiFormat = "m"
		self._progressbar = True
		self.tmpDataDir = ""

	def __init__(
		self,
		info: "Optional[Dict[str, str]]" = None,
		ui: "Optional[UIBase]" = None,
	) -> None:
		"""
		info:	OrderedDict or dict instance, or None
				no need to copy OrderedDict instance before passing here
				we will not reference to it
		"""
		self._data = []
		self._rawEntryCompress = True
		self._cleanupPathList = []
		self.clear()
		if info:
			if not isinstance(info, (dict, odict)):
				raise TypeError(
					"Glossary: `info` has invalid type"
					", dict or OrderedDict expected"
				)
			for key, value in info.items():
				self.setInfo(key, value)

		self.ui = ui

	def _removeDir(self, dirPath):
		import shutil
		shutil.rmtree(dirPath)

	def cleanup(self):
		if not self._cleanupPathList:
			return
		if not self.getConfig("cleanup", True):
			log.info("Not cleaning up files:")
			log.info("\n".join(self._cleanupPathList))
			return
		for cleanupPath in self._cleanupPathList:
			if isfile(cleanupPath):
				log.debug(f"Removing file {cleanupPath}")
				try:
					os.remove(cleanupPath)
				except Exception:
					log.exception(f"error removing {cleanupPath}")
			elif isdir(cleanupPath):
				log.debug(f"Removing directory {cleanupPath}")
				try:
					self._removeDir(cleanupPath)
				except Exception:
					log.exception(f"error removing {cleanupPath}/")
			else:
				log.error(f"no such file or directory: {cleanupPath}")

	def setRawEntryCompress(self, enable: bool) -> bool:
		self._rawEntryCompress = enable

	def updateEntryFilters(self) -> None:
		from . import entry_filters as ef
		self._entryFilters = []
		config = getattr(self.ui, "config", {})

		self._entryFilters.append(ef.StripEntryFilter(self))
		self._entryFilters.append(ef.NonEmptyWordFilter(self))

		if config.get("skip_resources", False):
			self._entryFilters.append(ef.SkipDataEntryFilter(self))

		if config.get("utf8_check", True):
			self._entryFilters.append(ef.FixUnicodeFilter(self))

		if config.get("lower", True):
			self._entryFilters.append(ef.LowerWordFilter(self))

		if config.get("remove_html_all", False):
			self._entryFilters.append(ef.RemoveHtmlTagsAll(self))
		elif config.get("remove_html"):
			tags = config.get("remove_html").split(",")
			self._entryFilters.append(ef.RemoveHtmlTags(self, tags))

		if config.get("normalize_html", False):
			self._entryFilters.append(ef.NormalizeHtml(self))

		self._entryFilters.append(ef.LangEntryFilter(self))
		self._entryFilters.append(ef.CleanEntryFilter(self))
		self._entryFilters.append(ef.NonEmptyWordFilter(self))
		self._entryFilters.append(ef.NonEmptyDefiFilter(self))
		self._entryFilters.append(ef.RemoveEmptyAndDuplicateAltWords(self))

		if self.ui and self._progressbar:
			self._entryFilters.append(ef.ProgressBarEntryFilter(self))

		if log.level <= core.TRACE:
			try:
				import psutil
			except ModuleNotFoundError:
				pass
			else:
				self._entryFilters.append(ef.MaxMemoryUsageEntryFilter(self))

		self._entryFiltersName = {
			entryFilter.name
			for entryFilter in self._entryFilters
		}

	def prepareEntryFilters(self) -> None:
		"""
			call .prepare() method on all _entryFilters
			run this after glossary info is set and ready
			for most entry filters, it won't do anything
		"""
		for ef in self._entryFilters:
			ef.prepare()

	def removeHtmlTagsAll(self) -> None:
		from . import entry_filters as ef
		if ef.RemoveHtmlTagsAll.name in self._entryFiltersName:
			return
		self._entryFilters.append(ef.RemoveHtmlTagsAll(self))

	def __str__(self) -> str:
		return "glossary.Glossary"

	def _calcProgressThreshold(self, wordCount: int) -> int:
		return max(1, min(500, wordCount // 200))

	def _loadedEntryGen(self) -> "Iterator[BaseEntry]":
		if self._progressbar:
			self.progressInit("Writing")

		for index, rawEntry in enumerate(self._data):
			if index & 0x7f == 0:  # 0x3f, 0x7f, 0xff
				gc.collect()
			yield Entry.fromRaw(
				self,
				rawEntry,
				defaultDefiFormat=self._defaultDefiFormat
			)

		if self._progressbar:
			self.progressEnd()

	def _readersEntryGen(self) -> "Iterator[BaseEntry]":
		for reader in self._readers:
			wordCount = 0
			if self._progressbar:
				self.progressInit("Converting")
			try:
				for index, entry in enumerate(self._applyEntryFiltersGen(reader)):
					if entry is not None:
						yield entry
			finally:
				reader.close()
			if self._progressbar:
				self.progressEnd()

	def _applyEntryFiltersGen(
		self,
		gen: "Iterator[BaseEntry]",
	) -> "Iterator[BaseEntry]":
		for index, entry in enumerate(gen):
			if not entry:
				continue
			for entryFilter in self._entryFilters:
				entry = entryFilter.run(entry, index)
				if not entry:
					break
			else:
				yield entry

	def __iter__(self) -> "Iterator[BaseEntry]":
		if self._iter is None:
			log.error(
				"Trying to iterate over a blank Glossary"
				", must call `glos.read` first"
			)
			return iter([])
		return self._iter

	def setDefaultDefiFormat(self, defiFormat: str) -> None:
		"""
		defiFormat must be empty or one of these:
			"m": plain text
			"h": html
			"x": xdxf
		"""
		self._defaultDefiFormat = defiFormat

	def getDefaultDefiFormat(self) -> str:
		return self._defaultDefiFormat

	# TODO
	# def _reopenReader(self, reader):
	# 	log.info(f"re-opening {reader.__class__}")
	# 	filename, options = self._readersOpenArgs[reader]
	# 	reader.close()
	# 	reader.open(filename, **options)

	def collectDefiFormat(
		self,
		maxCount: int,
	) -> "Optional[Dict[str, float]]":
		"""
			example return value:
				[("h", 0.91), ("m", 0.09)]
		"""
		from collections import Counter
		readers = self._readers
		if readers:
			log.error("collectDefiFormat: not supported in direct mode")
			return None

		counter = Counter()
		count = 0
		for entry in self:
			if entry.isData():
				continue
			entry.detectDefiFormat()
			counter[entry.defiFormat] += 1
			count += 1
			if count >= maxCount:
				break

		result = {
			defiFormat: itemCount / count
			for defiFormat, itemCount in counter.items()
		}
		for defiFormat in ("h", "m", "x"):
			if defiFormat not in result:
				result[defiFormat] = 0

		# TODO
		# for reader in readers:
		# 	self._reopenReader(reader)
		# self._readers = readers

		self._updateIter()

		return result

	def __len__(self) -> int:
		return len(self._data) + sum(
			len(reader) for reader in self._readers
		)

	def infoKeys(self) -> "List[str]":
		return list(self._info.keys())

	# def formatInfoKeys(self, format: str):# FIXME

	def iterInfo(self) -> "Iterator[Tuple[str, str]]":
		return self._info.items()

	def getInfo(self, key: str) -> str:
		key = str(key)  # FIXME: required?
		key = self.infoKeysAliasDict.get(key.lower(), key)
		return self._info.get(key, "")  # "" or None as default? FIXME

	def setInfo(self, key: str, value: str) -> None:
		#  FIXME
		origKey = key
		key = fixUtf8(key)
		value = fixUtf8(value)

		key = self.infoKeysAliasDict.get(key.lower(), key)

		if origKey != key:
			log.debug(f"setInfo: {origKey} -> {key}")

		self._info[key] = value

	def getExtraInfos(self, excludeKeys: "List[str]") -> "odict":
		"""
		excludeKeys: a list of (basic) info keys to be excluded
		returns an OrderedDict including the rest of info keys,
				with associated values
		"""
		excludeKeySet = set()
		for key in excludeKeys:
			excludeKeySet.add(key)
			key2 = self.infoKeysAliasDict.get(key.lower())
			if key2:
				excludeKeySet.add(key2)

		extra = odict()
		for key, value in self._info.items():
			if key in excludeKeySet:
				continue
			extra[key] = value

		return extra

	def getAuthor(self) -> str:
		for key in ("author", "publisher"):
			value = self._info.get(key, "")
			if value:
				return value
		return ""

	def _getLangByStr(self, st) -> "Optional[Lang]":
		lang = langDict[st]
		if lang:
			return lang
		lang = langDict[st.lower()]
		if lang:
			return lang
		log.error(f"unknown language {st!r}")
		return

	def _getLangByInfoKey(self, key: str) -> "Optional[Lang]":
		st = self.getInfo(key)
		if not st:
			return
		return self._getLangByStr(st)

	@property
	def sourceLang(self) -> "Optional[Lang]":
		return self._getLangByInfoKey("sourceLang")

	@property
	def targetLang(self) -> "Optional[Lang]":
		return self._getLangByInfoKey("targetLang")

	@sourceLang.setter
	def sourceLang(self, lang) -> None:
		if not isinstance(lang, Lang):
			raise TypeError(f"invalid lang={lang}, must be a Lang object")
		self.setInfo("sourceLang", lang.name)

	@targetLang.setter
	def targetLang(self, lang) -> None:
		if not isinstance(lang, Lang):
			raise TypeError(f"invalid lang={lang}, must be a Lang object")
		self.setInfo("targetLang", lang.name)

	@property
	def sourceLangName(self) -> str:
		lang = self.sourceLang
		if lang is None:
			return ""
		return lang.name

	@sourceLangName.setter
	def sourceLangName(self, langName: str) -> None:
		if not langName:
			self.setInfo("sourceLang", "")
			return
		lang = self._getLangByStr(langName)
		if lang is None:
			return
		self.setInfo("sourceLang", lang.name)

	@property
	def targetLangName(self) -> str:
		lang = self.targetLang
		if lang is None:
			return ""
		return lang.name

	@targetLangName.setter
	def targetLangName(self, langName: str) -> None:
		if not langName:
			self.setInfo("targetLang", "")
			return
		lang = self._getLangByStr(langName)
		if lang is None:
			return
		self.setInfo("targetLang", lang.name)

	def titleElement(
		self,
		hf: "lxml.etree.htmlfile",
		sample: str = "",
	) -> "lxml.etree._FileWriterElement":
		from .langs.writing_system import getWritingSystemFromText
		sourceLang = self.sourceLang
		if sourceLang:
			return hf.element(sourceLang.titleTag)
		if sample:
			ws = getWritingSystemFromText(sample)
			if ws:
				return hf.element(ws.titleTag)
		return hf.element("b")

	def getConfig(self, name: str, default: "Optional[str]") -> "Optional[str]":
		if self.ui:
			return self.ui.config.get(name, default)
		else:
			return default

	def addEntryObj(self, entry: Entry) -> None:
		self._data.append(entry.getRaw(self))

	def newEntry(
		self,
		word: str,
		defi: str,
		defiFormat: str = "",
		byteProgress: "Optional[Tuple[int, int]]" = None,
	) -> "Entry":
		"""
		create and return a new entry object

		defiFormat must be empty or one of these:
			"m": plain text
			"h": html
			"x": xdxf
		"""
		if not defiFormat:
			defiFormat = self._defaultDefiFormat

		return Entry(
			word, defi,
			defiFormat=defiFormat,
			byteProgress=byteProgress,
		)

	def newDataEntry(self, fname: str, data: bytes) -> "DataEntry":
		inTmp = not self._readers
		return DataEntry(fname, data, inTmp)

	# ________________________________________________________________________#

	# def _hasWriteAccessToDir(self, dirPath: str) -> None:
	# 	if isdir(dirPath):
	# 		return os.access(dirPath, os.W_OK)
	# 	return os.access(dirname(dirPath), os.W_OK)

	def _createReader(self, format: str, options: "Dict[str, Any]") -> "Any":
		reader = self.plugins[format].readerClass(self)
		for name, value in options.items():
			setattr(reader, f"_{name}", value)
		return reader

	def detectLangsFromName(self):
		"""
		extract sourceLang and targetLang from glossary name/title
		"""
		name = self.getInfo("name")
		if not name:
			return
		if self.getInfo("sourceLang"):
			return
		for match in re.findall(
			r"(\w\w\w*)\s*(-| to )\s*(\w\w\w*)",
			name,
			flags=re.I,
		):
			sourceLang = langDict[match[0]]
			if sourceLang is None:
				log.info(f"Invalid language code/name {match[0]!r} in match={match}")
				continue
			targetLang = langDict[match[2]]
			if targetLang is None:
				log.info(f"Invalid language code/name {match[2]!r} in match={match}")
				continue
			self.sourceLang = sourceLang
			self.targetLang = targetLang
			log.info(
				f"Detected sourceLang={sourceLang.name!r}, "
				f"targetLang={targetLang.name!r} "
				f"from glossary name {name!r}"
			)
			return
		log.info(
			f"Failed to detect sourceLang and targetLang from glossary name {name!r}"
		)

	def read(
		self,
		filename: str,
		format: str = "",
		direct: bool = False,
		progressbar: bool = True,
		**options
	) -> bool:
		"""
		filename (str):	name/path of input file
		format (str):	name of input format,
						or "" to detect from file extension
		direct (bool):	enable direct mode
		"""
		filename = abspath(filename)

		# good thing about cacheDir is that we don't have to clean it up after
		# conversion is finished.
		# specially since dataEntry.save(...) will move the file from cacheDir
		# to the new directory (associated with output glossary path)
		# And we don't have to check for write access to cacheDir because it's
		# inside user's home dir. But input glossary might be in a directory
		# that we don't have write access to.
		# still maybe add a config key to decide if we should always use cacheDir
		# if self._hasWriteAccessToDir(f"{filename}_res", os.W_OK):
		# 	self.tmpDataDir = f"{filename}_res"
		# else:
		self.tmpDataDir = join(cacheDir, split(filename)[1] + "_res")
		os.makedirs(self.tmpDataDir, mode=0o700, exist_ok=True)
		self._cleanupPathList.append(self.tmpDataDir)

		# don't allow direct=False when there are readers
		# (read is called before with direct=True)
		if self._readers and not direct:
			raise ValueError(
				f"there are already {len(self._readers)} readers"
				f", you can not read with direct=False mode"
			)

		###
		inputArgs = self.detectInputFormat(filename, format=format)
		if inputArgs is None:
			return False
		origFilename = filename
		filename, format, compression = inputArgs

		if compression:
			from pyglossary.glossary_utils import uncompress
			uncompress(origFilename, filename, compression)

		validOptionKeys = list(self.formatsReadOptions[format].keys())
		for key in list(options.keys()):
			if key not in validOptionKeys:
				log.error(
					f"Invalid read option {key!r} "
					f"given for {format} format"
				)
				del options[key]

		filenameNoExt, ext = splitext(filename)
		if not ext.lower() in self.plugins[format].extensions:
			filenameNoExt = filename

		self._filename = filenameNoExt
		if not self.getInfo("name"):
			self.setInfo("name", split(filename)[1])
		self._progressbar = progressbar

		self.updateEntryFilters()

		reader = self._createReader(format, options)
		try:
			reader.open(filename)
		except Exception:
			log.exception("")
			return False
		self._readersOpenArgs[reader] = (filename, options)
		self.prepareEntryFilters()

		self._readers.append(reader)
		if not direct:
			self._inactivateDirectMode()

		self._updateIter()
		self.detectLangsFromName()

		return True

	def loadReader(self, reader: "Any") -> None:
		"""
		iterates over `reader` object and loads the whole data into self._data
		must call `reader.open(filename)` before calling this function
		"""
		from . import entry_filters as ef
		self.showMemoryUsage()
		progressbarFilter = None
		if self.ui and self._progressbar:
			progressbarFilter = ef.ProgressBarEntryFilter(self)
			self.progressInit("Reading")

		try:
			for index, entry in enumerate(self._applyEntryFiltersGen(reader)):
				if index & 0x7f == 0:  # 0x3f, 0x7f, 0xff
					gc.collect()
				if entry:
					self.addEntryObj(entry)
				if progressbarFilter is not None:
					progressbarFilter.run(entry, index)
		finally:
			reader.close()

		if self._progressbar:
			self.progressEnd()

		self.showMemoryUsage()

	def _inactivateDirectMode(self) -> None:
		"""
		loads all of `self._readers` into `self._data`
		closes readers
		and sets self._readers to []
		"""
		for reader in self._readers:
			self.loadReader(reader)
		self._readers = []

	def _updateIter(self) -> None:
		"""
		updates self._iter
		depending on:
			1- Wheather or not direct mode is On (self._readers not empty)
				or Off (self._readers empty)
			2- Wheather sort is True, and if it is,
				checks for self._sortKey and self._sortCacheSize
		"""
		if not self._readers:  # indirect mode
			self._iter = self._loadedEntryGen()
			return

		# direct mode
		if not self._sort:
			self._iter = self._readersEntryGen()
			return

		self._updateIterPartialSort()

	def _updateIterPartialSort(self) -> None:
		from .sort_stream import hsortStreamList
		sortKey = self._sortKey
		cacheSize = self._sortCacheSize
		log.info(f"Stream sorting enabled, cache size: {cacheSize}")
		# only sort by main word, or list of words + alternates? FIXME
		self._iter = hsortStreamList(
			self._readers,
			cacheSize,
			key=Entry.getEntrySortKey(sortKey),
		)

	def sortWords(
		self,
		key: "Optional[Callable[[bytes], Any]]" = None,
		cacheSize: int = 0,
	) -> None:
		if key is None:
			log.warning("sortWords: no key function is provided")
		if self._readers:
			self._sortKey = key
			if cacheSize > 0:
				self._sortCacheSize = cacheSize  # FIXME
		else:
			t0 = now()
			self._data.sort(
				key=Entry.getRawEntrySortKey(self, key),
			)
			log.info(f"Sorting took {now() - t0:.1f} seconds")
		self._sort = True
		self._updateIter()

	@classmethod
	def findPlugin(cls, query: str) -> "Optional[PluginProp]":
		"""
			find plugin by name or extention
		"""
		plugin = Glossary.plugins.get(query)
		if plugin:
			return plugin
		plugin = Glossary.pluginByExt.get(query)
		if plugin:
			return plugin
		return None

	@classmethod
	def splitFilenameExt(
		cls,
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

		if ext[1:] in stdCompressions + ("zip",):
			compression = ext[1:]
			filename = filenameNoExt
			filenameNoExt, ext = splitext(filename)
			ext = ext.lower()

		return filenameNoExt, filename, ext, compression

	@classmethod
	def detectOutputFormat(
		cls,
		filename: str = "",
		format: str = "",
		inputFilename: str = "",
		quiet: bool = False,
		addExt: bool = False,
	) -> "Optional[Tuple[str, str, str]]":
		"""
		returns (filename, format, compression) or None
		"""
		def error(msg: str) -> None:
			if not quiet:
				log.error(msg)
			return None

		plugin = None
		if format:
			plugin = Glossary.plugins.get(format)
			if not plugin:
				return error(f"Invalid write format {format}")
			if not plugin.canWrite:
				return error(f"plugin {plugin.name} does not support writing")

		if not filename:
			if not inputFilename:
				return error(f"Invalid filename {filename!r}")
			if not plugin:
				return error("No filename nor format is given for output file")
			if not plugin.canWrite:
				return error(f"plugin {plugin.name} does not support writing")
			filename = splitext(inputFilename)[0] + plugin.ext
			return filename, plugin.name, ""

		filenameOrig = filename
		filenameNoExt, filename, ext, compression = cls.splitFilenameExt(filename)

		if not plugin:
			plugin = cls.pluginByExt.get(ext)
			if not plugin:
				plugin = cls.findPlugin(filename)

		if not plugin:
			return error("Unable to detect write format!")

		if not plugin.canWrite:
			return error(f"plugin {plugin.name} does not support writing")

		if compression in getattr(plugin.writerClass, "compressions", []):
			compression = ""
			filename = filenameOrig

		if addExt:
			if not filenameNoExt:
				if inputFilename:
					ext = plugin.ext
					filename = splitext(inputFilename)[0] + ext
				else:
					error("inputFilename is empty")
			if not ext and plugin.ext:
				filename += plugin.ext

		return filename, plugin.name, compression

	def _createWriter(
		self,
		format: str,
		options: "Dict[str, Any]",
	) -> "Any":
		writer = self.plugins[format].writerClass(self)
		for name, value in options.items():
			setattr(writer, f"_{name}", value)
		return writer

	def write(
		self,
		filename: str,
		format: str,
		sort: "Optional[bool]" = None,
		sortKey: "Optional[Callable[[bytes], Any]]" = None,
		defaultSortKey: "Optional[Callable[[bytes], Any]]" = None,
		sortCacheSize: int = 0,
		**options
	) -> "Optional[str]":
		"""
		sort (bool):
			True (enable sorting),
			False (disable sorting),
			None (auto, get from UI)

		sortKey (callable or None):
			key function for sorting
			takes a word as argument, which is str or list (with alternates)

		defaultSortKey (callable or None):
			used when no sortKey was given, or found in plugin

		returns absolute path of output file, or None if failed
		"""
		filename = abspath(filename)

		validOptions = self.formatsWriteOptions.get(format)
		if validOptions is None:
			log.critical(f"No write support for {format!r} format")
			return
		validOptionKeys = list(validOptions.keys())
		for key in list(options.keys()):
			if key not in validOptionKeys:
				log.error(
					f"Invalid write option {key!r}"
					f" given for {format} format"
				)
				del options[key]

		plugin = self.plugins[format]
		sortOnWrite = plugin.sortOnWrite
		if sortOnWrite == ALWAYS:
			if sort is False:
				log.warning(
					f"Writing {format} requires sorting"
					f", ignoring user sort=False option"
				)
			sort = True
			sortCacheSize = 0
		elif sortOnWrite == DEFAULT_YES:
			if sort is None:
				sort = True
		elif sortOnWrite == DEFAULT_NO:
			if sort is None:
				sort = False
		elif sortOnWrite == NEVER:
			if sort:
				log.warning(
					"Plugin prevents sorting before write" +
					", ignoring user sort=True option"
				)
			sort = False

		if self._readers and sort and sortCacheSize == 0:
			log.warning(
				f"Full sort enabled, falling back to indirect mode"
			)
			self._inactivateDirectMode()
			log.info(f"Loaded {len(self._data)} entries")

		writer = None
		if format not in self.plugins or not self.plugins[format].canWrite:
			log.error(f"No Writer class found for plugin {format}")
			return

		log.info(f"Writing to {format} file {filename!r}")

		writer = self._createWriter(format, options)

		self._sort = sort

		if sort:
			writerSortKey = getattr(writer, "sortKey", None)
			if sortOnWrite == ALWAYS:
				if writerSortKey:
					if sortKey:
						log.warning(
							f"Ignoring user-defined sort order, and "
							f"using sortKey function from {format} plugin"
						)
					sortKey = writerSortKey
				else:
					log.error(f"No sortKey was found in plugin")

			if sortKey is None:
				if writerSortKey:
					log.info(f"Using sortKey from {format} plugin")
					sortKey = writerSortKey
				elif defaultSortKey:
					log.info(f"Using default sortKey")
					sortKey = defaultSortKey
				else:
					log.critical(f"No sortKey was found")
					return

			if self._readers:
				self._sortKey = sortKey
				if sortCacheSize > 0:
					self._sortCacheSize = sortCacheSize  # FIXME
			else:
				t0 = now()
				self._data.sort(key=Entry.getRawEntrySortKey(self, sortKey))
				log.info(f"Sorting took {now() - t0:.1f} seconds")

		self._updateIter()
		try:
			writer.open(filename)
		except Exception:
			log.exception("")
			return False

		for reader in self._readers:
			log.info(
				f"Using Reader class from {reader.formatName} plugin"
				f" for direct conversion without loading into memory"
			)

		self.showMemoryUsage()

		writerList = [writer]
		try:
			genList = []
			gen = writer.write()
			if gen is None:
				log.error(f"{format} write function is not a generator")
			else:
				genList.append(gen)

			if self.getConfig("save_info_json", False):
				infoWriter = self._createWriter("Info", {})
				filenameNoExt, _, _, _ = Glossary.splitFilenameExt(filename)
				infoWriter.open(f"{filenameNoExt}.info")
				genList.append(infoWriter.write())
				writerList.append(infoWriter)

			for gen in genList:
				gen.send(None)
			for entry in self:
				for gen in genList:
					gen.send(entry)
			for gen in genList:
				try:
					gen.send(None)
				except StopIteration:
					pass
		except Exception:
			log.exception("Exception while calling plugin\'s write function")
			return
		finally:
			self.showMemoryUsage()
			log.debug("Running writer.finish()")
			for writer in writerList:
				writer.finish()
			self.clear()

		self.showMemoryUsage()

		return filename

	def _compressOutput(self, filename: str, compression: str) -> str:
		from pyglossary.glossary_utils import compress
		return compress(self, filename, compression)

	def convert(
		self,
		inputFilename: str,
		inputFormat: str = "",
		direct: "Optional[bool]" = None,
		progressbar: bool = True,
		outputFilename: str = "",
		outputFormat: str = "",
		sort: "Optional[bool]" = None,
		sortKey: "Optional[Callable[[bytes], Any]]" = None,
		defaultSortKey: "Optional[Callable[[bytes], Any]]" = None,
		sortCacheSize: int = 0,
		readOptions: "Optional[Dict[str, Any]]" = None,
		writeOptions: "Optional[Dict[str, Any]]" = None,
	) -> "Optional[str]":
		"""
		returns absolute path of output file, or None if failed

		defaultSortKey is used when no sortKey was given, or found in plugin
		"""
		if not readOptions:
			readOptions = {}
		if not writeOptions:
			writeOptions = {}

		if outputFilename == inputFilename:
			log.error(f"Input and output files are the same")
			return

		if readOptions:
			log.info(f"readOptions = {readOptions}")
		if writeOptions:
			log.info(f"writeOptions = {writeOptions}")

		outputArgs = self.detectOutputFormat(
			filename=outputFilename,
			format=outputFormat,
			inputFilename=inputFilename,
		)
		if not outputArgs:
			log.error(f"Writing file {outputFilename!r} failed.")
			return
		outputFilename, outputFormat, compression = outputArgs

		if direct is None:
			if sort is not True:
				direct = True  # FIXME

		if isdir(outputFilename):
			log.error(f"Directory already exists: {outputFilename}")
			return

		self.showMemoryUsage()

		tm0 = now()
		if not self.read(
			inputFilename,
			format=inputFormat,
			direct=direct,
			progressbar=progressbar,
			**readOptions
		):
			return
		log.info("")

		finalOutputFile = self.write(
			outputFilename,
			outputFormat,
			sort=sort,
			sortKey=sortKey,
			defaultSortKey=defaultSortKey,
			sortCacheSize=sortCacheSize,
			**writeOptions
		)
		log.info("")
		if not finalOutputFile:
			log.error(f"Writing file {outputFilename!r} failed.")
			return

		if compression:
			finalOutputFile = self._compressOutput(finalOutputFile, compression)

		log.info(f"Writing file {finalOutputFile!r} done.")
		log.info(f"Running time of convert: {now()-tm0:.1f} seconds")
		self.showMemoryUsage()
		self.cleanup()

		return finalOutputFile

	# ________________________________________________________________________#

	def writeTxt(
		self,
		entryFmt: str = "",  # contain {word} and {defi}
		filename: str = "",
		writeInfo: bool = True,
		wordEscapeFunc: "Optional[Callable]" = None,
		defiEscapeFunc: "Optional[Callable]" = None,
		ext: str = ".txt",
		head: str = "",
		tail: str = "",
		outInfoKeysAliasDict: "Optional[Dict[str, str]]" = None,
		# TODO: replace above arg with a func?
		encoding: str = "utf-8",
		newline: str = "\n",
		resources: bool = True,
	) -> "Generator[None, BaseEntry, None]":
		from .compression import compressionOpen as c_open
		if not entryFmt:
			raise ValueError("entryFmt argument is missing")
		if not filename:
			filename = self._filename + ext

		if not outInfoKeysAliasDict:
			outInfoKeysAliasDict = {}

		fileObj = c_open(filename, mode="wt", encoding=encoding, newline=newline)

		fileObj.write(head)
		if writeInfo:
			for key, value in self._info.items():
				# both key and value are supposed to be non-empty string
				if not (key and value):
					log.warning(f"skipping info key={key!r}, value={value!r}")
					continue
				key = outInfoKeysAliasDict.get(key, key)
				if not key:
					continue
				word = f"##{key}"
				if wordEscapeFunc is not None:
					word = wordEscapeFunc(word)
					if not word:
						continue
				if defiEscapeFunc is not None:
					value = defiEscapeFunc(value)
					if not value:
						continue
				fileObj.write(entryFmt.format(
					word=word,
					defi=value,
				))
		fileObj.flush()

		myResDir = f"{filename}_res"
		if not isdir(myResDir):
			os.mkdir(myResDir)

		while True:
			entry = yield
			if entry is None:
				break
			if entry.isData():
				if resources:
					entry.save(myResDir)
				continue

			word = entry.s_word
			defi = entry.defi
			if word.startswith("#"):  # FIXME
				continue
			# if self.getConfig("enable_alts", True):  # FIXME

			if wordEscapeFunc is not None:
				word = wordEscapeFunc(word)
			if defiEscapeFunc is not None:
				defi = defiEscapeFunc(defi)
			fileObj.write(entryFmt.format(word=word, defi=defi))

		if tail:
			fileObj.write(tail)

		fileObj.close()
		if not os.listdir(myResDir):
			os.rmdir(myResDir)

	def writeTabfile(
		self,
		filename: str = "",
		**kwargs,
	) -> "Generator[None, BaseEntry, None]":
		from .text_utils import escapeNTB
		yield from self.writeTxt(
			entryFmt="{word}\t{defi}\n",
			filename=filename,
			wordEscapeFunc=escapeNTB,
			defiEscapeFunc=escapeNTB,
			ext=".txt",
			**kwargs
		)

	# ________________________________________________________________________#

	def progressInit(self, *args) -> None:
		if self.ui:
			self.ui.progressInit(*args)

	def progress(self, pos: int, total: int, unit: str = "entries") -> None:
		if not self.ui:
			return
		if total == 0:
			log.warning(f"pos={pos}, total={total}")
			return
		self.ui.progress(
			min(pos + 1, total) / total,
			f"{pos:,} / {total:,} {unit}",
		)

	def progressEnd(self) -> None:
		if self.ui:
			self.ui.progressEnd()

	def showMemoryUsage(self):
		if log.level > core.TRACE:
			return
		try:
			import psutil
		except ModuleNotFoundError:
			return
		usage = psutil.Process(os.getpid()).memory_info().rss // 1024
		log.trace(f"Memory Usage: {usage} kB")

	# ________________________________________________________________________#

	@classmethod
	def init(cls):
		cls.readFormats = []
		cls.writeFormats = []
		cls.loadPlugins(join(dirname(__file__), "plugins"))
		cls.loadPlugins(userPluginsDir)
