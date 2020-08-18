# -*- coding: utf-8 -*-

from formats_common import *

enable = True
format = "Zim"
description = "Zim (Kiwix)"
extensions = (".zim",)
singleFile = True
optionsProp = {
}

# https://wiki.kiwix.org/wiki/Software
tools = [
	{
		"name": "Kiwix Desktop",
		"web": "https://github.com/kiwix/kiwix-desktop",
		"platforms": ["Linux", "Windows"],
		"license": "GPL",
	},
	{
		"name": "Kiwix JS",
		"web": "https://github.com/kiwix/kiwix-js",
		"platforms": ["Windows"],
		"license": "GPL",
	},
	{
		"name": "Kiwix Serve",
		"web": "https://github.com/kiwix/kiwix-tools",
		"platforms": ["Linux", "Windows"],
		"license": "GPL",
	},
	{
		"name": "Kiwix for Apple Mac OS X",
		"web": "macos.kiwix.org",
		"platforms": ["Mac"],
		"license": "",
	},
	{
		"name": "Kiwix for Android",
		"web": "https://github.com/kiwix/kiwix-android",
		"platforms": ["Android"],
		"license": "GPL",
	},
]


class Reader(object):
	depends = {
		"libzim": "libzim",
	}

	resourceMimeTypes = {
		"image/png",
		"image/jpeg",
		"image/gif",
		"image/svg+xml",
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
			from libzim.reader import File
		except ModuleNotFoundError as e:
			e.msg += f", run `{pip} install libzim` to install"
			raise e

		self._filename = filename
		self._zimfile = File(filename)

	def close(self) -> None:
		self._filename = None
		self._zimfile = None

	def __len__(self) -> int:
		if self._zimfile is None:
			log.error(f"len(reader) called before reader.open()")
			return 0
		return self._zimfile.article_count

	def __iter__(self):
		glos = self._glos
		zimfile = self._zimfile
		emptyContentCount = 0
		invalidMimeTypeCount = 0
		article_count = zimfile.article_count
		for articleIndex in range(article_count):
			ar = zimfile.get_article_by_id(articleIndex)
			word = ar.title
			b_content = ar.content.tobytes()

			if not b_content:
				emptyContentCount += 1
				if ar.url != word:
					defi = f"URL: {ar.url}"
					yield glos.newEntry(word, defi, defiFormat="m")
				yield None
				continue

			try:
				mimetype = ar.mimetype
			except RuntimeError:
				invalidMimeTypeCount += 1
				yield glos.newDataEntry(word, b_content)

			if mimetype == "text/html":
				yield glos.newEntry(
					word, b_content.decode("utf-8"),
					defiFormat="h",
				)
				continue
			if mimetype == "text/plain":
				yield glos.newEntry(
					word, b_content.decode("utf-8"),
					defiFormat="m",
				)
				continue

			if mimetype not in self.resourceMimeTypes:
				log.warn("Unrecognized mimetype={mimetype!r}")

			yield glos.newDataEntry(word, b_content)

		log.info(f"Article Count: {article_count}")
		if emptyContentCount > 0:
			log.info(f"Empty Content Count: {emptyContentCount}")
		if invalidMimeTypeCount > 0:
			log.info(f"Invalid MIME-Type Count: {invalidMimeTypeCount}")
