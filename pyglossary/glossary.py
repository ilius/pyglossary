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
	basename,
	abspath,
)

from time import time as now
import subprocess
import re

import pkgutil
from collections import OrderedDict as odict

import io
import gc

from typing import (
	Dict,
	Tuple,
	List,
	Any,
	Optional,
	ClassVar,
	Iterator,
	Callable,
)

from .flags import *
from . import core
from .core import VERSION, userPluginsDir, cacheDir
from .entry_base import BaseEntry
from .entry import Entry, DataEntry
from .plugin_prop import PluginProp
from .langs import LangDict, Lang
from .sort_stream import hsortStreamList

from .text_utils import (
	fixUtf8,
)
from .os_utils import indir

from .glossary_type import GlossaryType

homePage = "https://github.com/ilius/pyglossary"
log = logging.getLogger("root")

langDict = LangDict()

file = io.BufferedReader


def get_ext(path: str) -> str:
	return splitext(path)[1].lower()


sortKeyType = Optional[
	Callable[
		[bytes],
		Tuple[bytes, bytes],
	]
]


class Glossary(GlossaryType):
	"""
	Direct access to glos.data is droped
	Use `glos.addEntry(word, defi, [defiFormat])`
		where both word and defi can be list (including alternates) or string
	See help(glos.addEntry)

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

	plugins = {}  # format name => PluginProp
	pluginByDesc = {}  # description => PluginProp
	pluginByExt = {}  # extension => PluginProp

	readerClasses = {}
	writeFunctions = {}
	writerClasses = {}
	formatsReadOptions = {}
	formatsWriteOptions = {}

	readFormats = []
	writeFormats = []
	readExt = []
	writeExt = []
	readDesc = []
	writeDesc = []

	@classmethod
	def loadPlugins(cls: ClassVar, directory: str) -> None:
		"""
		executed on startup.  as name implies, loads plugins from directory
		"""
		log.debug(f"Loading plugins from directory: {directory!r}")
		if not isdir(directory):
			log.error(f"Invalid plugin directory: {directory!r}")
			return

		sys.path.append(directory)
		for _, pluginName, _ in pkgutil.iter_modules([directory]):
			cls.loadPlugin(pluginName)
		sys.path.pop()

	@classmethod
	def getRWOptionsFromFunc(cls, func, format):
		import inspect
		optionsProp = cls.plugins[format].optionsProp
		sig = inspect.signature(func)
		optNames = []
		for name, param in sig.parameters.items():
			if param.default is inspect._empty:
				if name not in ("self", "glos", "filename", "dirname", "kwargs"):
					log.warning(f"empty default value for {name}: {param.default}")
				continue  # non-keyword argument
			if name not in optionsProp:
				log.warning(f"skipping option {name} in plugin {format}")
				continue
			prop = optionsProp[name]
			if prop.disabled:
				log.debug(f"skipping disabled option {name} in {format} plugin")
				continue
			if not prop.validate(param.default):
				log.warning(
					"invalid default value for option: "
					f"{name} = {param.default!r}"
				)
			optNames.append(name)
		return optNames

	@classmethod
	def loadPlugin(cls: ClassVar, pluginName: str) -> None:
		try:
			plugin = __import__(pluginName)
		except ModuleNotFoundError as e:
			log.warning(f"Module {e.name!r} not found, skipping plugin {pluginName!r}")
			return
		except Exception as e:
			log.exception(f"Error while importing plugin {pluginName}")
			return

		if (not hasattr(plugin, "enable")) or (not plugin.enable):
			log.debug(f"Plugin disabled or not a plugin: {pluginName}")
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
		cls.pluginByDesc[desc] = prop

		for ext in extensions:
			cls.pluginByExt[ext] = prop

		hasReadSupport = False
		try:
			Reader = plugin.Reader
		except AttributeError:
			pass
		else:
			for attr in (
				"__init__",
				"open",
				"close",
				"__len__",
				"__iter__",
			):
				if not hasattr(Reader, attr):
					log.error(
						f"Invalid Reader class in {format!r} plugin"
						f", no {attr!r} method"
					)
					break
			else:
				cls.readerClasses[format] = Reader
				hasReadSupport = True
				options = cls.getRWOptionsFromFunc(
					Reader.open,
					format,
				)
				cls.formatsReadOptions[format] = options
				Reader.formatName = format

		if hasReadSupport:
			cls.readFormats.append(format)
			cls.readExt.append(extensions)
			cls.readDesc.append(desc)

		hasWriteSupport = False
		if hasattr(plugin, "Writer"):
			cls.writerClasses[format] = plugin.Writer
			options = cls.getRWOptionsFromFunc(
				plugin.Writer.write,
				format,
			)
			cls.formatsWriteOptions[format] = options
			hasWriteSupport = True

		if not hasWriteSupport and hasattr(plugin, "write"):
			cls.writeFunctions[format] = plugin.write
			options = cls.getRWOptionsFromFunc(
				plugin.write,
				format,
			)
			cls.formatsWriteOptions[format] = options
			hasWriteSupport = True

		if hasWriteSupport:
			cls.writeFormats.append(format)
			cls.writeExt.append(extensions)
			cls.writeDesc.append(desc)

		return plugin

	@classmethod
	def detectInputFormat(cls, filename, format=""):
		if not format:
			ext = get_ext(filename)
			for name, plug in Glossary.plugins.items():
				if ext in plug.extensions:
					format = name

		return format

	def clear(self) -> None:
		self._info = odict()

		self._data = []

		try:
			readers = self._readers
		except AttributeError:
			pass
		else:
			for reader in readers:
				try:
					reader.close()
				except Exception:
					log.exception("")
		self._readers = []

		self._iter = None
		self._entryFilters = []
		self._entryFiltersName = set()
		self._sortKey = None
		self._sortCacheSize = 1000

		self._filename = ""
		self._defaultDefiFormat = "m"
		self._progressbar = True
		self._rawEntryCompress = True
		self.tmpDataDir = ""

	def __init__(
		self,
		info: Optional[Dict[str, str]] = None,
		ui: Any = None,
	) -> None:
		"""
		info:	OrderedDict instance, or None
				no need to copy OrderedDict instance,
				we will not reference to it
		"""
		self.clear()
		if info:
			if not isinstance(info, (dict, odict)):
				raise TypeError(
					"Glossary: `info` has invalid type"
					", dict or OrderedDict expected"
				)
			for key, value in info.items():
				self.setInfo(key, value)

		"""
		self._data is a list of tuples with length 2 or 3:
			(word, definition)
			(word, definition, defiFormat)
			where both word and definition can be a string, or list
				(containing word and alternates)

			defiFormat: format of the definition:
				"m": plain text
				"h": html
				"x": xdxf
		"""
		self.ui = ui

	# def setRawEntryCompress(self, enable: bool) -> bool:
	# 	self._rawEntryCompress = enable

	def updateEntryFilters(self) -> None:
		from . import entry_filters as ef
		self._entryFilters = []
		pref = getattr(self.ui, "pref", {})

		self._entryFilters.append(ef.StripEntryFilter(self))
		self._entryFilters.append(ef.NonEmptyWordFilter(self))

		if pref.get("skipResources", False):
			self._entryFilters.append(ef.SkipDataEntryFilter(self))

		if pref.get("utf8Check", True):
			self._entryFilters.append(ef.FixUnicodeFilter(self))

		if pref.get("lower", True):
			self._entryFilters.append(ef.LowerWordFilter(self))

		if pref.get("remove_html_all", False):
			self._entryFilters.append(ef.RemoveHtmlTagsAll(self))
		elif pref.get("remove_html"):
			tags = pref.get("remove_html").split(",")
			self._entryFilters.append(ef.RemoveHtmlTags(self, tags))

		self._entryFilters.append(ef.LangEntryFilter(self))
		self._entryFilters.append(ef.CleanEntryFilter(self))
		self._entryFilters.append(ef.NonEmptyWordFilter(self))
		self._entryFilters.append(ef.NonEmptyDefiFilter(self))
		self._entryFilters.append(ef.RemoveEmptyAndDuplicateAltWords(self))

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

	def addEntryObj(self, entry: Entry) -> None:
		self._data.append(entry.getRaw(self))

	def newEntry(
		self,
		word: str,
		defi: str,
		defiFormat: str = "",
		byteProgress: Optional[Tuple[int, int]] = None,
	) -> Entry:
		"""
		create and return a new entry object
		"""
		if not defiFormat:
			defiFormat = self._defaultDefiFormat

		return Entry(
			word, defi,
			defiFormat=defiFormat,
			byteProgress=byteProgress,
		)

	def addEntry(self, word: str, defi: str, defiFormat: str = "") -> None:
		"""
		create and add a new entry object to glossary
		"""
		self.addEntryObj(self.newEntry(word, defi, defiFormat))

	def _loadedEntryGen(self) -> Iterator[BaseEntry]:
		wordCount = len(self._data)
		wcThreshold = wordCount // 200 + 1
		progressbar = self.ui and self._progressbar
		if progressbar:
			self.progressInit("Writing")
		for index, rawEntry in enumerate(self._data):
			if index & 0x7f == 0:  # 0x3f, 0x7f, 0xff
				gc.collect()
			yield Entry.fromRaw(
				self,
				rawEntry,
				defaultDefiFormat=self._defaultDefiFormat
			)
			if progressbar and index % wcThreshold == 0:
				self.progress(index, wordCount)
		if progressbar:
			self.progressEnd()

	def _readersEntryGen(self) -> Iterator[BaseEntry]:
		for reader in self._readers:
			wordCount = 0
			progressbar = False
			if self.ui and self._progressbar:
				try:
					wordCount = len(reader)
				except Exception:
					log.exception("")
				if wordCount >= 0:
					progressbar = True
			if progressbar:
				self.progressInit("Converting")
			wcThreshold = wordCount // 200 + 1
			lastPos = 0
			try:
				for index, entry in enumerate(reader):
					yield entry
					if progressbar:
						if entry is None or wordCount > 0:
							if index % wcThreshold == 0:
								self.progress(index, wordCount)
							continue
						bp = entry.byteProgress()
						if bp and bp[0] > lastPos + 10000:
							self.progress(bp[0], bp[1], unit="bytes")
							lastPos = bp[0]
			finally:
				reader.close()
			if progressbar:
				self.progressEnd()

	def _applyEntryFiltersGen(
		self,
		gen: Iterator[BaseEntry],
	) -> Iterator[BaseEntry]:
		for entry in gen:
			if not entry:
				continue
			for entryFilter in self._entryFilters:
				entry = entryFilter.run(entry)
				if not entry:
					break
			else:
				yield entry

	def __iter__(self) -> Iterator[BaseEntry]:
		if self._iter is None:
			log.error(
				"Trying to iterate over a blank Glossary"
				", must call `glos.read` first"
			)
			return iter([])
		return self._iter

	def iterEntryBuckets(self, size: int) -> Iterator[BaseEntry]:
		"""
		iterate over buckets of entries, with size `size`
		For example:
			for bucket in glos.iterEntryBuckets(100):
				assert len(bucket) == 100
				for entry in bucket:
					print(entry.word)
				print("-----------------")
		"""
		bucket = []
		for entry in self:
			if len(bucket) >= size:
				yield bucket
				bucket = []
			bucket.append(entry)
		yield bucket

	def setDefaultDefiFormat(self, defiFormat: str) -> None:
		self._defaultDefiFormat = defiFormat

	def getDefaultDefiFormat(self) -> str:
		return self._defaultDefiFormat

	def __len__(self) -> int:
		return len(self._data) + sum(
			len(reader) for reader in self._readers
		)

	def infoKeys(self) -> List[str]:
		return list(self._info.keys())

	# def formatInfoKeys(self, format: str):# FIXME

	def iterInfo(self) -> Iterator[Tuple[str, str]]:
		return self._info.items()

	def getInfo(self, key: str) -> str:
		key = str(key)  # FIXME: required?

		try:
			key = self.infoKeysAliasDict[key.lower()]
		except KeyError:
			pass

		return self._info.get(key, "")  # "" or None as default? FIXME

	def setInfo(self, key: str, value: str) -> None:
		#  FIXME
		origKey = key
		key = fixUtf8(key)
		value = fixUtf8(value)

		try:
			key = self.infoKeysAliasDict[key.lower()]
		except KeyError:
			pass

		if origKey != key:
			log.debug(f"setInfo: {origKey} -> {key}")

		self._info[key] = value

	def getExtraInfos(self, excludeKeys: List[str]) -> odict:
		"""
		excludeKeys: a list of (basic) info keys to be excluded
		returns an OrderedDict including the rest of info keys,
				with associated values
		"""
		excludeKeySet = set()
		for key in excludeKeys:
			excludeKeySet.add(key)
			try:
				excludeKeySet.add(self.infoKeysAliasDict[key.lower()])
			except KeyError:
				pass

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

	def _getLangByInfoKey(self, key: str) -> Optional[Lang]:
		st = self.getInfo(key)
		if not st:
			return
		lang = langDict[st]
		if lang:
			return lang
		lang = langDict[st.lower()]
		if lang:
			return lang
		return

	@property
	def sourceLang(self) -> Optional[Lang]:
		return self._getLangByInfoKey("sourceLang")

	@property
	def targetLang(self) -> Optional[Lang]:
		return self._getLangByInfoKey("targetLang")

	def getPref(self, name: str, default: Optional[str]) -> Optional[str]:
		if self.ui:
			return self.ui.pref.get(name, default)
		else:
			return default

	def newDataEntry(self, fname: str, data: bytes) -> DataEntry:
		inTmp = not self._readers
		return DataEntry(fname, data, inTmp)

	# ________________________________________________________________________#

	def _hasWriteAccessToDir(self, dirPath: str) -> None:
		if isdir(dirPath):
			return os.access(dirPath, os.W_OK)
		return os.access(dirname(dirPath), os.W_OK)

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
		# still maybe add a pref key to decide if we should always use cacheDir
		# if self._hasWriteAccessToDir(f"{filename}_res", os.W_OK):
		# 	self.tmpDataDir = f"{filename}_res"
		# else:
		self.tmpDataDir = join(cacheDir, split(filename)[1] + "_res")

		# don't allow direct=False when there are readers
		# (read is called before with direct=True)
		if self._readers and not direct:
			raise ValueError(
				f"there are already {len(self._readers)} readers"
				f", you can not read with direct=False mode"
			)

		###
		format = self.detectInputFormat(filename, format=format)
		if not format:
			log.error(f"Could not detect input format from file name: {filename!r}")
			return False

		validOptionKeys = self.formatsReadOptions[format]
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

		Reader = self.readerClasses[format]
		reader = Reader(self)
		reader.open(filename, **options)
		self.prepareEntryFilters()
		if direct:
			self._readers.append(reader)
		else:
			self.loadReader(reader)

		self._updateIter()

		return True

	def loadReader(self, reader: Any) -> bool:
		"""
		iterates over `reader` object and loads the whole data into self._data
		must call `reader.open(filename)` before calling this function
		"""
		wordCount = 0
		progressbar = False
		if self.ui and self._progressbar:
			try:
				wordCount = len(reader)
			except Exception:
				log.exception("")
			progressbar = True
		if progressbar:
			self.progressInit("Reading")
		wcThreshold = wordCount // 200 + 1
		lastPos = 0
		try:
			for index, entry in enumerate(reader):
				if index & 0x7f == 0:  # 0x3f, 0x7f, 0xff
					gc.collect()
				if entry:
					self.addEntryObj(entry)
				if progressbar:
					if entry is None or wordCount > 0:
						if index % wcThreshold == 0:
							self.progress(index, wordCount)
						continue
					bp = entry.byteProgress()
					if bp and bp[0] > lastPos + 20000:
						self.progress(bp[0], bp[1], unit="bytes")
						lastPos = bp[0]
		finally:
			reader.close()
		if progressbar:
			self.progressEnd()

		return True

	def _inactivateDirectMode(self) -> None:
		"""
		loads all of `self._readers` into `self._data`
		closes readers
		and sets self._readers to []
		"""
		for reader in self._readers:
			self.loadReader(reader)
		self._readers = []

	def _updateIter(self, sort: bool = False) -> None:
		"""
		updates self._iter
		depending on:
			1- Wheather or not direct mode is On (self._readers not empty)
				or Off (self._readers empty)
			2- Wheather sort is True, and if it is,
				checks for self._sortKey and self._sortCacheSize
		"""
		if self._readers:  # direct mode
			if sort:
				sortKey = self._sortKey
				cacheSize = self._sortCacheSize
				log.info(f"Stream sorting enabled, cache size: {cacheSize}")
				# only sort by main word, or list of words + alternates? FIXME
				gen = hsortStreamList(
					self._readers,
					cacheSize,
					key=Entry.getEntrySortKey(sortKey),
				)
			else:
				gen = self._readersEntryGen()
		else:
			gen = self._loadedEntryGen()

		self._iter = self._applyEntryFiltersGen(gen)

	def sortWords(
		self,
		key: Optional[Callable[[bytes], Any]] = None,
		cacheSize: int = 0,
	) -> None:
		if key is None:
			log.warn("WARNING: sortWords: no key function is provided")
		if self._readers:
			self._sortKey = key
			if cacheSize > 0:
				self._sortCacheSize = cacheSize  # FIXME
		else:
			t0 = now()
			self._data.sort(
				key=Entry.getRawEntrySortKey(key),
			)
			log.info(f"Sorting took {now() - t0:.1f} seconds")
		self._updateIter(sort=True)

	@classmethod
	def detectOutputFormat(
		cls,
		filename: str = "",
		format: str = "",
		inputFilename: str = "",
	) -> Optional[Tuple[str, str, str]]:
		"""
		returns (filename, format, compression) or None
		"""
		compression = ""
		if filename:
			ext = ""
			filenameNoExt, fext = splitext(filename)
			fext = fext.lower()
			if fext in (".gz", ".bz2", ".zip"):
				compression = fext[1:]
				filename = filenameNoExt
				fext = get_ext(filename)
			if not format:
				for fmt, plug in Glossary.plugins.items():
					for e in plug.extensions:
						if format == e[1:] or format == e:
							format = fmt
							ext = e
							break
					if format:
						break
				if not format:
					for fmt, plug in Glossary.plugins.items():
						extList = plug.extensions
						if filename == fmt:
							if not inputFilename:
								log.error("inputFilename is empty")
							else:
								format = filename
								ext = extList[0]
								filename = inputFilename + ext
								break
						for e in extList:
							if not inputFilename:
								log.error("inputFilename is empty")
							elif filename == e[1:] or filename == e:
								format = fmt
								ext = e
								filename = inputFilename + ext
								break
						if format:
							break
				if not format:
					for fmt, plug in Glossary.plugins.items():
						if fext in plug.extensions:
							format = fmt
							ext = fext
			if not format:
				log.error("Unable to detect write format!")
				return

		else:  # filename is empty
			if not inputFilename:
				log.error(f"Invalid filename {filename!r}")
				return
			filename = inputFilename  # no extension
			if not format:
				log.error("No filename nor format is given for output file")
				return
			try:
				filename += Glossary.plugins[format].extensions[0]
			except KeyError:
				log.error("Invalid write format")
				return

		return filename, format, compression

	def write(
		self,
		filename: str,
		format: str,
		sort: Optional[bool] = None,
		sortKey: Optional[Callable[[bytes], Any]] = None,
		sortCacheSize: int = 1000,
		**options
	) -> Optional[str]:
		"""
		sort (bool):
			True (enable sorting),
			False (disable sorting),
			None (auto, get from UI)
		sortKey (callable or None):
			key function for sorting
			takes a word as argument, which is str or list (with alternates)

		returns absolute path of output file, or None if failed
		"""
		try:
			validOptionKeys = self.formatsWriteOptions[format]
		except KeyError:
			log.critical(f"No write support for {format!r} format")
			return
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
			if self._readers:
				log.warning(
					f"Writing to {format} format requires full sort"
					f", falling back to indirect mode"
				)
				self._inactivateDirectMode()
				log.info(f"Loaded {len(self._data)} entries")
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

		writer = None
		if format in self.writerClasses:
			writer = self.writerClasses[format].__call__(self)

		if sort:
			writerSortKey = getattr(writer, "sortKey", None)
			if sortKey is None:
				if not writerSortKey:
					log.critical(f"Plugin has not provided sortKey")
					return
				sortKey = writerSortKey
				log.debug(f"Using Writer.sortKey method from {format} plugin")
			elif sortOnWrite == ALWAYS:
				if writerSortKey:
					sortKey = writerSortKey
					log.warning(
						f"Ignoring user-defined sort order"
						f", and using key function from {format} plugin"
					)
			if sortKey is None:
				sortKey = Entry.defaultSortKey
			self.sortWords(
				key=sortKey,
				cacheSize=sortCacheSize
			)
		else:
			self._updateIter(sort=False)

		for reader in self._readers:
			log.info(
				f"Using Reader class from {reader.formatName} plugin"
				f" for direct conversion without loading into memory"
			)

		filename = abspath(filename)
		log.info(f"Writing to file {filename!r}")
		try:
			if writer is not None:
				writer.write(filename, **options)
			elif format in self.writeFunctions:
				self.writeFunctions[format].__call__(self, filename, **options)
			else:
				log.error(f"No write function or Writer class found for plugin {format}")
				return
		except Exception:
			log.exception("Exception while calling plugin\'s write function")
			return
		finally:
			self.clear()

		return filename

	def zipOutDir(self, filename: str):
		if isdir(filename):
			dirn, name = split(filename)
			with indir(filename):
				output, error = subprocess.Popen(
					["zip", "-r", f"../{name}.zip", ".", "-m"],
					stdout=subprocess.PIPE,
				).communicate()
				return error

		dirn, name = split(filename)
		with indir(dirn):
			output, error = subprocess.Popen(
				["zip", f"{filename}.zip", name, "-m"],
				stdout=subprocess.PIPE,
			).communicate()
			return error

	def compressOutDir(self, filename: str, compression: str) -> str:
		"""
		filename is the existing file path
		compression is the archive extension (without dot): "gz", "bz2", "zip"
		"""
		try:
			os.remove(f"{filename}.{compression}")
		except OSError:
			pass
		if compression == "gz":
			output, error = subprocess.Popen(
				["gzip", filename],
				stdout=subprocess.PIPE,
			).communicate()
			if error:
				log.error(
					error + "\n" +
					f"Failed to compress file \"{filename}\""
				)
		elif compression == "bz2":
			output, error = subprocess.Popen(
				["bzip2", filename],
				stdout=subprocess.PIPE,
			).communicate()
			if error:
				log.error(
					error + "\n" +
					f"Failed to compress file \"{filename}\""
				)
		elif compression == "zip":
			error = self.zipOutDir(filename)
			if error:
				log.error(
					error + "\n" +
					f"Failed to compress file \"{filename}\""
				)

		compressedFilename = f"{filename}.{compression}"
		if isfile(compressedFilename):
			return compressedFilename
		else:
			return filename

	def convert(
		self,
		inputFilename: str,
		inputFormat: str = "",
		direct: Optional[bool] = None,
		progressbar: bool = True,
		outputFilename: str = "",
		outputFormat: str = "",
		sort: Optional[bool] = None,
		sortKey: Optional[Callable[[bytes], Any]] = None,
		sortCacheSize: int = 1000,
		readOptions: Optional[Dict[str, Any]] = None,
		writeOptions: Optional[Dict[str, Any]] = None,
	) -> Optional[str]:
		"""
		returns absolute path of output file, or None if failed
		"""
		if not readOptions:
			readOptions = {}
		if not writeOptions:
			writeOptions = {}

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
			sortCacheSize=sortCacheSize,
			**writeOptions
		)
		log.info("")
		if not finalOutputFile:
			log.error(f"Writing file {outputFilename!r} failed.")
			return

		if compression:
			finalOutputFile = self.compressOutDir(finalOutputFile, compression)

		log.info(f"Writing file {finalOutputFile!r} done.")
		log.info(f"Running time of convert: {now()-tm0:.1f} seconds")

		return finalOutputFile

	# ________________________________________________________________________#

	def writeTxt(
		self,
		entryFmt: str = "",  # contain {word} and {defi}
		filename: str = "",
		writeInfo: bool = True,
		rplList: Optional[List[Tuple[str, str]]] = None,
		ext: str = ".txt",
		head: str = "",
		iterEntries: Optional[Iterator[BaseEntry]] = None,
		entryFilterFunc: Optional[Callable[[BaseEntry], Optional[BaseEntry]]] = None,
		outInfoKeysAliasDict: Optional[Dict[str, str]] = None,
		encoding: str = "utf-8",
		newline: str = "\n",
		resources: bool = True,
	) -> bool:
		if not entryFmt:
			raise ValueError("entryFmt argument is missing")
		if rplList is None:
			rplList = []
		if not filename:
			filename = self._filename + ext
		if not outInfoKeysAliasDict:
			outInfoKeysAliasDict = {}

		fp = open(filename, "w", encoding=encoding, newline=newline)
		fp.write(head)
		if writeInfo:
			for key, desc in self._info.items():
				try:
					key = outInfoKeysAliasDict[key]
				except KeyError:
					pass
				for rpl in rplList:
					desc = desc.replace(rpl[0], rpl[1])
				fp.write("##" + entryFmt.format(word=key, defi=desc))
		fp.flush()

		myResDir = f"{filename}_res"
		if not isdir(myResDir):
			os.mkdir(myResDir)

		if not iterEntries:
			iterEntries = self

		for entry in iterEntries:
			if entry.isData():
				if resources:
					entry.save(myResDir)
				continue

			if entryFilterFunc:
				entry = entryFilterFunc(entry)
				if not entry:
					continue
			word = entry.word
			defi = entry.defi
			if word.startswith("#"):  # FIXME
				continue
			# if self.getPref("enable_alts", True):  # FIXME

			for rpl in rplList:
				defi = defi.replace(rpl[0], rpl[1])
			fp.write(entryFmt.format(word=word, defi=defi))
		fp.close()
		if not os.listdir(myResDir):
			os.rmdir(myResDir)
		return True

	def writeTabfile(self, filename: str = "", **kwargs) -> None:
		self.writeTxt(
			entryFmt="{word}\t{defi}\n",
			filename=filename,
			rplList=(
				("\\", "\\\\"),
				("\r", ""),
				("\n", "\\n"),
				("\t", "\\t"),
			),
			ext=".txt",
			**kwargs
		)

	def writeDict(self, filename: str = "", writeInfo: bool = False) -> None:
		# Used in "/usr/share/dict/" for some dictionarys such as "ding"
		self.writeTxt(
			entryFmt="{word} :: {defi}\n",
			filename=filename,
			writeInfo=writeInfo,
			rplList=(
				("\n", "\\n"),
			),
			ext=".dict",
		)

	def	iterJsonLines(
		self,
		filename: str = "",
		infoKeys: Optional[List] = None,
		addExtraInfo: bool = True,
		newline: str = "\\n",
		transaction: bool = False,
	) -> Iterator[str]:
		newline = "<br>"

		yield (
			"{"
		)

		for i, entry in enumerate(self):
			if entry.isData():
				# FIXME
				continue
			word = entry.word.replace("\\", "\\\\").replace('"', '\\"').replace("\n","").replace("\r","")
			defi = entry.defi.replace("\\", "\\\\").replace('"', '\\"').replace("\n","").replace("\r","")
			yield f"\"{word}\":\"{defi}\","


		yield '"":""\n}'

	# ________________________________________________________________________#

	def iterSqlLines(
		self,
		filename: str = "",
		infoKeys: Optional[List] = None,
		addExtraInfo: bool = True,
		newline: str = "\\n",
		transaction: bool = False,
	) -> Iterator[str]:
		newline = "<br>"
		infoDefLine = "CREATE TABLE dbinfo ("
		infoValues = []

		if not infoKeys:
			infoKeys = [
				"dbname",
				"author",
				"version",
				"direction",
				"origLang",
				"destLang",
				"license",
				"category",
				"description",
			]

		for key in infoKeys:
			value = self.getInfo(key)
			value = value\
				.replace("\'", "\'\'")\
				.replace("\x00", "")\
				.replace("\r", "")\
				.replace("\n", newline)
			infoValues.append(f"\'{value}\'")
			infoDefLine += f"{key} char({len(value)}), "

		infoDefLine = infoDefLine[:-2] + ");"
		yield infoDefLine

		if addExtraInfo:
			yield (
				"CREATE TABLE dbinfo_extra (" +
				"\'id\' INTEGER PRIMARY KEY NOT NULL, " +
				"\'name\' TEXT UNIQUE, \'value\' TEXT);"
			)

		yield (
			"CREATE TABLE word (\'id\' INTEGER PRIMARY KEY NOT NULL, " +
			"\'w\' TEXT, \'m\' TEXT);"
		)

		if transaction:
			yield "BEGIN TRANSACTION;"
		yield f"INSERT INTO dbinfo VALUES({','.join(infoValues)});"

		if addExtraInfo:
			extraInfo = self.getExtraInfos(infoKeys)
			for index, (key, value) in enumerate(extraInfo.items()):
				key = key.replace("\'", "\'\'")
				value = value.replace("\'", "\'\'")
				yield (
					f"INSERT INTO dbinfo_extra VALUES({index+1}, "
					f"\'{key}\', \'{value}\');"
				)

		for i, entry in enumerate(self):
			if entry.isData():
				# FIXME
				continue
			word = entry.word
			defi = entry.defi
			word = word.replace("\'", "\'\'")\
				.replace("\r", "").replace("\n", newline)
			defi = defi.replace("\'", "\'\'")\
				.replace("\r", "").replace("\n", newline)
			yield f"INSERT INTO word VALUES({i+1}, \'{word}\', \'{defi}\');"
		if transaction:
			yield "END TRANSACTION;"
		yield "CREATE INDEX ix_word_w ON word(w COLLATE NOCASE);"

	# ________________________________________________________________________#

	def progressInit(self, *args) -> None:
		if self.ui:
			self.ui.progressInit(*args)

	def progress(self, pos: int, total: int, unit: str = "entries") -> None:
		if not self.ui:
			return
		self.ui.progress(
			min(pos + 1, total) / total,
			f"{pos:d} / {total:d} {unit}",
		)

	def progressEnd(self) -> None:
		if self.ui:
			self.ui.progressEnd()

	# ________________________________________________________________________#

	@classmethod
	def init(cls):
		cls.readFormats = []
		cls.writeFormats = []
		cls.readExt = []
		cls.writeExt = []
		cls.readDesc = []
		cls.writeDesc = []
		cls.loadPlugins(join(dirname(__file__), "plugins"))
		cls.loadPlugins(userPluginsDir)


Glossary.init()
