# -*- coding: utf-8 -*-

from formats_common import *
from pyglossary.entry import Entry

enable = True
format = 'Aard2Slob'
description = 'Aard 2 (slob)'
extensions = ('.slob',)
singleFile = True
tools = [
	{
		"name": "Aard 2 for Android",
		"web": "http://aarddict.org/",
		"platforms": ["Android"],
		"license": "GPL",
		# no html support at all, no RTL support
	},
	{
		"name": "Aard2 for Web",
		"web": "http://aarddict.org/",
		"platforms": ["Web"],
		"license": "MPL",
		# no html support at all, RTL works fine
	},
]
optionsProp = {
	"compression": StrOption(
		values=["", "bz2", "zlib", "lzma2"],
		comment="Compression Algorithm",
	),
	"content_type": StrOption(
		customValue=True,
		values=["text/plain; charset=utf-8"],
		comment="Content Type",
	),
	"encoding": EncodingOption(),
}
depends = {
	"icu": "PyICU",
}


class Reader(object):
	def __init__(self, glos):
		self._glos = glos
		self._clear()
		try:
			import icu
		except ModuleNotFoundError as e:
			e.msg += f", run `{pip} install PyICU` to install"
			raise e

	def close(self):
		if self._slobObj is not None:
			self._slobObj.close()
		self._clear()

	def _clear(self):
		self._filename = ""
		self._slobObj = None # slobObj is instance of slob.Slob class
		self._refIndex = -1

	def open(self, filename, encoding="utf-8"):
		from pyglossary.plugin_lib import slob
		self._filename = filename
		self._slobObj = slob.open(filename)

	def __len__(self):
		if self._slobObj is None:
			log.error("called len() on a reader which is not open")
			return 0
		return len(self._slobObj)

	def __iter__(self):
		return self

	def __next__(self):
		if not self._slobObj:
			log.error("iterating over a reader which is not open")
			raise StopIteration
		self._refIndex += 1
		if self._refIndex >= len(self._slobObj):
			raise StopIteration
		blob = self._slobObj[self._refIndex]
		# blob.key is str, blob.content is bytes
		word = blob.key
		defi = toStr(blob.content)
		return Entry(word, defi)


def write(
	glos: GlossaryType,
	filename: str,
	compression: str = "",
	content_type: str = "",
):
	try:
		import icu
	except ModuleNotFoundError as e:
		e.msg += f", run `{pip} install PyICU` to install"
		raise e
	from pyglossary.plugin_lib import slob
	kwargs = {}
	if compression:
		kwargs["compression"] = compression
	log.info("removing all html tags since Aard2 does not support html")
	glos.removeHtmlTagsAll()
	# must not pass compression=None to slob.create()
	with slob.create(filename, **kwargs) as slobWriter:
		name = glos.getInfo("name")
		slobWriter.tag("label", toStr(name))
		while True:
			entry = yield
			if entry is None:
				break
			words = entry.l_word
			b_defi = entry.defi.encode("utf-8")
			slobWriter.add(
				b_defi,
				*tuple(words),
				content_type=content_type,
			)
	# slobWriter.finalize() is called called on __exit__


# is Writer class needed?



