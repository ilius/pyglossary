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

import sys

import os
import os.path
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
import re

from collections import OrderedDict as odict

import gc

from .flags import *
from . import core
from .core import userPluginsDir, cacheDir
from .entry import Entry, DataEntry
from .plugin_prop import PluginProp
from .entry_filters import *

from .langs import langDict, Lang

from .text_utils import (
	fixUtf8,
)
from .glossary_utils import (
	splitFilenameExt,
	EntryList,
)
from .sort_keys import namedSortKeyByName, NamedSortKey
from .os_utils import showMemoryUsage, rmtree
from .glossary_type import GlossaryType
from .info import *

log = logging.getLogger("pyglossary")


"""
sortKeyType = Callable[
	[[List[str]],
	Any,
]
"""

defaultSortKeyName = "headword_lower"


class Glossary(GlossaryType):
	"""
	Direct access to glos.data is droped
	Use `glos.addEntryObj(glos.newEntry(word, defi, [defiFormat]))`
		where both word and defi can be list (including alternates) or string
	See help(glos.addEntryObj)

	Use `for entry in glos:` to iterate over entries (glossary data)
	See help(pyglossary.entry.Entry) for details

	"""

	plugins = {}  # type: Dict[str, PluginProp]
	pluginByExt = {}  # type: Dict[str, PluginProp]

	formatsReadOptions = {}  # type: Dict[str, OrderedDict[str, Any]]
	formatsWriteOptions = {}  # type: Dict[str, OrderedDict[str, Any]]
	# for example formatsReadOptions[format][optName] gives you the default value

	readFormats = []  # type: List[str]
	writeFormats = []  # type: List[str]

	entryFiltersRules = [
		(None, StripWhitespaces),
		(None, NonEmptyWordFilter),
		(("skip_resources", False), SkipDataEntry),
		(("utf8_check", False), FixUnicode),
		(("lower", False), LowerWord),
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

	@classmethod
	def loadPlugins(cls: "ClassVar", directory: str) -> None:
		import pkgutil
		"""
		executed on startup.  as name implies, loads plugins from directory
		"""
		# log.debug(f"Loading plugins from directory: {directory!r}")
		if not isdir(directory):
			log.critical(f"Invalid plugin directory: {directory!r}")
			return

		pluginNames = [
			pluginName
			for _, pluginName, _ in pkgutil.iter_modules([directory])
		]
		pluginNames.sort()

		sys.path.append(directory)
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
				log.critical(msg)
			return None

		filenameOrig = filename
		filenameNoExt, filename, ext, compression = splitFilenameExt(filename)

		plugin = None
		if format:
			plugin = cls.plugins.get(format)
			if plugin is None:
				return error(f"Invalid format {format!r}")
		else:
			plugin = cls.pluginByExt.get(ext)
			if not plugin:
				plugin = cls.findPlugin(filename)
				if not plugin:
					return error("Unable to detect input format!")

		if not plugin.canRead:
			return error(f"plugin {plugin.name} does not support reading")

		if compression in getattr(plugin.readerClass, "compressions", []):
			compression = ""
			filename = filenameOrig

		return filename, plugin.name, compression

	def _closeReaders(self):
		for reader in self._readers:
			try:
				reader.close()
			except Exception:
				log.exception("")

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
		self._defiHasWordTitle = False

		self._iter = None
		self._entryFilters = []
		self._entryFiltersName = set()
		self._sort = False

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
		self._config = {}
		self._data = EntryList(self)
		self._sqlite = False
		self._rawEntryCompress = True
		self._cleanupPathList = set()
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

	def cleanup(self):
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

		if self.ui and self._progressbar:
			entryFilters.append(ShowProgressBar(self))

		if log.level <= core.TRACE:
			try:
				import psutil
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

	def removeHtmlTagsAll(self) -> None:
		"""
		Remove all HTML tags from definition

		This should only be called from a plugin's Writer.__init__ method.
		Does not apply on entries added with glos.addEntryObj
		"""
		if RemoveHtmlTagsAll.name in self._entryFiltersName:
			return
		self._entryFilters.append(RemoveHtmlTagsAll(self))

	def preventDuplicateWords(self):
		"""
		Adds entry filter to prevent duplicate `entry.s_word`

		This should only be called from a plugin's Writer.__init__ method.
		Does not apply on entries added with glos.addEntryObj

		Note: there may be still duplicate headwords or alternate words
			but we only care about making the whole `entry.s_word`
			(aka entry key) unique
		"""
		if PreventDuplicateWords.name in self._entryFiltersName:
			return
		self._entryFilters.append(PreventDuplicateWords(self))

	def __str__(self) -> str:
		return (
			"Glossary{"
			f"filename: {self._filename!r}"
			f", name: {self._info.get('name')!r}"
			"}"
		)

	def _loadedEntryGen(self) -> "Iterator[BaseEntry]":
		if not (self.ui and self._progressbar):
			yield from self._data
			return

		pbFilter = ShowProgressBar(self)
		self.progressInit("Writing")
		for entry in self._data:
			pbFilter.run(entry)
			yield entry
		self.progressEnd()

	def _readersEntryGen(self) -> "Iterator[BaseEntry]":
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
		gen: "Iterator[BaseEntry]",
	) -> "Iterator[BaseEntry]":
		for index, entry in enumerate(gen):
			if index & 0x7f == 0:  # 0x3f, 0x7f, 0xff
				gc.collect()
			if entry is None:
				continue
			for entryFilter in self._entryFilters:
				entry = entryFilter.run(entry)
				if entry is None:
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

	def infoKeys(self) -> "List[str]":
		return list(self._info.keys())

	# def formatInfoKeys(self, format: str):# FIXME

	def iterInfo(self) -> "Iterator[Tuple[str, str]]":
		return self._info.items()

	def getInfo(self, key: str) -> str:
		if not isinstance(key, str):
			raise TypeError(f"invalid key={key!r}, must be str")
		return self._info.get(
			infoKeysAliasDict.get(key.lower(), key),
			"",
		)

	def setInfo(self, key: str, value: "Optional[str]") -> None:
		if value is None:
			try:
				del self._info[key]
			except KeyError:
				pass
			return

		if not isinstance(key, str):
			raise TypeError(f"invalid key={key!r}, must be str")

		key = fixUtf8(key)
		value = fixUtf8(str(value))

		key = infoKeysAliasDict.get(key.lower(), key)
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
			key2 = infoKeysAliasDict.get(key.lower())
			if key2:
				excludeKeySet.add(key2)

		extra = odict()
		for key, value in self._info.items():
			if key in excludeKeySet:
				continue
			extra[key] = value

		return extra

	@property
	def author(self) -> str:
		for key in (c_author, c_publisher):
			value = self._info.get(key, "")
			if value:
				return value
		return ""

	def _getLangByStr(self, st) -> "Optional[Lang]":
		lang = langDict[st]
		if lang:
			return lang
		log.error(f"unknown language {st!r}")
		return

	def _getLangByInfoKey(self, key: str) -> "Optional[Lang]":
		st = self._info.get(key, "")
		if not st:
			return
		return self._getLangByStr(st)

	@property
	def config(self):
		raise NotImplementedError

	@config.setter
	def config(self, c: "Dict[str, Any]"):
		if self._config:
			log.error(f"glos.config is set more than once")
			return
		self._config = c

	@property
	def alts(self) -> bool:
		return self._config.get("enable_alts", True)

	@property
	def filename(self):
		return self._filename

	@property
	def sourceLang(self) -> "Optional[Lang]":
		return self._getLangByInfoKey(c_sourceLang)

	@property
	def targetLang(self) -> "Optional[Lang]":
		return self._getLangByInfoKey(c_targetLang)

	@sourceLang.setter
	def sourceLang(self, lang) -> None:
		if not isinstance(lang, Lang):
			raise TypeError(f"invalid lang={lang}, must be a Lang object")
		self._info[c_sourceLang] = lang.name

	@targetLang.setter
	def targetLang(self, lang) -> None:
		if not isinstance(lang, Lang):
			raise TypeError(f"invalid lang={lang}, must be a Lang object")
		self._info[c_targetLang] = lang.name

	@property
	def sourceLangName(self) -> str:
		lang = self.sourceLang
		if lang is None:
			return ""
		return lang.name

	@sourceLangName.setter
	def sourceLangName(self, langName: str) -> None:
		if not langName:
			self._info[c_sourceLang] = ""
			return
		lang = self._getLangByStr(langName)
		if lang is None:
			return
		self._info[c_sourceLang] = lang.name

	@property
	def targetLangName(self) -> str:
		lang = self.targetLang
		if lang is None:
			return ""
		return lang.name

	@targetLangName.setter
	def targetLangName(self, langName: str) -> None:
		if not langName:
			self._info[c_targetLang] = ""
			return
		lang = self._getLangByStr(langName)
		if lang is None:
			return
		self._info[c_targetLang] = lang.name

	def _getTitleTag(self, sample: str) -> str:
		from .langs.writing_system import getWritingSystemFromText
		ws = getWritingSystemFromText(sample)
		if ws and ws.name != "Latin":
			return ws.titleTag
		sourceLang = self.sourceLang
		if sourceLang:
			return sourceLang.titleTag
		return "b"

	def titleElement(
		self,
		hf: "lxml.etree.htmlfile",
		sample: str = "",
	) -> "lxml.etree._FileWriterElement":
		return hf.element(self._getTitleTag(sample))

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

	def addEntryObj(self, entry: Entry) -> None:
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
		tmpPath = None
		if not self._readers:
			if self.tmpDataDir:
				tmpPath = join(self.tmpDataDir, fname.replace("/", "_"))
			else:
				os.makedirs(join(cacheDir, "tmp"), mode=0o700, exist_ok=True)
				self._cleanupPathList.add(join(cacheDir, "tmp"))
				tmpPath = join(cacheDir, "tmp", uuid.uuid1().hex)
		return DataEntry(fname, data, tmpPath=tmpPath)

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
		name = self._info.get(c_name)
		if not name:
			return
		if self._info.get(c_sourceLang):
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

	def _setTmpDataDir(self, filename):
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
		self.tmpDataDir = join(cacheDir, basename(filename) + "_res")
		log.debug(f"tmpDataDir = {self.tmpDataDir}")
		os.makedirs(self.tmpDataDir, mode=0o700, exist_ok=True)
		self._cleanupPathList.add(self.tmpDataDir)

	def read(
		self,
		filename: str,
		format: str = "",
		direct: bool = False,
		**kwargs
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
				f", you can not read with direct=False mode"
			)

		return self._read(
			filename=filename,
			format=format,
			direct=direct,
			**kwargs
		)

	def _read(
		self,
		filename: str,
		format: str = "",
		direct: bool = False,
		progressbar: bool = True,
		**options
	) -> bool:
		filename = abspath(filename)

		self._setTmpDataDir(filename)

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
		if not self._info.get(c_name):
			self._info[c_name] = split(filename)[1]
		self._progressbar = progressbar

		self.updateEntryFilters()

		reader = self._createReader(format, options)
		try:
			reader.open(filename)
		except FileNotFoundError as e:
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
			1- Wheather or not direct mode is On (self._readers not empty)
				or Off (self._readers empty)
		"""
		if not self._readers:  # indirect mode
			self._iter = self._loadedEntryGen()
			return

		# direct mode
		self._iter = self._readersEntryGen()

	def updateIter(self):
		if self._readers:
			raise RuntimeError("can not call this while having a reader")
		self._updateIter()

	def sortWords(
		self,
		sortKeyName: "str" = "headword_lower",
		sortEncoding: "str" = "utf-8",
		writeOptions: "Optional[Dict[str, Any]]" = None,
	) -> None:
		"""
			sortKeyName: see doc/sort-key.md
		"""
		if self._readers:
			raise NotImplementedError(
				"can not use sortWords in direct mode"
			)

		if self._sqlite:
			raise NotImplementedError(
				"can not use sortWords in SQLite mode"
			)

		namedSortKey = namedSortKeyByName.get(sortKeyName)
		if namedSortKey is None:
			log.critical(f"invalid sortKeyName = {sortKeyName!r}")
			return

		t0 = now()

		self._dataSetNamedSortKey(namedSortKey, sortEncoding, writeOptions)
		self._data.sort()

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
				log.critical(msg)
			return None

		plugin = None
		if format:
			plugin = Glossary.plugins.get(format)
			if not plugin:
				return error(f"Invalid format {format}")
			if not plugin.canWrite:
				return error(f"plugin {plugin.name} does not support writing")

		if not filename:
			if not inputFilename:
				return error(f"Invalid filename {filename!r}")
			if not plugin:
				return error("No filename nor format is given for output file")
			filename = splitext(inputFilename)[0] + plugin.ext
			return filename, plugin.name, ""

		filenameOrig = filename
		filenameNoExt, filename, ext, compression = splitFilenameExt(filename)

		if not plugin:
			plugin = cls.pluginByExt.get(ext)
			if not plugin:
				plugin = cls.findPlugin(filename)

		if not plugin:
			return error("Unable to detect output format!")

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
					log.error("inputFilename is empty")
			if not ext and plugin.ext:
				filename += plugin.ext

		return filename, plugin.name, compression

	def _createWriter(
		self,
		format: str,
		options: "Dict[str, Any]",
	) -> "Any":
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

		writer = self.plugins[format].writerClass(self)
		for name, value in options.items():
			setattr(writer, f"_{name}", value)
		return writer

	def _dataSetNamedSortKey(
		self,
		namedSortKey: "NamedSortKey",
		sortEncoding: "Optional[str]",
		writeOptions: "Dict[str, Any]",
	):
		if not sortEncoding:
			sortEncoding = "utf-8"
		if writeOptions is None:
			writeOptions = {}
		self._data.setSortKey(
			namedSortKey.normal(sortEncoding, **writeOptions),
			["a", "b"]
		)

	def write(
		self,
		filename: str,
		format: str,
		**kwargs
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
			**kwargs
		)

	def _write(
		self,
		filename: str,
		format: str,
		sort: "Optional[bool]" = None,
		namedSortKey: "Optional[NamedSortKey]" = None,
		sortEncoding: "Optional[str]" = None,
		**options
	) -> "Optional[str]":
		filename = abspath(filename)

		if format not in self.plugins or not self.plugins[format].canWrite:
			log.critical(f"No Writer class found for plugin {format}")
			return

		plugin = self.plugins[format]

		if self._readers and sort:
			log.warning(
				f"Full sort enabled, falling back to indirect mode"
			)
			self._inactivateDirectMode()

		log.info(f"Writing to {format} file {filename!r}")

		writer = self._createWriter(format, options)

		self._sort = sort

		if sort:
			t0 = now()
			if not self._sqlite:
				self._dataSetNamedSortKey(namedSortKey, sortEncoding, options)
			self._data.sort()
			log.info(f"Sorting took {now() - t0:.1f} seconds")

		self._updateIter()
		try:
			writer.open(filename)
		except FileNotFoundError as e:
			log.critical(str(e))
			return False
		except Exception:
			log.exception("")
			return False

		for reader in self._readers:
			log.info(
				f"Using Reader class from {reader.formatName} plugin"
				f" for direct conversion without loading into memory"
			)

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
			for gen in genList:
				try:
					gen.send(None)
				except StopIteration:
					pass
		except FileNotFoundError as e:
			log.critical(str(e))
			return
		except Exception:
			log.exception("Exception while calling plugin\'s write function")
			return
		finally:
			showMemoryUsage()
			log.debug("Running writer.finish()")
			for writer in writerList:
				writer.finish()
			self.clear()

		showMemoryUsage()

		return filename

	def _compressOutput(self, filename: str, compression: str) -> str:
		from pyglossary.glossary_utils import compress
		return compress(self, filename, compression)

	def _switchToSQLite(
		self,
		inputFilename: str,
		outputFormat: str,
		namedSortKey: "NamedSortKey",
		sortEncoding: "Optional[str]",
		writeOptions: "Dict[str, Any]",
	) -> bool:
		from pyglossary.sq_entry_list import SqEntryList

		if not sortEncoding:
			sortEncoding = "utf-8"
		sqliteSortKey = namedSortKey.sqlite(sortEncoding, **writeOptions)

		sq_fpath = join(cacheDir, f"{basename(inputFilename)}.db")
		if isfile(sq_fpath):
			log.info(f"Removing and re-creating {sq_fpath!r}")
			os.remove(sq_fpath)

		self._data = SqEntryList(
			self,
			sq_fpath,
			sqliteSortKey,
			create=True,
			persist=True,
		)
		self._rawEntryCompress = False
		self._cleanupPathList.add(sq_fpath)

		if not self.alts:
			log.warning(
				f"SQLite mode only works with enable_alts=True"
				f", force-enabling it."
			)
		self._config["enable_alts"] = True
		self._sqlite = True

	def _resolveConvertSortParams(
		self,
		sort: "Optional[bool]",
		sortKeyName: "Optional[str]",
		sortEncoding: "Optional[str]",
		direct: "Optional[bool]",
		sqlite: "Optional[bool]",
		inputFilename: str,
		outputFormat: str,
		writeOptions: "Dict[str, Any]",
	) -> "Tuple[bool, bool, Optional[NamedSortKey]]":
		"""
			sortKeyName: see doc/sort-key.md

			returns (sort, direct, namedSortKey)
		"""
		plugin = self.plugins[outputFormat]

		sortOnWrite = plugin.sortOnWrite
		if sortOnWrite == ALWAYS:
			if sort is False:
				log.warning(
					f"Writing {format} requires sorting"
					f", ignoring user sort=False option"
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
					"Plugin prevents sorting before write" +
					", ignoring user sort=True option"
				)
			sort = False

		if direct and sqlite:
			raise ValueError(f"Conflictng arguments: direct={direct}, sqlite={sqlite}")

		if not sort:
			if direct is None:
				direct = True
			return direct, False, None

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
					f" for writing {outputFormat}"
				)

		if sortOnWrite == ALWAYS:
			if writerSortKeyName:
				if sortKeyName and sortKeyName != writerSortKeyName:
					log.warning(
						f"Ignoring user-defined sort order {sortKeyName!r}"
						f", and using sortKey function from {format} plugin"
					)
				sortKeyName = writerSortKeyName
			else:
				log.critical(f"No sortKeyName was found in plugin")
				return False, True, None
			if writerSortEncoding:
				sortEncoding = writerSortEncoding
		elif not sortKeyName:
			if writerSortKeyName:
				sortKeyName = writerSortKeyName
			else:
				sortKeyName = defaultSortKeyName

		namedSortKey = namedSortKeyByName.get(sortKeyName)
		if namedSortKey is None:
			log.critical(f"invalid sortKeyName = {sortKeyName!r}")
			return False, True, None

		log.info(f"Using sortKeyName = {namedSortKey.name!r}")

		if sqlite:
			self._switchToSQLite(
				inputFilename=inputFilename,
				outputFormat=outputFormat,
				namedSortKey=namedSortKey,
				sortEncoding=sortEncoding,
				writeOptions=writeOptions,
			)

		return False, True, namedSortKey

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
		readOptions: "Optional[Dict[str, Any]]" = None,
		writeOptions: "Optional[Dict[str, Any]]" = None,
		sqlite: "Optional[bool]" = None,
		infoOverride: "Optional[Dict[str, str]]" = None,
	) -> "Optional[str]":
		"""
		returns absolute path of output file, or None if failed

		sortKeyName: name of sort key/algorithm
			defaults to `defaultSortKeyName` in glossary.py
			see doc/sort-key.md or sort_keys.py for other possible values

		sortEncoding: encoding/charset for sorting, default to utf-8
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
			log.critical(f"Input and output files are the same")
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
			log.critical(f"Writing file {outputFilename!r} failed.")
			return
		outputFilename, outputFormat, compression = outputArgs
		del outputArgs

		if isdir(outputFilename):
			log.critical(f"Directory already exists: {outputFilename}")
			return

		direct, sort, namedSortKey = self._resolveConvertSortParams(
			sort=sort,
			sortKeyName=sortKeyName,
			sortEncoding=sortEncoding,
			direct=direct,
			sqlite=sqlite,
			inputFilename=inputFilename,
			outputFormat=outputFormat,
			writeOptions=writeOptions,
		)
		if sort and namedSortKey is None:
			return

		del sqlite
		showMemoryUsage()

		tm0 = now()
		if not self._read(
			inputFilename,
			format=inputFormat,
			direct=direct,
			progressbar=progressbar,
			**readOptions
		):
			log.critical(f"Reading file {inputFilename!r} failed.")
			return

		del inputFilename, inputFormat, direct, readOptions
		log.info("")

		if infoOverride:
			for key, value in infoOverride.items():
				self.setInfo(key, value)

		finalOutputFile = self._write(
			outputFilename,
			outputFormat,
			sort=sort,
			namedSortKey=namedSortKey,
			sortEncoding=sortEncoding,
			**writeOptions
		)
		log.info("")
		if not finalOutputFile:
			log.critical(f"Writing file {outputFilename!r} failed.")
			self._closeReaders()
			return

		if compression:
			finalOutputFile = self._compressOutput(finalOutputFile, compression)

		log.info(f"Writing file {finalOutputFile!r} done.")
		log.info(f"Running time of convert: {now()-tm0:.1f} seconds")
		showMemoryUsage()
		self.cleanup()

		return finalOutputFile

	# ________________________________________________________________________#

	def progressInit(self, *args) -> None:
		if self.ui and self._progressbar:
			self.ui.progressInit(*args)

	def progress(self, pos: int, total: int, unit: str = "entries") -> None:
		if total == 0:
			log.warning(f"pos={pos}, total={total}")
			return
		self.ui.progress(
			min(pos + 1, total) / total,
			f"{pos:,} / {total:,} {unit}",
		)

	def progressEnd(self) -> None:
		if self.ui and self._progressbar:
			self.ui.progressEnd()

	# ________________________________________________________________________#

	@classmethod
	def init(cls):
		cls.readFormats = []
		cls.writeFormats = []
		cls.loadPlugins(join(dirname(__file__), "plugins"))
		if os.path.exists(userPluginsDir):
			cls.loadPlugins(userPluginsDir)
		if not isdir(cacheDir):
			os.makedirs(cacheDir)
