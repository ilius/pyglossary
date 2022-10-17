# -*- coding: utf-8 -*-
# glossary.py
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

import logging
import os
import os.path
from collections import OrderedDict as odict
from contextlib import suppress
from os.path import (
	isdir,
	isfile,
	join,
	relpath,
)
from time import time as now
from typing import (
	Any,
	Dict,
	Iterator,
	List,
	Optional,
	Tuple,
	Type,
	TypeVar,
)

from . import core
from .core import (
	cacheDir,
	dataDir,
	pluginsDir,
	userPluginsDir,
)
from .entry import DataEntry, Entry
from .entry_filters import (
	EntryFilter,
	FixUnicode,
	LanguageCleanup,
	LowerWord,
	NonEmptyDefiFilter,
	NonEmptyWordFilter,
	NormalizeHtml,
	PreventDuplicateWords,
	RemoveEmptyAndDuplicateAltWords,
	RemoveHtmlTags,
	RemoveHtmlTagsAll,
	RTLDefi,
	ShowMaxMemoryUsage,
	ShowProgressBar,
	SkipDataEntry,
	SkipEntriesWithDuplicateHeadword,
	TrimArabicDiacritics,
	# TextListSymbolCleanup,
	TrimWhitespaces,
)
from .flags import (
	ALWAYS,
	DEFAULT_NO,
	DEFAULT_YES,
	NEVER,
)
from .glossary_info import GlossaryInfo
from .glossary_type import EntryType, GlossaryType
from .glossary_utils import (
	EntryList,
	splitFilenameExt,
)
from .info import c_name
from .os_utils import rmtree, showMemoryUsage
from .plugin_manager import PluginManager
from .sort_keys import namedSortKeyByName

log = logging.getLogger("pyglossary")


"""
sortKeyType = Callable[
	[[List[str]],
	Any,
]
"""

defaultSortKeyName = "headword_lower"

EntryFilterType = TypeVar("EntryFilter", bound=EntryFilter)


