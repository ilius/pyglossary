# -*- coding: utf-8 -*-

from formats_common import *

enable = True
format = "Zim"
description = "Zim (Kiwix)"
extensions = (".zim",)
singleFile = True
optionsProp = {
	"skip_duplicate_words": BoolOption(),
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

	_skip_duplicate_words = False

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
		articleCount = zimfile.article_count

		duplicateArticleCount = 0
		redirectCount = 0
		skip_dup = self._skip_duplicate_words
		hashSet = set()

		for articleIndex in range(articleCount):
			ar = zimfile.get_article_by_id(articleIndex)
			word = ar.title

			if ar.is_redirect:
				redirectCount += 1
				targetWord = ar.get_redirect_article().title
				yield glos.newEntry(
					word,
					f'Redirect: <a href="bword://{targetWord}">{targetWord}</a>',
					defiFormat="h",
				)
				continue

			b_content = ar.content.tobytes()

			if skip_dup:
				if word in hashSet:
					duplicateArticleCount += 1
					yield None
					continue
				hashSet.add(word)

			if not b_content:
				emptyContentCount += 1
				if ar.url == word:
					yield None
				else:
					defi = f"URL: {ar.url}"
					yield glos.newEntry(word, defi, defiFormat="m")
				continue

			try:
				mimetype = ar.mimetype
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

		log.info(f"Article Count: {articleCount}")
		if duplicateArticleCount > 0:
			log.info(f"Duplicate Title Count: {duplicateArticleCount}")
		if emptyContentCount > 0:
			log.info(f"Empty Content Count: {emptyContentCount}")
		if invalidMimeTypeCount > 0:
			log.info(f"Invalid MIME-Type Count: {invalidMimeTypeCount}")
		if redirectCount > 0:
			log.info(f"Redirect Count: {redirectCount}")
