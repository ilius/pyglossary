# Dictionary creation library
# Copyright (C) 2002 John Goerzen <jgoerzen@complete.org>
# Copyright (C) 2020 Saeed Rasooli
#
#	This program is free software; you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation; either version 2 of the License, or
#	(at your option) any later version.
#
#	This program is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#
#	You should have received a copy of the GNU General Public License
#	along with this program; if not, write to the Free Software
#	Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import gzip
import os
import string
import sys
import typing

b64_list = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
url_headword = "00-database-url"
short_headword = "00-database-short"
info_headword = "00-database-info"

validdict = set(
	string.ascii_letters + string.digits + " \t",
)


def b64_encode(val: int) -> str:
	"""Takes as input an integer val and returns a string of it encoded
	with the base64 algorithm used by dict indexes."""
	startfound = 0
	retval = ""
	for i in range(5, -1, -1):
		thispart = (val >> (6 * i)) & ((2 ** 6) - 1)
		if (not startfound) and (not thispart):
			# Both zero -- keep going.
			continue
		startfound = 1
		retval += b64_list[thispart]
	if len(retval):
		return retval
	return b64_list[0]


def b64_decode(str: str) -> int:
	"""Takes as input a string and returns an integer value of it decoded
	with the base64 algorithm used by dict indexes."""
	if not len(str):
		return 0
	retval = 0
	shiftval = 0
	for i in range(len(str) - 1, -1, -1):
		val = b64_list.index(str[i])
		retval = retval | (val << shiftval)
		shiftval += 6
	return retval


def sortNormalize(x: str) -> str:
	"""Returns a value such that x is mapped to a format that sorts properly
	with standard comparison."""
	x2 = ''
	for i in range(len(x)):
		if x[i] in validdict:
			x2 += x[i]
	return x2.upper() + "\0" + x.upper()


def sortKey(x: str) -> "list[str]":
	"""Emulate sort -df."""
	return x.split("\0")


