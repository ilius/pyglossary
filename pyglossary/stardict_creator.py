from __future__ import annotations

from os.path import splitext
from typing import TYPE_CHECKING

from pyglossary.entry import DataEntry, Entry
from pyglossary.glossary_v2 import Glossary
from pyglossary.os_utils import runDictzip
from pyglossary.plugins.stardict import Writer
from pyglossary.sort_keys import lookupSortKey
from pyglossary.sq_entry_list import SqEntryList

if TYPE_CHECKING:
	from pyglossary.glossary_types import EntryType, RawEntryType


class StarDictCreator:
	def __init__(
		self,
		filename: str,
		tmpDbFile: str,
		defiFormat: str = "h",
	) -> None:
		self._filename = filename
		self._defiFormat = defiFormat
		self._defiFormatB = defiFormat.encode("ascii")
		glos = self._glos = Glossary()
		w = self._writer = Writer(glos)

		# w._sametypesequence = "h" # generally not needed

		w.open(filename)

		gen = self._gen = w.write()
		next(gen)

		entryList = self._entryList = SqEntryList(
			entryToRaw=self.entryToRaw,
			entryFromRaw=self.entryFromRaw,
			database=tmpDbFile,
			create=True,
		)
		entryList.setSortKey(
			namedSortKey=lookupSortKey("stardict"),
			sortEncoding="utf-8",
			writeOptions={},
		)
		entryList.sort()

	def entryToRaw(self, entry: EntryType) -> RawEntryType:
		return [self._defiFormatB, entry.b_defi] + entry.lb_term

	def entryFromRaw(self, rawEntry: RawEntryType) -> EntryType:
		defiFormat = rawEntry[0].decode("ascii") or self._defiFormat
		defi = rawEntry[1].decode("utf-8")

		if defiFormat == "b":
			fname = rawEntry[2].decode("utf-8")
			if isinstance(fname, list):
				fname = fname[0]
			return DataEntry(fname, tmpPath=defi)

		return Entry(
			[b.decode("utf-8") for b in rawEntry[2:]],
			defi,
			defiFormat=defiFormat,
		)

	def addEntry(self, terms: list[str], defi: str) -> None:
		self._entryList.append(self._glos.newEntry(terms, defi))

	def addResource(self, fname: str, data: bytes) -> None:
		self._entryList.append(self._glos.newDataEntry(fname, data))

	def write(self) -> None:
		for entry in self._entryList:
			self._gen.send(entry)

		try:
			self._gen.send(None)
		except StopIteration:
			pass

	def finish(self, dictzip: bool = False) -> None:
		self._writer.finish()
		outPathNoExt, _ = splitext(self._filename)
		if dictzip:
			runDictzip(f"{outPathNoExt}.dict")
