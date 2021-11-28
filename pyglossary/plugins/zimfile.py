# -*- coding: utf-8 -*-

from formats_common import *

enable = True
lname = "zim"
format = "Zim"
description = "Zim (.zim, for Kiwix)"
extensions = (".zim",)
extensionCreate = ".zim"
singleFile = True
kind = "binary"
wiki = "https://en.wikipedia.org/wiki/ZIM_(file_format)"
website = (
	"https://wiki.openzim.org/wiki/OpenZIM",
	"OpenZIM",
)
optionsProp = {
	"skip_duplicate_words": BoolOption(
		comment="Detect and skip duplicate words",
	),
}

# https://wiki.kiwix.org/wiki/Software


class Reader(object):
	depends = {
		"libzim": "libzim==1.0",
	}

	_skip_duplicate_words = False

	resourceMimeTypes = {
		"image/png",
		"image/jpeg",
		"image/gif",
		"image/svg+xml",
		"image/webp",
		"text/css",
		"application/javascript",
		"application/octet-stream+xapian",
	}

	def __init__(self, glos: GlossaryType) -> None:
		self._glos = glos
		self._filename = None
		self._zimfile = None

	def open(self, filename: str) -> None:
		try:
			from libzim.reader import Archive
		except ModuleNotFoundError as e:
			e.msg += f", run `{pip} install libzim` to install"
			raise e

		self._filename = filename
		self._zimfile = Archive(filename)

	def close(self) -> None:
		self._filename = None
		self._zimfile = None

	def __len__(self) -> int:
		if self._zimfile is None:
			log.error(f"len(reader) called before reader.open()")
			return 0
		return self._zimfile.entry_count

	def __iter__(self):
		glos = self._glos
		zimfile = self._zimfile
		emptyContentCount = 0
		invalidMimeTypeCount = 0
		entryCount = zimfile.entry_count

		duplicateEntryCount = 0
		redirectCount = 0
		skip_dup = self._skip_duplicate_words
		hashSet = set()

		for entryIndex in range(entryCount):
			zEntry = zimfile._get_entry_by_id(entryIndex)
			word = zEntry.title

			if zEntry.is_redirect:
				redirectCount += 1
				targetWord = zEntry.get_redirect_entry().title
				yield glos.newEntry(
					word,
					f'Redirect: <a href="bword://{targetWord}">{targetWord}</a>',
					defiFormat="h",
				)
				continue

			zItem = zEntry.get_item()
			b_content = zItem.content.tobytes()

			if skip_dup:
				if word in hashSet:
					duplicateEntryCount += 1
					yield None
					continue
				hashSet.add(word)

			if not b_content:
				emptyContentCount += 1
				yield None
				# TODO: test with more zim files
				# Looks like: zItem.path == zEntry.path == "-" + word
				# print(f"b_content empty, word={word!r}, zEntry.path={zEntry.path!r}, zItem.path={zItem.path}")
				# if zEntry.path == "-" + word:
				# 	yield None
				# else:
				# 	defi = f"Path: {zEntry.path}"
				# 	yield glos.newEntry(word, defi, defiFormat="m")
				continue

			try:
				mimetype = zItem.mimetype
			except RuntimeError:
				invalidMimeTypeCount += 1
				yield glos.newDataEntry(word, b_content)

			if mimetype == "text/html":
				defi = b_content.decode("utf-8")
				defi = defi.replace(' src="../I/', ' src="./')
				yield glos.newEntry(word, defi, defiFormat="h")
				continue

			if mimetype == "text/plain":
				yield glos.newEntry(
					word, b_content.decode("utf-8"),
					defiFormat="m",
				)
				continue

			if mimetype not in self.resourceMimeTypes:
				log.warn(f"Unrecognized mimetype={mimetype!r}")

			if "|" in word:
				log.error(f"resource title: {word}")

			yield glos.newDataEntry(word, b_content)

		log.info(f"ZIM Entry Count: {entryCount}")
		if duplicateEntryCount > 0:
			log.info(f"Duplicate Title Count: {duplicateEntryCount}")
		if emptyContentCount > 0:
			log.info(f"Empty Content Count: {emptyContentCount}")
		if invalidMimeTypeCount > 0:
			log.info(f"Invalid MIME-Type Count: {invalidMimeTypeCount}")
		if redirectCount > 0:
			log.info(f"Redirect Count: {redirectCount}")