class DictDB(object):
	def __init__(
		self: "typing.Self",
		basename: str,
		mode: str = 'read',
		quiet: int = 0,
	) -> None:
		#, url = 'unknown', shortname = 'unknown',
		#		 longinfo = 'unknown', quiet = 0):
		"""Initialize a DictDB object.

		Mode must be one of:

		read -- read-only access

		write -- write-only access, truncates existing files, does not work
		with .dz.  dict created if nonexistent.

		update -- read/write access, dict created if nonexistent.  Does not
		work with .dz.

		Read can read dict or dict.dz files.  Write and update will NOT work
		with dict.dz files.

		If quiet is nonzero, status messages
		will be suppressed."""

		self.mode = mode
		self.quiet = quiet
		self.indexEntries: "dict[str, list[tuple[int, int]]]" = {}
		# indexEntries[index] is a list of (start: int, size: int)
		self.count = 0
		self.basename = basename

		self.indexFilename = self.basename + ".index"
		if mode == 'read' and os.path.isfile(self.basename + ".dict.dz"):
			self.useCompression = 1
		else:
			self.useCompression = 0

		if self.useCompression:
			self.dictFilename = self.basename + ".dict.dz"
		else:
			self.dictFilename = self.basename + ".dict"

		if mode == 'read':
			self.indexFile = open(self.indexFilename, "rt", encoding="utf-8")
			if self.useCompression:
				self.dictFile = gzip.GzipFile(self.dictFilename, "rb")
			else:
				self.dictFile = open(self.dictFilename, "rb")
			self._initIndex()
		elif mode == 'write':
			self.indexFile = open(self.indexFilename, "wt", encoding="utf-8")
			if self.useCompression:
				raise ValueError("'write' mode incompatible with .dz files")
			self.dictFile = open(self.dictFilename, "wb")
		elif mode == 'update':
			try:
				self.indexFile = open(self.indexFilename, "r+b")
			except IOError:
				self.indexFile = open(self.indexFilename, "w+b")
			if self.useCompression:
				# Open it read-only since we don't support mods.
				self.dictFile = gzip.GzipFile(self.dictFilename, "rb")
			else:
				try:
					self.dictFile = open(self.dictFilename, "r+b")
				except IOError:
					self.dictFile = open(self.dictFilename, "w+b")
			self._initIndex()
		else:
			raise ValueError("mode must be 'read', 'write', or 'update'")

		#self.writeentry(url_headword + "\n     " + url, [url_headword])
		#self.writeentry(short_headword + "\n     " + shortname,
		#				[short_headword])
		#self.writeentry(info_headword + "\n" + longinfo, [info_headword])

	def __len__(self: "typing.Self") -> int:
		return len(self.indexEntries)

	def _initIndex(self: "typing.Self") -> None:
		"""Load the entire index off disk into memory."""
		self.indexFile.seek(0)
		for line in self.indexFile:
			splits = line.rstrip().split("\t")
			if splits[0] not in self.indexEntries:
				self.indexEntries[splits[0]] = []
			self.indexEntries[splits[0]].append((
				b64_decode(splits[1]),
				b64_decode(splits[2]),
			))

	def addIndexEntry(
		self: "typing.Self",
		word: str,
		start: int,
		size: int,
	) -> None:
		"""Adds an entry to the index.  word is the relevant word.
		start is the starting position in the dictionary and size is the
		size of the definition; both are integers."""
		if word not in self.indexEntries:
			self.indexEntries[word] = []
		self.indexEntries[word].append((start, size))

	def deleteIndexEntry(
		self: "typing.Self",
		word: str,
		start: "int | None" = None,
		size: "int | None" = None,
	) -> None:
		"""Removes an entry from the index; word is the word to search for.

		start and size are optional.  If they are specified, only index
		entries matching the specified values will be removed.

		For instance, if word is "foo" and start and size are not specified,
		all index entries for the word foo will be removed.  If start and size
		are specified, only those entries matching all criteria will be
		removed.

		This function does not actually remove the data from the .dict file.
		Therefore, information removed by this function will still
		exist on-disk in the .dict file, but the dict server will just
		not "see" it -- there will be no way to get to it anymore.

		Returns a count of the deleted entries."""

		if word not in self.indexEntries:
			return 0
		retval = 0
		entrylist = self.indexEntries[word]
		for i in range(len(entrylist) - 1, -1, -1):
			# Go backwards so the del doesn't effect the index.
			if (start is None or start == entrylist[i][0]) and \
				(size is None or size == entrylist[i][1]):
				del(entrylist[i])
				retval += 1
		if len(entrylist) == 0:         # If we emptied it, del it completely
			del(self.indexEntries[word])
		return retval

	def update(self: "typing.Self", text: str) -> None:
		"""Writes string out, if not quiet."""
		if not self.quiet:
			sys.stdout.write(text)
			sys.stdout.flush()

	def setUrl(self: "typing.Self", url: str) -> None:
		"""Sets the URL attribute of this database.  If there was
		already a URL specified, we will use deleteIndexEntry() on it
		first."""
		self.deleteIndexEntry(url_headword)
		self.addEntry(url_headword + "\n     " + url, [url_headword])

	def setShortName(self: "typing.Self", shortname: str) -> None:
		"""Sets the shortname for this database.  If there was already
		a shortname specified, we will use deleteIndexEntry() on it first."""
		self.deleteIndexEntry(short_headword)
		self.addEntry(
			short_headword + "\n     " + shortname,
			[short_headword],
		)

	def setLongInfo(self: "typing.Self", longinfo: str) -> None:
		"""Sets the extended information for this database.  If there was
		already long info specified, we will use deleteIndexEntry() on it
		first."""
		self.deleteIndexEntry(info_headword)
		self.addEntry(info_headword + "\n" + longinfo, [info_headword])

	def addEntry(
		self: "typing.Self",
		defstr: bytes,
		headwords: "list[str]",
	) -> None:
		"""Writes an entry.  defstr holds the content of the definition.
		headwords is a list specifying one or more words under which this
		definition should be indexed.  This function always adds \\n
		to the end of defstr."""
		self.dictFile.seek(0, 2)        # Seek to end of file
		start = self.dictFile.tell()
		defstr += b"\n"
		self.dictFile.write(defstr)
		for word in headwords:
			self.addIndexEntry(word, start, len(defstr))
			self.count += 1

		if self.count % 1000 == 0:
			self.update("Processed %d records\r" % self.count)

	def finish(self: "typing.Self", dosort: bool = True) -> None:
		"""Called to finish the writing process.
		**REQUIRED IF OPENED WITH 'update' OR 'write' MODES**.
		This will write the index and close the files.

		dosort is optional and defaults to true.  If set to false,
		dictlib will not sort the index file.  In this case, you
		MUST manually sort it through "sort -df" before it can be used."""

		self.update("Processed %d records.\n" % self.count)

		if dosort:
			self.update("Sorting index: converting")

			indexList: "list[str]" = []
			for word, defs in self.indexEntries.items():
				for thisdef in defs:
					indexList.append("%s\t%s\t%s" % (
						word,
						b64_encode(thisdef[0]),
						b64_encode(thisdef[1]),
					))

			self.update(" mapping")

			sortmap = {}
			for entry in indexList:
				norm = sortNormalize(entry)
				if norm in sortmap:
					sortmap[norm].append(entry)
					sortmap[norm].sort(key=sortKey)
				else:
					sortmap[norm] = [entry]

			self.update(" listing")

			normalizedentries = list(sortmap.keys())

			self.update(" sorting")

			normalizedentries.sort()

			self.update(" re-mapping")
			indexList = []

			for normentry in normalizedentries:
				for entry in sortmap[normentry]:
					indexList.append(entry)

			self.update(", done.\n")

		self.update("Writing index...\n")

		self.indexFile.seek(0)

		for entry in indexList:
			self.indexFile.write(entry + "\n")

		if self.mode == 'update':
			# In case things were deleted
			self.indexFile.truncate()

		self.close()

		self.update("Complete.\n")

	def close(self: "typing.Self") -> None:
		self.indexFile.close()
		self.dictFile.close()

	def getDefList(self: "typing.Self") -> "list[str]":
		"""Returns a list of strings naming all definitions contained
		in this dictionary."""
		return self.indexEntries.keys()

	def hasDef(self: "typing.Self", word: str) -> None:
		return word in self.indexEntries

	def getDef(self: "typing.Self", word: str) -> "list[bytes]":
		"""Given a definition name, returns a list of strings with all
		matching definitions.  This is an *exact* match, not a
		case-insensitive one.  Returns [] if word is not in the dictionary."""
		retval = []
		if not self.hasDef(word):
			return retval
		for start, length in self.indexEntries[word]:
			self.dictFile.seek(start)
			retval.append(self.dictFile.read(length))
		return retval

# print("------------------------ ", __name__)
if __name__ == "__main__":
	db = DictDB()
	print(db)
