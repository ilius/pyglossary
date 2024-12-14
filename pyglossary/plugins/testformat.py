

from __future__ import annotations

# -*- coding: utf-8 -*-
from collections.abc import Generator, Iterator

from pyglossary.glossary_types import EntryType, GlossaryType
from pyglossary.option import Option

__all__ = [
	"Reader",
	"Writer",
	"description",
	"enable",
	"extensionCreate",
	"extensions",
	"kind",
	"lname",
	"name",
	"optionsProp",
	"singleFile",
	"website",
	"wiki",
]

enable = False
lname = "testformat"
name = "Test"
description = "Test Format File(.test)"
extensions = (".test", ".tst")
extensionCreate = ".test"
singleFile = True
kind = "text"
wiki = ""
website = None

# key is option/argument name, value is instance of Option
optionsProp: dict[str, Option] = {}


class Reader:
	def __init__(self, glos: GlossaryType) -> None:
		self._glos = glos
		self._filename = ""
		self._wordCount = 0

	def __len__(self) -> int:
		# return the number of entries if you have it
		# if you don't, return 0 and progressbar will be disabled
		# self._wordCount can be set in self.open function
		# but if you want to set it, you should set it before
		# iteration begins and __iter__ method is called
		return self._wordCount

	def open(self, filename: str) -> None:
		# open the file, read headers / info and set info to self._glos
		# and set self._wordCount if you can
		# read-options should be keyword arguments in this method
		self._wordCount = 100
		# log.info(f"some useful message")
		# here read info from file and set to Glossary object
		self._glos.setInfo("name", "Test")
		desc = "Test glossary created by a PyGlossary plugin"
		self._glos.setInfo("description", desc)
		self._glos.setInfo("author", "Me")
		self._glos.setInfo("copyright", "GPL")

	def close(self) -> None:
		# this is called after reading/conversion is finished
		# if you have an open file object, close it here
		# if you need to clean up temp files, do it here
		pass

	def __iter__(self) -> Iterator[EntryType]:
		# the easiest and simplest way to implement an Iterator is
		# by writing a generator, by calling: yield glos.newEntry(word, defi)
		# inside a loop (typically iterating over a file object for text file)
		# another way (which is harder) is by implementing __next__ method
		# and returning self in __iter__
		# that forces you to keep the state manually because __next__ is called
		# repeatedly, but __iter__ is only called once
		glos = self._glos
		for i in range(self._wordCount):
			# here get word and definition from file(depending on your format)
			word = f"word_{i}"
			defi = f"definition {i}"
			yield glos.newEntry(word, defi)


class Writer:
	def __init__(self, glos: GlossaryType) -> None:
		self._glos = glos
		self._filename = ""

	def open(self, filename: str) -> None:
		self._filename = filename

	def write(self) -> Generator[None, EntryType, None]:
		glos = self._glos
		filename = self._filename  # noqa
		# log.info(f"some useful message")
		while True:
			entry = yield
			if entry is None:
				break
			if entry.isData():
				# can save it with entry.save(directory)
				continue
			word = entry.s_word  # noqa
			defi = entry.defi  # noqa
			# here write word and defi to the output file (depending on
			# your format)
		# here read info from Glossaey object
		name = glos.getInfo("name")  # noqa
		desc = glos.getInfo("description")  # noqa
		author = glos.author  # noqa
		copyright = glos.getInfo("copyright")  # noqa
		# if an info key doesn't exist, getInfo returns empty string
		# now write info to the output file (depending on your output format)

	def finish(self) -> None:
		self._filename = ""
