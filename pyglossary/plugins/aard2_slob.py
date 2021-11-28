# -*- coding: utf-8 -*-

from formats_common import *
import shutil

enable = True
lname = "aard2_slob"
format = 'Aard2Slob'
description = 'Aard 2 (.slob)'
extensions = ('.slob',)
extensionCreate = ".slob"
singleFile = True
kind = "binary"
wiki = "https://github.com/itkach/slob/wiki"
website = (
	"http://aarddict.org/",
	"aarddict.org",
)
optionsProp = {
	"compression": StrOption(
		values=["", "bz2", "zlib", "lzma2"],
		comment="Compression Algorithm",
	),
	"content_type": StrOption(
		customValue=True,
		values=[
			"text/plain; charset=utf-8",
			"text/html; charset=utf-8",
		],
		comment="Content Type",
	),
	# "encoding": EncodingOption(),
	"file_size_approx": FileSizeOption(
		comment="split up by given approximate file size\nexamples: 100m, 1g",
	),
	"separate_alternates": BoolOption(
		comment="add alternate headwords as separate entries to slob",
	),
	"word_title": BoolOption(
		comment="add headwords title to begining of definition",
	),
}

extraDocs = [
	(
		"PyICU",
		"See [doc/pyicu.md](./doc/pyicu.md) file for more detailed"
		" instructions on how to install PyICU.",
	),
]

file_size_check_every = 100


class Reader(object):
	depends = {
		"icu": "PyICU",  # >=1.5
	}

	def __init__(self, glos):
		self._glos = glos
		self._clear()
		self._re_bword = re.compile(
			'(<a href=[^<>]+?>)',
			re.I,
		)
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
		self._slobObj = None  # slobObj is instance of slob.Slob class

	def open(self, filename):
		from pyglossary.plugin_lib import slob
		self._filename = filename
		self._slobObj = slob.open(filename)
		tags = dict(self._slobObj.tags.items())

		try:
			name = tags.pop("label")
		except KeyError:
			pass
		else:
			self._glos.setInfo("name", name)

		try:
			creationTime = tags.pop("created.at")
		except KeyError:
			pass
		else:
			self._glos.setInfo("creationTime", creationTime)

		try:
			createdBy = tags.pop("created.by")
		except KeyError:
			pass
		else:
			self._glos.setInfo("author", createdBy)

		copyrightLines = []
		for key in ("copyright", "license.name", "license.url"):
			try:
				value = tags.pop(key)
			except KeyError:
				continue
			copyrightLines.append(value)
		if copyrightLines:
			self._glos.setInfo("copyright", "\n".join(copyrightLines))

		try:
			uri = tags.pop("uri")
		except KeyError:
			pass
		else:
			self._glos.setInfo("website", uri)

		try:
			edition = tags.pop("edition")
		except KeyError:
			pass
		else:
			self._glos.setInfo("edition", edition)

		for key, value in tags.items():
			self._glos.setInfo(f"slob.{key}", value)

	def __len__(self):
		if self._slobObj is None:
			log.error("called len() on a reader which is not open")
			return 0
		return len(self._slobObj)

	def _href_sub(self, m: "re.Match") -> str:
		st = m.group(0)
		if "//" in st:
			return st
		st = st.replace('href="', 'href="bword://')
		st = st.replace("href='", "href='bword://")
		return st

	def __iter__(self):
		from pyglossary.plugin_lib.slob import MIME_HTML, MIME_TEXT
		if self._slobObj is None:
			raise RuntimeError("iterating over a reader while it's not open")

		slobObj = self._slobObj
		blobSet = set()

		# slob library gives duplicate blobs when iterating over slobObj
		# even keeping the last id is not enough, since duplicate blobs
		# are not all consecutive. so we have to keep a set of blob IDs

		for blob in slobObj:
			_id = blob.id
			if _id in blobSet:
				yield None  # update progressbar
				continue
			blobSet.add(_id)

			# blob.key is str, blob.content is bytes
			word = blob.key

			ctype = blob.content_type.split(";")[0]
			if ctype not in (MIME_HTML, MIME_TEXT):
				log.debug(f"{word!r}: content_type={blob.content_type}")
				if word.startswith("~/"):
					word = word[2:]
				yield self._glos.newDataEntry(word, blob.content)
				continue
			defiFormat = ""
			if ctype == MIME_HTML:
				defiFormat = "h"
			elif ctype == MIME_TEXT:
				defiFormat = "m"

			defi = blob.content.decode("utf-8")
			defi = self._re_bword.sub(self._href_sub, defi)
			yield self._glos.newEntry(word, defi, defiFormat=defiFormat)