class Glossary(GlossaryInfo, PluginManager, GlossaryType):
	"""
	Direct access to glos.data is dropped
	Use `glos.addEntryObj(glos.newEntry(word, defi, [defiFormat]))`
		where both word and defi can be list (including alternates) or string
	See help(glos.addEntryObj)

	Use `for entry in glos:` to iterate over entries (glossary data)
	See help(pyglossary.entry.Entry) for details

	"""

	entryFiltersRules = [
		(None, TrimWhitespaces),
		(None, NonEmptyWordFilter),
		(("skip_resources", False), SkipDataEntry),
		(("utf8_check", False), FixUnicode),
		(("lower", False), LowerWord),
		(("skip_duplicate_headword", False), SkipEntriesWithDuplicateHeadword),
		(("trim_arabic_diacritics", False), TrimArabicDiacritics),
		(("rtl", False), RTLDefi),
		(("remove_html_all", False), RemoveHtmlTagsAll),
		(("remove_html", ""), RemoveHtmlTags),
		(("normalize_html", False), NormalizeHtml),
		(None, LanguageCleanup),

		# TODO
		# (("text_list_symbol_cleanup", False), TextListSymbolCleanup),

		(None, NonEmptyWordFilter),
		(None, NonEmptyDefiFilter),
		(None, RemoveEmptyAndDuplicateAltWords),
	]
	# other entry filters that are added conditionally (other than with config):
	#   - ShowProgressBar
	#   - ShowMaxMemoryUsage

	def _closeReaders(self) -> None:
		for reader in self._readers:
			try:
				reader.close()
			except Exception:
				log.exception("")

	def clear(self) -> None:
		self._info = odict()

		self._data.clear()

		readers = getattr(self, "_readers", [])
		for reader in readers:
			try:
				reader.close()
			except Exception:
				log.exception("")
		self._readers = []
		self._readersOpenArgs = {}
		self._defiHasWordTitle = False

		self._iter = None
		self._entryFilters = []
		self._entryFiltersName = set()
		self._sort = False

		self._filename = ""
		self._defaultDefiFormat = "m"
		self._progressbar = True
		self._tmpDataDir = ""

	def __init__(
		self,
		info: "Optional[Dict[str, str]]" = None,
		ui: "Optional[UIBase]" = None,  # noqa: F821
	) -> None:
		"""
		info:	OrderedDict or dict instance, or None
				no need to copy OrderedDict instance before passing here
				we will not reference to it
		"""
		GlossaryInfo.__init__(self)
		self._config = {}
		self._data = EntryList(self)  # type: List[RawEntryType]
		self._sqlite = False
		self._rawEntryCompress = False
		self._cleanupPathList = set()
		self.clear()
		if info:
			if not isinstance(info, (dict, odict)):
				raise TypeError(
					"Glossary: `info` has invalid type"
					", dict or OrderedDict expected",
				)
			for key, value in info.items():
				self.setInfo(key, value)

		self._ui = ui

	def cleanup(self) -> None:
		if not self._cleanupPathList:
			return
		if not self._config.get("cleanup", True):
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
				rmtree(cleanupPath)
			else:
				log.error(f"no such file or directory: {cleanupPath}")
		self._cleanupPathList = set()

	@property
	def rawEntryCompress(self) -> bool:
		return self._rawEntryCompress

	def setRawEntryCompress(self, enable: bool) -> bool:
		self._rawEntryCompress = enable

	def updateEntryFilters(self) -> None:
		entryFilters = []
		config = self._config

		for configRule, filterClass in self.entryFiltersRules:
			args = ()
			if configRule is not None:
				param, default = configRule
				value = config.get(param, default)
				if not value:
					continue
				if not isinstance(default, bool):
					args = (value,)
			entryFilters.append(filterClass(self, *args))

		if self._ui and self._progressbar:
			entryFilters.append(ShowProgressBar(self))

		if log.level <= core.TRACE:
			try:
				import psutil  # noqa: F401
			except ModuleNotFoundError:
				pass
			else:
				entryFilters.append(ShowMaxMemoryUsage(self))

		self._entryFilters = entryFilters

		self._entryFiltersName = {
			entryFilter.name
			for entryFilter in entryFilters
		}

	def prepareEntryFilters(self) -> None:
		"""
			call .prepare() method on all _entryFilters
			run this after glossary info is set and ready
			for most entry filters, it won't do anything
		"""
		for entryFilter in self._entryFilters:
			entryFilter.prepare()

	def _addExtraEntryFilter(self, cls: "Type[EntryFilterType]") -> None:
		if cls.name in self._entryFiltersName:
			return
		self._entryFilters.append(cls(self))
		self._entryFiltersName.add(cls.name)

	def removeHtmlTagsAll(self) -> None:
		"""
		Remove all HTML tags from definition

		This should only be called from a plugin's Writer.__init__ method.
		Does not apply on entries added with glos.addEntryObj
		"""
		self._addExtraEntryFilter(RemoveHtmlTagsAll)

	def preventDuplicateWords(self) -> None:
		"""
		Adds entry filter to prevent duplicate `entry.s_word`

		This should only be called from a plugin's Writer.__init__ method.
		Does not apply on entries added with glos.addEntryObj

		Note: there may be still duplicate headwords or alternate words
			but we only care about making the whole `entry.s_word`
			(aka entry key) unique
		"""
		self._addExtraEntryFilter(PreventDuplicateWords)

	def __str__(self) -> str:
		return (
			"Glossary{"
			f"filename: {self._filename!r}"
			f", name: {self._info.get('name')!r}"
			"}"
		)

	def _loadedEntryGen(self) -> "Iterator[EntryType]":
		if not (self._ui and self._progressbar):
			yield from self._data
			return

		pbFilter = ShowProgressBar(self)
		self.progressInit("Writing")
		for entry in self._data:
			pbFilter.run(entry)
			yield entry
		self.progressEnd()

	def _readersEntryGen(self) -> "Iterator[EntryType]":
		for reader in self._readers:
			self.progressInit("Converting")
			try:
				yield from self._applyEntryFiltersGen(reader)
			finally:
				reader.close()
			self.progressEnd()

	# This iterator/generator does not give None entries.
	# And Entry is not falsable, so bool(entry) is always True.
	# Since ProgressBar is already handled with an EntryFilter, there is
	# no point of returning None entries anymore.
	def _applyEntryFiltersGen(
		self,
		gen: "Iterator[EntryType]",
	) -> "Iterator[EntryType]":
		for entry in gen:
			if entry is None:
				continue
			for entryFilter in self._entryFilters:
				entry = entryFilter.run(entry)
				if entry is None:
					break
			else:
				yield entry

	def __iter__(self) -> "Iterator[EntryType]":
		if self._iter is None:
			log.error(
				"Trying to iterate over a blank Glossary"
				", must call `glos.read` first",
			)
			return iter([])
		return self._iter

	# TODO: switch to @property defaultDefiFormat
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

	@property
	def config(self):
		raise NotImplementedError

	@config.setter
	def config(self, config: "Dict[str, Any]") -> None:
		if self._config:
			log.error("glos.config is set more than once")
			return
		self._config = config
		if "optimize_memory" in config:
			self._rawEntryCompress = config["optimize_memory"]

	@property
	def alts(self) -> bool:
		return self._config.get("enable_alts", True)

	@property
	def filename(self) -> str:
		return self._filename

	@property
	def tmpDataDir(self) -> str:
		if not self._tmpDataDir:
			self._setTmpDataDir(self._filename)
		return self._tmpDataDir

	def wordTitleStr(
		self,
		word: str,
		sample: str = "",
		_class: str = "",
	) -> str:
		"""
		notes:
			- `word` needs to be escaped before passing
			- `word` can contain html code (multiple words, colors, etc)
			- if input format (reader) indicates that words are already included
				in definition (as title), this method will return empty string
			- depending on glossary's `sourceLang` or writing system of `word`,
				(or sample if given) either '<b>' or '<big>' will be used
		"""
		if self._defiHasWordTitle:
			return ""
		if not word:
			return ""
		if not sample:
			sample = word
		tag = self._getTitleTag(sample)
		if _class:
			return f'<{tag} class="{_class}">{word}</{tag}><br>'
		return f'<{tag}>{word}</{tag}><br>'

	def getConfig(self, name: str, default: "Optional[str]") -> "Optional[str]":
		return self._config.get(name, default)

	def addEntryObj(self, entry: "EntryType") -> None:
		self._data.append(entry)

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
		import uuid

		if self._readers:
			return DataEntry(fname, data)

		if self._tmpDataDir:
			return DataEntry(
				fname,
				data,
				tmpPath=join(self._tmpDataDir, fname.replace("/", "_")),
			)

		tmpDir = join(cacheDir, "tmp")
		os.makedirs(tmpDir, mode=0o700, exist_ok=True)
		self._cleanupPathList.add(tmpDir)
		return DataEntry(
			fname,
			data,
			tmpPath=join(tmpDir, uuid.uuid1().hex),
		)

	# ________________________________________________________________________#

	# def _hasWriteAccessToDir(self, dirPath: str) -> None:
	# 	if isdir(dirPath):
	# 		return os.access(dirPath, os.W_OK)
	# 	return os.access(os.path.dirname(dirPath), os.W_OK)

	def _createReader(self, format: str, options: "Dict[str, Any]") -> "Any":
		reader = self.plugins[format].readerClass(self)
		for name, value in options.items():
			setattr(reader, f"_{name}", value)
		return reader

	def _setTmpDataDir(self, filename: str):
		import uuid
		# good thing about cacheDir is that we don't have to clean it up after
		# conversion is finished.
		# specially since dataEntry.save(...) will move the file from cacheDir
		# to the new directory (associated with output glossary path)
		# And we don't have to check for write access to cacheDir because it's
		# inside user's home dir. But input glossary might be in a directory
		# that we don't have write access to.
		# still maybe add a config key to decide if we should always use cacheDir
		# if self._hasWriteAccessToDir(f"{filename}_res", os.W_OK):
		# 	self._tmpDataDir = f"{filename}_res"
		# else:
		if not filename:
			filename = uuid.uuid1().hex
		self._tmpDataDir = join(cacheDir, os.path.basename(filename) + "_res")
		log.debug(f"tmpDataDir = {self._tmpDataDir}")
		os.makedirs(self._tmpDataDir, mode=0o700, exist_ok=True)
		self._cleanupPathList.add(self._tmpDataDir)

	def read(
		self,
		filename: str,
		format: str = "",
		direct: bool = False,
		**kwargs,
	) -> bool:
		"""
		filename (str):	name/path of input file
		format (str):	name of input format,
						or "" to detect from file extension
		direct (bool):	enable direct mode
		progressbar (bool): enable progressbar

		read-options can be passed as additional keyword arguments
		"""
		if type(filename) is not str:
			raise TypeError("filename must be str")
		if format is not None and type(format) is not str:
			raise TypeError("format must be str")

		# don't allow direct=False when there are readers
		# (read is called before with direct=True)
		if self._readers and not direct:
			raise ValueError(
				f"there are already {len(self._readers)} readers"
				f", you can not read with direct=False mode",
			)

		return self._read(
			filename=filename,
			format=format,
			direct=direct,
			**kwargs,
		)

	def _read(
		self,
		filename: str,
		format: str = "",
		direct: bool = False,
		progressbar: bool = True,
		**options,
	) -> bool:
		filename = os.path.abspath(filename)

		self._setTmpDataDir(filename)

		###
		inputArgs = self.detectInputFormat(filename, format=format)
		if inputArgs is None:
			return False
		origFilename = filename
		filename, format, compression = inputArgs

		if compression:
			from pyglossary.compression import uncompress
			uncompress(origFilename, filename, compression)

		validOptionKeys = list(self.formatsReadOptions[format].keys())
		for key in list(options.keys()):
			if key not in validOptionKeys:
				log.error(
					f"Invalid read option {key!r} "
					f"given for {format} format",
				)
				del options[key]

		filenameNoExt, ext = os.path.splitext(filename)
		if ext.lower() not in self.plugins[format].extensions:
			filenameNoExt = filename

		self._filename = filenameNoExt
		if not self._info.get(c_name):
			self._info[c_name] = os.path.split(filename)[1]
		self._progressbar = progressbar

		self.updateEntryFilters()

		reader = self._createReader(format, options)
		try:
			reader.open(filename)
		except (FileNotFoundError, LookupError) as e:
			log.critical(str(e))
			return False
		except Exception:
			log.exception("")
			return False
		self._readersOpenArgs[reader] = (filename, options)
		self.prepareEntryFilters()

		hasTitleStr = self._info.get("definition_has_headwords", "")
		if hasTitleStr:
			if hasTitleStr.lower() == "true":
				self._defiHasWordTitle = True
			else:
				log.error(f"bad info value: definition_has_headwords={hasTitleStr!r}")

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
		showMemoryUsage()

		self.progressInit("Reading")
		try:
			for entry in self._applyEntryFiltersGen(reader):
				self.addEntryObj(entry)
		finally:
			reader.close()

		self.progressEnd()

		log.trace(f"Loaded {len(self._data)} entries")
		showMemoryUsage()

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
			1- Whether or not direct mode is On (self._readers not empty)
				or Off (self._readers empty)
		"""
		if not self._readers:  # indirect mode
			self._iter = self._loadedEntryGen()
			return

		# direct mode
		self._iter = self._readersEntryGen()

	def updateIter(self) -> None:
		if self._readers:
			raise RuntimeError("can not call this while having a reader")
		self._updateIter()

	def sortWords(
		self,
		sortKeyName: "str" = "headword_lower",
		sortEncoding: "str" = "utf-8",
		sortLocale: "Optional[str]" = None,
		writeOptions: "Optional[Dict[str, Any]]" = None,
	) -> None:
		"""
			sortKeyName: see doc/sort-key.md
		"""
		if self._readers:
			raise NotImplementedError(
				"can not use sortWords in direct mode",
			)

		if self._sqlite:
			raise NotImplementedError(
				"can not use sortWords in SQLite mode",
			)

		namedSortKey = namedSortKeyByName.get(sortKeyName)
		if namedSortKey is None:
			log.critical(f"invalid {sortKeyName = }")
			return

		if not sortEncoding:
			sortEncoding = "utf-8"
		if writeOptions is None:
			writeOptions = {}

		t0 = now()
		self._data.setSortKey(
			namedSortKey=namedSortKey,
			sortEncoding=sortEncoding,
			sortLocale=sortLocale,
			sortScript=None,
			writeOptions=writeOptions,
		)
		self._data.sort()
		log.info(f"Sorting took {now() - t0:.1f} seconds")

		self._sort = True
		self._updateIter()

	def _createWriter(
		self,
		format: str,
		options: "Dict[str, Any]",
	) -> "Any":
		validOptions = self.formatsWriteOptions.get(format)
		if validOptions is None:
			log.critical(f"No write support for {format!r} format")
			return None
		validOptionKeys = list(validOptions.keys())
		for key in list(options.keys()):
			if key not in validOptionKeys:
				log.error(
					f"Invalid write option {key!r}"
					f" given for {format} format",
				)
				del options[key]

		writer = self.plugins[format].writerClass(self)
		for name, value in options.items():
			setattr(writer, f"_{name}", value)
		return writer

	def write(
		self,
		filename: str,
		format: str,
		**kwargs,
	) -> "Optional[str]":
		"""
		filename (str): file name or path to write

		format (str): format name

		sort (bool):
			True (enable sorting),
			False (disable sorting),
			None (auto, get from UI)

		sortKeyName (str or None):
			key function name for sorting

		sortEncoding (str or None):
			encoding for sorting, default utf-8

		sortLocale: (str or None):
			locale name for sorting (conflicts with sortEncoding)

		You can pass write-options (of given format) as keyword arguments

		returns absolute path of output file, or None if failed
		"""
		if type(filename) is not str:
			raise TypeError("filename must be str")
		if format is not None and type(format) is not str:
			raise TypeError("format must be str")

		return self._write(
			filename=filename,
			format=format,
			**kwargs,
		)

	def _write(
		self,
		filename: str,
		format: str,
		sort: "Optional[bool]" = None,
		**options,
	) -> "Optional[str]":
		filename = os.path.abspath(filename)

		if format not in self.plugins or not self.plugins[format].canWrite:
			log.critical(f"No Writer class found for plugin {format}")
			return None

		if self._readers and sort:
			log.warning(
				"Full sort enabled, falling back to indirect mode",
			)
			self._inactivateDirectMode()

		log.info(f"Writing to {format} file {filename!r}")

		writer = self._createWriter(format, options)

		self._sort = sort

		if sort:
			t0 = now()
			self._data.sort()
			log.info(f"Sorting took {now() - t0:.1f} seconds")

		self._updateIter()
		try:
			writer.open(filename)
		except (FileNotFoundError, LookupError) as e:
			log.critical(str(e))
			return None
		except Exception:
			log.exception("")
			return None

		showMemoryUsage()

		writerList = [writer]
		try:
			genList = []
			gen = writer.write()
			if gen is None:
				log.error(f"{format} write function is not a generator")
			else:
				genList.append(gen)

			if self._config.get("save_info_json", False):
				infoWriter = self._createWriter("Info", {})
				filenameNoExt, _, _, _ = splitFilenameExt(filename)
				infoWriter.open(f"{filenameNoExt}.info")
				genList.append(infoWriter.write())
				writerList.append(infoWriter)

			for gen in genList:
				gen.send(None)
			for entry in self:
				for gen in genList:
					gen.send(entry)
			# suppress() on the whole for-loop does not work
			for gen in genList:
				with suppress(StopIteration):
					gen.send(None)
		except (FileNotFoundError, LookupError) as e:
			log.critical(str(e))
			return None
		except Exception:
			log.exception("Exception while calling plugin\'s write function")
			return None
		finally:
			showMemoryUsage()
			log.debug("Running writer.finish()")
			for writer in writerList:
				writer.finish()
			self.clear()

		showMemoryUsage()

		return filename

	def _compressOutput(self, filename: str, compression: str) -> str:
		from pyglossary.compression import compress
		return compress(self, filename, compression)

	def _switchToSQLite(
		self,
		inputFilename: str,
		outputFormat: str,
	) -> bool:
		from pyglossary.sq_entry_list import SqEntryList

		# sq_hash = hash((inputFilename, outputFormat))
		# we don't have outputFilename
		# should we include time in this?
		# should we add a lock file to prevent accessing from 2 different proccesses?
		sq_fpath = join(
			cacheDir,
			f"{os.path.basename(inputFilename)}.db",
		)
		if isfile(sq_fpath):
			log.info(f"Removing and re-creating {sq_fpath!r}")
			os.remove(sq_fpath)

		self._data = SqEntryList(
			self,
			sq_fpath,
			create=True,
			persist=True,
		)
		self._rawEntryCompress = False
		self._cleanupPathList.add(sq_fpath)

		if not self.alts:
			log.warning(
				"SQLite mode only works with enable_alts=True"
				", force-enabling it.",
			)
		self._config["enable_alts"] = True
		self._sqlite = True

	def _resolveConvertSortParams(
		self,
		sort: "Optional[bool]",
		sortKeyName: "Optional[str]",
		sortEncoding: "Optional[str]",
		sortLocale: "Optional[str]",
		sortScript: "Optional[List[str]]",
		direct: "Optional[bool]",
		sqlite: "Optional[bool]",
		inputFilename: str,
		outputFormat: str,
		writeOptions: "Dict[str, Any]",
	) -> "Optional[Tuple[bool, bool]]":
		"""
			sortKeyName: see doc/sort-key.md

			returns (sort, direct) or None if fails
		"""
		plugin = self.plugins[outputFormat]

		sortOnWrite = plugin.sortOnWrite
		if sortOnWrite == ALWAYS:
			if sort is False:
				log.warning(
					f"Writing {outputFormat} requires sorting"
					f", ignoring user sort=False option",
				)
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
					"Plugin prevents sorting before write"
					", ignoring user sort=True option",
				)
			sort = False

		if direct and sqlite:
			raise ValueError(f"Conflictng arguments: {direct=}, {sqlite=}")

		if not sort:
			if direct is None:
				direct = True
			return direct, False

		direct = False
		# from this point, sort == True and direct == False

		writerSortKeyName = plugin.sortKeyName
		namedSortKey = None

		writerSortEncoding = getattr(plugin, "sortEncoding", None)

		if sqlite is None:
			sqlite = sort and self._config.get("auto_sqlite", True)
			if sqlite:
				log.info(
					"Automatically switching to SQLite mode"
					f" for writing {outputFormat}",
				)

		if sortOnWrite == ALWAYS:
			if not writerSortKeyName:
				log.critical("No sortKeyName was found in plugin")
				return None

			if sortKeyName and sortKeyName != writerSortKeyName:
				log.warning(
					f"Ignoring user-defined sort order {sortKeyName!r}"
					f", and using sortKey function from {outputFormat} plugin",
				)
			sortKeyName = writerSortKeyName

			if writerSortEncoding:
				sortEncoding = writerSortEncoding
		elif not sortKeyName:
			if writerSortKeyName:
				sortKeyName = writerSortKeyName
			else:
				sortKeyName = defaultSortKeyName

		namedSortKey = namedSortKeyByName.get(sortKeyName)
		if namedSortKey is None:
			log.critical(f"invalid {sortKeyName = }")
			return None

		log.info(f"Using sortKeyName = {namedSortKey.name!r}")

		if sqlite:
			self._switchToSQLite(
				inputFilename=inputFilename,
				outputFormat=outputFormat,
			)

		if not sortEncoding:
			sortEncoding = "utf-8"
		if writeOptions is None:
			writeOptions = {}
		self._data.setSortKey(
			namedSortKey=namedSortKey,
			sortEncoding=sortEncoding,
			sortLocale=sortLocale,
			sortScript=sortScript,
			writeOptions=writeOptions,
		)

		return False, True

	def convert(
		self,
		inputFilename: str,
		inputFormat: str = "",
		direct: "Optional[bool]" = None,
		progressbar: bool = True,
		outputFilename: str = "",
		outputFormat: str = "",
		sort: "Optional[bool]" = None,
		sortKeyName: "Optional[str]" = None,
		sortEncoding: "Optional[str]" = None,
		sortLocale: "Optional[str]" = None,
		sortScript: "Optional[List[str]]" = None,
		readOptions: "Optional[Dict[str, Any]]" = None,
		writeOptions: "Optional[Dict[str, Any]]" = None,
		sqlite: "Optional[bool]" = None,
		infoOverride: "Optional[Dict[str, str]]" = None,
	) -> "Optional[str]":
		"""
		returns absolute path of output file, or None if failed

		sortKeyName:
			name of sort key/algorithm
			defaults to `defaultSortKeyName` in glossary.py
			see doc/sort-key.md or sort_keys.py for other possible values

		sortEncoding:
			encoding/charset for sorting, default to utf-8
		"""
		if type(inputFilename) is not str:
			raise TypeError("inputFilename must be str")
		if type(outputFilename) is not str:
			raise TypeError("outputFilename must be str")

		if inputFormat is not None and type(inputFormat) is not str:
			raise TypeError("inputFormat must be str")
		if outputFormat is not None and type(outputFormat) is not str:
			raise TypeError("outputFormat must be str")

		if not readOptions:
			readOptions = {}
		if not writeOptions:
			writeOptions = {}

		if outputFilename == inputFilename:
			log.critical("Input and output files are the same")
			return None

		if readOptions:
			log.info(f"{readOptions = }")
		if writeOptions:
			log.info(f"{writeOptions = }")

		outputArgs = self.detectOutputFormat(
			filename=outputFilename,
			format=outputFormat,
			inputFilename=inputFilename,
		)
		if not outputArgs:
			log.critical(f"Writing file {relpath(outputFilename)!r} failed.")
			return None
		outputFilename, outputFormat, compression = outputArgs
		del outputArgs

		if isdir(outputFilename) and os.listdir(outputFilename):
			log.critical(
				f"Directory already exists and not empty: {relpath(outputFilename)}",
			)
			return None

		sortParams = self._resolveConvertSortParams(
			sort=sort,
			sortKeyName=sortKeyName,
			sortEncoding=sortEncoding,
			sortLocale=sortLocale,
			sortScript=sortScript,
			direct=direct,
			sqlite=sqlite,
			inputFilename=inputFilename,
			outputFormat=outputFormat,
			writeOptions=writeOptions,
		)
		if sortParams is None:
			return None
		direct, sort = sortParams

		del sqlite
		showMemoryUsage()

		tm0 = now()
		if not self._read(
			inputFilename,
			format=inputFormat,
			direct=direct,
			progressbar=progressbar,
			**readOptions,
		):
			log.critical(f"Reading file {relpath(inputFilename)!r} failed.")
			self.cleanup()
			return None

		del inputFilename, inputFormat, direct, readOptions

		if infoOverride:
			for key, value in infoOverride.items():
				self.setInfo(key, value)

		if compression and not self.plugins[outputFormat].singleFile:
			os.makedirs(outputFilename, mode=0o700, exist_ok=True)

		finalOutputFile = self._write(
			outputFilename,
			outputFormat,
			sort=sort,
			**writeOptions,
		)
		if not finalOutputFile:
			log.critical(f"Writing file {relpath(outputFilename)!r} failed.")
			self._closeReaders()
			self.cleanup()
			return None

		if compression:
			finalOutputFile = self._compressOutput(finalOutputFile, compression)

		log.info(f"Writing file {finalOutputFile!r} done.")
		log.info(f"Running time of convert: {now()-tm0:.1f} seconds")
		showMemoryUsage()
		self.cleanup()

		return finalOutputFile

	# ________________________________________________________________________#

	def progressInit(self, *args) -> None:
		if self._ui and self._progressbar:
			self._ui.progressInit(*args)

	def progress(self, pos: int, total: int, unit: str = "entries") -> None:
		if total == 0:
			log.warning(f"{pos=}, {total=}")
			return
		self._ui.progress(
			min(pos + 1, total) / total,
			f"{pos:,} / {total:,} {unit}",
		)

	def progressEnd(self) -> None:
		if self._ui and self._progressbar:
			self._ui.progressEnd()

	# ________________________________________________________________________#

	@classmethod
	def init(
		cls,
		usePluginsJson: bool = True,
		skipDisabledPlugins: bool = True,
	):
		"""
		Glossary.init() must be called only once, so make sure you put it in the
		right place. Probably in the top of your program's main function or module.
		"""
		cls.readFormats = []
		cls.writeFormats = []
		pluginsJsonPath = join(dataDir, "plugins-meta", "index.json")

		# even if usePluginsJson, we should still call loadPlugins to load
		# possible new plugins that are not in json file

		if usePluginsJson:
			cls.loadPluginsFromJson(pluginsJsonPath)

		cls.loadPlugins(pluginsDir, skipDisabled=skipDisabledPlugins)

		if isdir(userPluginsDir):
			cls.loadPlugins(userPluginsDir)

		os.makedirs(cacheDir, mode=0o700, exist_ok=True)
