"""
Programmatic glossary writer with bounded RAM for sorted output formats.

Use ``GlossaryCreator`` when building a glossary in Python code and writing
it to any supported format. Unlike loading everything into ``Glossary`` and
calling ``write()``, formats that always sort on write buffer entries in
SQLite so large glossaries need not fit in memory.

See ``doc/lib-examples/custom-writer-epub2.py`` for a minimal example.

Note: entry filters (configured on ``Glossary``) do not apply to
``GlossaryCreator``.
"""

from __future__ import annotations

import os
from contextlib import suppress
from os.path import abspath, basename, isfile, join
from typing import TYPE_CHECKING, Any

from .core import cacheDir
from .flags import ALWAYS
from .glossary_utils import WriteError
from .glossary_v2 import Glossary
from .plugin_handler import PluginHandler
from .sort_keys import defaultSortKeyName, lookupSortKey
from .sq_entry_list import SqEntryList

if TYPE_CHECKING:
	from .entry_base import MultiStr
	from .glossary_types import EntryType
	from .plugin_prop import PluginProp


__all__ = ["GlossaryCreator"]


class GlossaryCreator:
	"""
	Build a glossary in code and write to any output format.

	For formats that require sorting, entries are stored in SQLite (by default)
	during building so RAM usage stays bounded — same idea as StarDictCreator,
	but works for any sorted format (StarDict, EPUB-2, Yomichan, etc.).

	Notes
	-----
	Entry filters configured on ``Glossary`` do not apply to this class.

	"""

	def __init__(  # noqa: PLR0913 Too many arguments in function definition
		self,
		filename: str,
		formatName: str,
		*,
		sqlite: bool = True,
		tmpDbFile: str = "",
		sortKeyName: str | None = None,
		sortEncoding: str | None = None,
		**writeOptions: Any,
	) -> None:
		"""
		Prepare a glossary writer for the given output file and format.

		For formats that always sort on write (StarDict, EPUB-2, Yomichan, etc.),
		entries are buffered in SQLite so large glossaries do not need to fit in RAM.

		Parameters
		----------
		filename:
			Output file or directory path.
		formatName:
			Plugin/format name (e.g. ``"Stardict"``, ``"Epub2"``).
		sqlite:
			When sorting, store entries in a SQLite file on disk (``True``)
			or in memory (``False``).
		tmpDbFile:
			Path for the temporary SQLite database. When empty and ``sqlite`` is
			``True``, a file under the cache directory is used.
		sortKeyName:
			Override the format's default sort key.
		sortEncoding:
			Override the format's default sort encoding.
		**writeOptions:
			Format-specific write options, merged into ``finish()`` options.

		"""
		self._filename = filename
		self._formatName = formatName
		self._writeOptions = writeOptions
		self._sqlite = sqlite
		self._glos = Glossary()
		self._entryList: SqEntryList | None = None

		if formatName not in PluginHandler.plugins:
			raise WriteError(f"No plugin {formatName!r} was found")

		plugin = PluginHandler.plugins[formatName]
		if plugin.sortOnWrite == ALWAYS:
			self._entryList = self._newSortedEntryList(
				plugin=plugin,
				filename=filename,
				sqlite=sqlite,
				tmpDbFile=tmpDbFile,
				sortKeyName=sortKeyName,
				sortEncoding=sortEncoding,
				writeOptions=writeOptions,
			)

	def _newSortedEntryList(  # noqa: PLR0913 Too many arguments in function definition
		self,
		plugin: PluginProp,
		filename: str,
		*,
		sqlite: bool,
		tmpDbFile: str,
		sortKeyName: str | None,
		sortEncoding: str | None,
		writeOptions: dict[str, Any],
	) -> SqEntryList:
		"""Create and configure a sorted entry list for the target format."""
		if not plugin.sortKeyName:
			raise WriteError(f"No sortKeyName in plugin {plugin.name!r}")
		keyName = sortKeyName or plugin.sortKeyName or defaultSortKeyName
		namedSortKey = lookupSortKey(keyName)
		if namedSortKey is None:
			raise WriteError(f"invalid sortKeyName={keyName!r}")
		encoding = sortEncoding or getattr(plugin, "sortEncoding", None) or "utf-8"

		database = tmpDbFile
		if sqlite:
			if not database:
				database = join(cacheDir, f"{basename(filename)}.db")
			if isfile(database):
				os.remove(database)
		else:
			database = "file::memory:"

		entryList = SqEntryList(
			entryToRaw=self._glos._entryToRaw,
			entryFromRaw=self._glos._entryFromRaw,
			database=database,
			create=True,
		)
		entryList.setSortKey(
			namedSortKey=namedSortKey,
			sortEncoding=encoding,
			writeOptions=writeOptions,
		)
		return entryList

	@property
	def glos(self) -> Glossary:
		"""Underlying Glossary instance."""
		return self._glos

	def addEntry(
		self,
		word: MultiStr,
		defi: str,
		defiFormat: str = "",
	) -> None:
		"""
		Add a glossary entry.

		``defiFormat`` must be empty or one of ``"m"`` (plain text),
		``"h"`` (HTML), or ``"x"`` (XDXF).
		"""
		entry = self._glos.newEntry(word, defi, defiFormat=defiFormat)
		self._appendEntry(entry)

	def addEntryObj(self, entry: EntryType) -> None:
		"""Add a pre-built entry object."""
		self._appendEntry(entry)

	def addDataEntry(self, fname: str, data: bytes) -> None:
		"""Add a resource file (image, CSS, etc.) as a data entry."""
		self._appendEntry(self._glos.newDataEntry(fname, data))

	def setInfo(self, key: str, value: str) -> None:
		"""Set glossary metadata (e.g. ``title``, ``author``)."""
		self._glos.info[key] = value

	def _appendEntry(self, entry: EntryType) -> None:
		"""Route the entry to the sorted buffer or in-memory glossary."""
		if self._entryList is not None:
			self._entryList.append(entry)
			return
		self._glos.addEntry(entry)

	def finish(self, **writeOptions: Any) -> str:
		"""
		Sort (if required) and write the glossary to disk.

		Returns the absolute path of the output file.
		Additional write options may be passed here or in ``__init__``.
		"""
		options = {**self._writeOptions, **writeOptions}
		if self._entryList is None:
			return self._glos.write(
				self._filename,
				formatName=self._formatName,
				**options,
			)

		self._entryList.sort()
		if self._sqlite:
			self._glos._sqlite = True
			self._glos._config["enable_alts"] = True

		writer = self._glos._createWriter(self._formatName, options)
		writer.open(self._filename)
		gen = writer.write()
		next(gen)
		for entry in self._entryList:
			gen.send(entry)
		with suppress(StopIteration):
			gen.send(None)
		writer.finish()
		return abspath(self._filename)