class Writer(object):
	depends = {
		"icu": "PyICU",
	}

	_compression: str = "zlib"
	_content_type: str = ""
	_file_size_approx: int = 0
	_separate_alternates: bool = False
	_word_title: bool = False

	resourceMimeTypes = {
		"png": "image/png",
		"jpeg": "image/jpeg",
		"jpg": "image/jpeg",
		"gif": "image/gif",
		"svg": "image/svg+xml",
		"webp": "image/webp",
		"tiff": "image/tiff",
		"tif": "image/tiff",
		"css": "text/css",
		"js": "application/javascript",
		"json": "application/json",
		"woff": "application/font-woff",
		"ttf": "application/x-font-ttf",
		"otf": "application/x-font-opentype",
		"mp3": "audio/mpeg",
		"ini": "text/plain",
		# "application/octet-stream+xapian",
	}

	def __init__(self, glos: GlossaryType) -> None:
		self._glos = glos
		self._filename = None
		self._resPrefix = ""
		self._slobWriter = None

	def _slobObserver(self, event: "slob.WriterEvent"):
		log.debug(f"slob: {event.name}{': ' + event.data if event.data else ''}")

	def _open(self, filename: str, namePostfix: str) -> None:
		import icu
		from pyglossary.plugin_lib import slob
		if isfile(filename):
			shutil.move(filename, f"{filename}.bak")
			log.warning(f"renamed existing {filename!r} to {filename+'.bak'!r}")
		kwargs = {}
		kwargs["compression"] = self._compression
		self._slobWriter = slobWriter = slob.Writer(
			filename,
			observer=self._slobObserver,
			workdir=cacheDir,
			**kwargs
		)
		slobWriter.tag("label", self._glos.getInfo("name") + namePostfix)

	def open(self, filename: str) -> None:
		try:
			import icu
		except ModuleNotFoundError as e:
			e.msg += f", run `{pip} install PyICU` to install"
			raise e
		if isfile(filename):
			raise IOError(f"File '{filename}' already exists")
		namePostfix = ""
		if self._file_size_approx > 0:
			namePostfix = " (part 1)"
		self._open(filename, namePostfix)
		self._filename = filename

	def finish(self):
		self._filename = None
		if self._slobWriter is not None:
			self._slobWriter.finalize()
			self._slobWriter = None

	def addDataEntry(self, entry: "DataEntry") -> None:
		slobWriter = self._slobWriter
		rel_path = entry.s_word
		_, ext = splitext(rel_path)
		ext = ext.lstrip(os.path.extsep).lower()
		content_type = self.resourceMimeTypes.get(ext)
		if not content_type:
			log.error(f'unknown content type for {rel_path!r}')
			return
		content = entry.data
		key = self._resPrefix + rel_path
		try:
			key.encode(slobWriter.encoding)
		except UnicodeEncodeError:
			log.error('Failed to add, broken unicode in key: {!a}'.format(key))
			return
		slobWriter.add(content, key, content_type=content_type)

	def addEntry(self, entry: "Entry") -> None:
		words = entry.l_word
		b_defi = entry.defi.encode("utf-8")
		_ctype = self._content_type
		writer = self._slobWriter

		entry.detectDefiFormat()
		defiFormat = entry.defiFormat

		if self._word_title and defiFormat in ("h", "m"):
			if defiFormat == "m":
				defiFormat = "h"
			title = self._glos.wordTitleStr(
				words[0],
			)
			b_defi = title.encode("utf-8") + b_defi

		if defiFormat == "h":
			b_defi = b_defi.replace(b'"bword://', b'"')
			b_defi = b_defi.replace(b"'bword://", b"'")

		if not _ctype:
			if defiFormat == "h":
				_ctype = "text/html; charset=utf-8"
			elif defiFormat == "m":
				_ctype = "text/plain; charset=utf-8"
			else:
				_ctype = "text/plain; charset=utf-8"

		if not self._separate_alternates:
			writer.add(
				b_defi,
				*tuple(words),
				content_type=_ctype,
			)
			return

		headword, *alts = words
		writer.add(
			b_defi,
			headword,
			content_type=_ctype,
		)
		for alt in alts:
			writer.add(
				b_defi,
				f"{alt}, {headword}",
				content_type=_ctype,
			)

	def write(self) -> "Generator[None, BaseEntry, None]":
		file_size_approx = int(self._file_size_approx * 0.95)
		entryCount = 0
		sumBlobSize = 0
		fileIndex = 0
		filenameNoExt, _ = splitext(self._filename)
		while True:
			entry = yield
			if entry is None:
				break

			if entry.isData():
				self.addDataEntry(entry)
			else:
				self.addEntry(entry)

			if file_size_approx > 0:
				entryCount += 1
				if entryCount % file_size_check_every == 0:
					sumBlobSize = self._slobWriter.size_data()
					if sumBlobSize >= file_size_approx:
						self._slobWriter.finalize()
						fileIndex += 1
						self._open(f"{filenameNoExt}.{fileIndex}.slob", f" (part {fileIndex+1})")
						sumBlobSize = 0
						entryCount = 0
