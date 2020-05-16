# -*- coding: utf-8 -*-
# glossary.py
#
# Copyright © 2008-2016 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
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
from collections import Counter
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
from .core import VERSION, userPluginsDir
from .entry_base import BaseEntry
from .entry import Entry, DataEntry
from .sort_stream import hsortStreamList

from .text_utils import (
	fixUtf8,
)
from .os_utils import indir

from .glossary_type import GlossaryType

homePage = "https://github.com/ilius/pyglossary"
log = logging.getLogger("root")

file = io.BufferedReader

try:
	ModuleNotFoundError
except NameError:
	ModuleNotFoundError = ImportError


def get_ext(path: str) -> str:
	return splitext(path)[1].lower()


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
	}
	plugins = {}  # format => pluginModule
	readFunctions = {}
	readerClasses = {}
	writeFunctions = {}
	writerClasses = {}
	formatsDesc = {}
	formatsExt = {}
	formatsReadOptions = {}
	formatsWriteOptions = {}
	formatsOptionsProp = {}
	formatsDepends = {}
	descFormat = {}
	descExt = {}
	extFormat = {}

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
		optionsProp = cls.formatsOptionsProp[format]
		sig = inspect.signature(func)
		optNames = []
		for name, param in sig.parameters.items():
			if param.default is inspect._empty:
				if name not in ("self", "glos", "filename", "dirname", "kwargs"):
					log.warning(f"empty default value for {name}: {param.default}")
				continue # non-keyword argument
			if name not in optionsProp:
				log.warning(f"skipping option {name} in plugin {format}")
				continue
			prop = optionsProp[name]
			if prop.disabled:
				log.debug(f"skipping disabled option {name} in {format} plugin")
				continue
			if not prop.validate(param.default):
				log.warning(f"invalid default value for option: {name} = {param.default!r}")
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
		# FIXME: deprecate non-tuple values in plugin.extensions
		if isinstance(extensions, str):
			extensions = (extensions,)
		elif not isinstance(extensions, tuple):
			extensions = tuple(extensions)

		if hasattr(plugin, "description"):
			desc = plugin.description
		else:
			desc = f"{format} ({extensions[0]})"

		cls.plugins[format] = plugin
		cls.descFormat[desc] = format
		cls.descExt[desc] = extensions[0]
		for ext in extensions:
			cls.extFormat[ext] = format
		cls.formatsExt[format] = extensions
		cls.formatsDesc[format] = desc
		cls.formatsOptionsProp[format] = getattr(
			plugin,
			"optionsProp",
			{},
		)
		cls.formatsDepends[format] = getattr(
			plugin,
			"depends",
			{},
		)

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
				cls.formatsReadOptions[format] = cls.getRWOptionsFromFunc(
					Reader.open,
					format,
				)

		# ignore "read" function if "Reader" class is present
		if not hasReadSupport:
			try:
				cls.readFunctions[format] = plugin.read
			except AttributeError:
				pass
			else:
				hasReadSupport = True
				cls.formatsReadOptions[format] = cls.getRWOptionsFromFunc(
					plugin.read,
					format,
				)

		if hasReadSupport:
			cls.readFormats.append(format)
			cls.readExt.append(extensions)
			cls.readDesc.append(desc)

		hasWriteSupport = False
		if hasattr(plugin, "Writer"):
			cls.writerClasses[format] = plugin.Writer
			cls.formatsWriteOptions[format] = cls.getRWOptionsFromFunc(
				plugin.Writer.write,
				format,
			)
			hasWriteSupport = True

		if not hasWriteSupport and hasattr(plugin, "write"):
			cls.writeFunctions[format] = plugin.write
			cls.formatsWriteOptions[format] = cls.getRWOptionsFromFunc(
				plugin.write,
				format,
			)
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
			for key in Glossary.formatsExt.keys():
				if ext in Glossary.formatsExt[key]:
					format = key

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
		self._sortKey = None
		self._sortCacheSize = 1000

		self._filename = ""
		self._defaultDefiFormat = "m"
		self._progressbar = True

	def __init__(self, info: Optional[Dict[str, str]] = None, ui=Any) -> None:
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

	def __str__(self) -> str:
		return "glossary.Glossary"

	def addEntryObj(self, entry: Entry) -> None:
		self._data.append(entry.getRaw())

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
			if index & 0x7f == 0: # 0x3f, 0x7f, 0xff
				gc.collect()
			yield Entry.fromRaw(
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
					print(entry.getWord())
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

	def getMostUsedDefiFormats(self, count: int = None) -> List[Tuple[str, int]]:
		return Counter([
			entry.getDefiFormat()
			for entry in self
		]).most_common(count)

	# def formatInfoKeys(self, format: str):# FIXME

	def iterInfo(self) -> Iterator[Tuple[str, str]]:
		return self._info.items()

	def getInfo(self, key: str) -> str:
		key = str(key) # FIXME: required?

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

	def getPref(self, name: str, default: Optional[str]) -> Optional[str]:
		if self.ui:
			return self.ui.pref.get(name, default)
		else:
			return default

	def newDataEntry(self, fname: str, data: bytes) -> DataEntry:
		inTmp = not self._readers
		return DataEntry(fname, data, inTmp)

	# ________________________________________________________________________#

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

		# don't allow direct=False when there are readers
		# (read is called before with direct=True)
		if self._readers and not direct:
			raise ValueError(
				f"there are already {len(self._readers)} readers"
				f", you can not read with direct=False mode"
			)

		self.updateEntryFilters()
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
		if not ext.lower() in self.formatsExt[format]:
			filenameNoExt = filename

		self._filename = filenameNoExt
		if not self.getInfo("name"):
			self.setInfo("name", split(filename)[1])
		self._progressbar = progressbar

		if format in self.readerClasses:
			Reader = self.readerClasses[format]
			reader = Reader(self)
			reader.open(filename, **options)
			if direct:
				self._readers.append(reader)
				log.info(
					f"Using Reader class from {format} plugin"
					f" for direct conversion without loading into memory"
				)
			else:
				self.loadReader(reader)
		else:
			if direct:
				log.debug(
					f"No `Reader` class found in {format} plugin"
					f", falling back to indirect mode"
				)
			result = self.readFunctions[format].__call__(
				self,
				filename,
				**options
			)
			# if not result:## FIXME
			#	return False

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
				if index & 0x7f == 0: # 0x3f, 0x7f, 0xff
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
		key: Optional[Callable[[str], Any]] = None,
		cacheSize: int = 0,
	) -> None:
		# only sort by main word, or list of words + alternates? FIXME
		if self._readers:
			self._sortKey = key
			if cacheSize > 0:
				self._sortCacheSize = cacheSize  # FIXME
		else:
			self._data.sort(
				key=Entry.getRawEntrySortKey(key),
			)
		self._updateIter(sort=True)

	@classmethod
	def detectOutputFormat(
		cls,
		filename: str = "",
		format: str = "",
		inputFilename: str = "",
	) -> Optional[Tuple[str, str, str]]:
		"""
		returns (filename, format, archiveType) or None
		"""
		archiveType = ""
		if filename:
			ext = ""
			filenameNoExt, fext = splitext(filename)
			fext = fext.lower()
			if fext in (".gz", ".bz2", ".zip"):
				archiveType = fext[1:]
				filename = filenameNoExt
				fext = get_ext(filename)
			if not format:
				for fmt, extList in Glossary.formatsExt.items():
					for e in extList:
						if format == e[1:] or format == e:
							format = fmt
							ext = e
							break
					if format:
						break
				if not format:
					for fmt, extList in Glossary.formatsExt.items():
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
					for fmt, extList in Glossary.formatsExt.items():
						if fext in extList:
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
				filename += Glossary.formatsExt[format][0]
			except KeyError:
				log.error("Invalid write format")
				return

		return filename, format, archiveType

	def write(
		self,
		filename: str,
		format: str,
		sort: Optional[bool] = None,
		sortKey: Optional[Callable[[str], Any]] = None,
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

		if sort:
			if sortKey is None:
				try:
					sortKey = plugin.sortKey
				except AttributeError:
					pass
				else:
					log.debug(
						"Using sort key function from %s plugin" % format
					)
			elif sortOnWrite == ALWAYS:
				try:
					sortKey = plugin.sortKey
				except AttributeError:
					pass
				else:
					log.warning(
						"Ignoring user-defined sort order, " +
						"and using key function from %s plugin" % format
					)
			self.sortWords(
				key=sortKey,
				cacheSize=sortCacheSize
			)
		else:
			self._updateIter(sort=False)

		filename = abspath(filename)
		log.info(f"Writing to file {filename!r}")
		try:
			if format in self.writerClasses:
				writer = self.writerClasses[format].__call__(self)
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

	def archiveOutDir(self, filename: str, archiveType: str) -> str:
		"""
		filename is the existing file path
		archiveType is the archive extension (without dot): "gz", "bz2", "zip"
		"""
		try:
			os.remove("%s.%s" % (filename, archiveType))
		except OSError:
			pass
		if archiveType == "gz":
			output, error = subprocess.Popen(
				["gzip", filename],
				stdout=subprocess.PIPE,
			).communicate()
			if error:
				log.error(
					error + "\n" +
					"Failed to compress file \"%s\"" % filename
				)
		elif archiveType == "bz2":
			output, error = subprocess.Popen(
				["bzip2", filename],
				stdout=subprocess.PIPE,
			).communicate()
			if error:
				log.error(
					error + "\n" +
					"Failed to compress file \"%s\"" % filename
				)
		elif archiveType == "zip":
			error = self.zipOutDir(filename)
			if error:
				log.error(
					error + "\n" +
					"Failed to compress file \"%s\"" % filename
				)

		archiveFilename = "%s.%s" % (filename, archiveType)
		if isfile(archiveFilename):
			return archiveFilename
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
		sortKey: Optional[Callable[[str], Any]] = None,
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
		outputFilename, outputFormat, archiveType = outputArgs

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

		if archiveType:
			finalOutputFile = self.archiveOutDir(finalOutputFile, archiveType)

		log.info(f"Writing file {finalOutputFile!r} done.")
		log.info(f"Running time of convert: {now()-tm0:.1f} seconds")

		return finalOutputFile

	# ________________________________________________________________________#

	def writeTxt(
		self,
		sep1: str,
		sep2: str,
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
				fp.write("##" + key + sep1 + desc + sep2)
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
			word = entry.getWord()
			defi = entry.getDefi()
			if word.startswith("#"):  # FIXME
				continue
			# if self.getPref("enable_alts", True):  # FIXME

			for rpl in rplList:
				defi = defi.replace(rpl[0], rpl[1])
			fp.write(word + sep1 + defi + sep2)
		fp.close()
		if not os.listdir(myResDir):
			os.rmdir(myResDir)
		return True

	def writeTabfile(self, filename: str = "", **kwargs) -> None:
		self.writeTxt(
			"\t",
			"\n",
			filename=filename,
			rplList=(
				("\\", "\\\\"),
				("\n", "\\n"),
				("\t", "\\t"),
			),
			ext=".txt",
			**kwargs
		)

	def writeDict(self, filename: str = "", writeInfo: bool = False) -> None:
		# Used in "/usr/share/dict/" for some dictionarys such as "ding"
		self.writeTxt(
			" :: ",
			"\n",
			filename,
			writeInfo,
			(
				("\n", "\\n"),
			),
			".dict",
		)

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
			word = entry.getWord()
			defi = entry.getDefi()
			word = word.replace("\'", "\'\'")\
				.replace("\r", "").replace("\n", newline)
			defi = defi.replace("\'", "\'\'")\
				.replace("\r", "").replace("\n", newline)
			yield f"INSERT INTO word VALUES({i+1}, \'{word}\', \'{defi}\');"
		if transaction:
			yield "END TRANSACTION;"
		yield "CREATE INDEX ix_word_w ON word(w COLLATE NOCASE);"

	# ________________________________________________________________________#

	def takeOutputWords(self, minWordLen: int = 3) -> List[str]:
		# fr"[\w]{{{minWordLen},}}"
		wordPattern = re.compile(r"[\w]{%d,}" % minWordLen, re.U)
		words = set()
		progressbar, self._progressbar = self._progressbar, False
		for entry in self:
			words.update(re.findall(
				wordPattern,
				entry.getDefi(),
			))
		self._progressbar = progressbar
		return sorted(words)

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

	def searchWordInDef(
		self,
		st: str,
		matchWord: bool = True,
		sepChars: str = ".,،",
		maxNum: int = 100,
		minRel: float = 0.0,
		minWordLen: int = 3,
		includeDefs: bool = False,
		showRel: str = "Percent", # "Percent" | "Percent At First" | ""
	) -> List[str]:
		# searches word "st" in definitions of the glossary
		splitPattern = re.compile(
			"|".join([re.escape(x) for x in sepChars]),
			re.U,
		)
		wordPattern = re.compile(r"[\w]{%d,}" % minWordLen, re.U)
		outRel = []
		for item in self._data:
			words, defi = item[:2]
			if isinstance(words, str):
				words = [words]
			if isinstance(defi, list):
				defi = "\n".join(defi)
			if st not in defi:
				continue
			for word in words:
				rel = 0  # relation value of word (0 <= rel <= 1)
				for part in re.split(splitPattern, defi):
					if not part:
						continue
					if matchWord:
						partWords = re.findall(
							wordPattern,
							part,
						)
						if not partWords:
							continue
						rel = max(
							rel,
							partWords.count(st) / len(partWords)
						)
					else:
						rel = max(
							rel,
							part.count(st) * len(st) / len(part)
						)
				if rel <= minRel:
					continue
				if includeDefs:
					outRel.append((word, rel, defi))
				else:
					outRel.append((word, rel))
		outRel.sort(
			key=lambda x: x[1],
			reverse=True,
		)
		n = len(outRel)
		if n > maxNum > 0:
			outRel = outRel[:maxNum]
			n = maxNum
		num = 0
		out = []
		if includeDefs:
			for j in range(n):
				numP = num
				w, num, m = outRel[j]
				m = m.replace("\n", "\\n").replace("\t", "\\t")
				onePer = int(1.0 / num)
				if onePer == 1.0:
					out.append(f"{w}\\n{m}")
				elif showRel == "Percent":
					out.append(f"{w}(%{100*num})\\n{m}")
				elif showRel == "Percent At First":
					if num == numP:
						out.append(f"{w}\\n{m}")
					else:
						out.append(f"{w}(%{100*num})\\n{m}")
				else:
					out.append(f"{w}\\n{m}")
			return out
		for j in range(n):
			numP = num
			w, num = outRel[j]
			onePer = int(1.0 / num)
			if onePer == 1.0:
				out.append(w)
			elif showRel == "Percent":
				out.append(f"{w}(%{100*num})")
			elif showRel == "Percent At First":
				if num == numP:
					out.append(w)
				else:
					out.append(f"{w}(%{100*num})")
			else:
				out.append(w)
		return out

	def reverse(
		self,
		savePath: str = "",
		words: Optional[List[str]] = None,
		includeDefs: bool = False,
		reportStep: int = 300,
		saveStep: int = 1000,  # set this to zero to disable auto saving
		**kwargs
	) -> Iterator[int]:
		"""
		This is a generator
		Usage:
			for wordIndex in glos.reverse(...):
				pass

		Inside the `for` loop, you can pause by waiting (for input or a flag)
			or stop by breaking

		Potential keyword arguments:
			words = None ## None, or list
			reportStep = 300
			saveStep = 1000
			savePath = ""
			matchWord = True
			sepChars = ".,،"
			maxNum = 100
			minRel = 0.0
			minWordLen = 3
			includeDefs = False
			showRel = "None"
				allowed values: "None", "Percent", "Percent At First"
		"""
		if not savePath:
			savePath = self.getInfo("name") + ".txt"

		if saveStep < 2:
			raise ValueError("saveStep must be more than 1")

		ui = self.ui

		if words:
			words = list(words)
		else:
			words = self.takeOutputWords()

		wordCount = len(words)
		log.info(
			f"Reversing to file {savePath!r}"
			f", number of words: {wordCount}"
		)
		self.progressInit("Reversing")
		wcThreshold = wordCount // 200 + 1
		with open(savePath, "w") as saveFile:
			for wordI in range(wordCount):
				word = words[wordI]
				if wordI % wcThreshold == 0:
					self.progress(wordI, wordCount)

				if wordI % saveStep == 0 and wordI > 0:
					saveFile.flush()
				result = self.searchWordInDef(
					word,
					includeDefs=includeDefs,
					**kwargs
				)
				if result:
					try:
						if includeDefs:
							defi = "\\n\\n".join(result)
						else:
							defi = ", ".join(result) + "."
					except Exception:
						log.exception("")
						log.debug(f"result = {result}")
						return
					saveFile.write(f"{word}\t{defi}\n")
				yield wordI

		self.progressEnd()
		yield wordCount

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
