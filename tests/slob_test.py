from __future__ import annotations

import io
import logging
import os
import random
import sys
import tempfile
import unicodedata
import unittest
from os.path import abspath, dirname
from typing import cast

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

import icu

from pyglossary import slob
from pyglossary.core_test import MockLogHandler

mockLog = MockLogHandler()
log = logging.getLogger("pyglossary")
log.addHandler(mockLog)


class StructReaderWriter(slob.StructWriter):
	def __init__(
		self,
		file: io.BufferedWriter,
		reader: slob.StructReader,
		encoding: str | None = None,
	) -> None:
		super().__init__(
			file=file,
			encoding=encoding,
		)
		self._reader = reader

	def tell(self) -> int:
		return self._file.tell()

	def write(self, data: bytes) -> int:
		return self._file.write(data)

	def read_byte(self) -> int:
		return self._reader.read_byte()

	def read_tiny_text(self) -> str:
		return self._reader.read_tiny_text()


class TagNotFound(Exception):
	pass


def set_tag_value(filename: str, name: str, value: str) -> None:
	with slob.fopen(filename, "rb+") as file:
		file.seek(len(slob.MAGIC) + 16)
		encoding = slob.read_byte_string(file, slob.U_CHAR).decode(slob.UTF8)
		if slob.encodings.search_function(encoding) is None:
			raise slob.UnknownEncoding(encoding)
		reader = StructReaderWriter(
			file=file,
			reader=slob.StructReader(file, encoding=encoding),
			encoding=encoding,
		)
		reader.read_tiny_text()
		tag_count = reader.read_byte()
		for _ in range(tag_count):
			key = reader.read_tiny_text()
			if key == name:
				reader.write_tiny_text(value, editable=True)
				return
			reader.read_tiny_text()
	raise TagNotFound(name)


class BaseTest(unittest.TestCase):
	def setUp(self):
		self.tmpdir = tempfile.TemporaryDirectory(prefix="test")
		self._writers = []

	def tearDown(self):
		for w in self._writers:
			w.close()
		self.tmpdir.cleanup()

	def _observer(self, event: slob.WriterEvent):
		log.info(f"slob: {event.name}{': ' + event.data if event.data else ''}")

	def create(self, *args, observer=None, **kwargs):
		if observer is None:
			observer = self._observer
		w = slob.Writer(*args, observer=observer, **kwargs)
		self._writers.append(w)
		return w


class TestReadWrite(BaseTest):
	def setUp(self):
		BaseTest.setUp(self)

		self.path = os.path.join(self.tmpdir.name, "test.slob")

		writer = self.create(self.path)

		self.tags = {
			"a": "abc",
			"bb": "xyz123",
			"ccc": "lkjlk",
		}
		for name, value in self.tags.items():
			writer.tag(name, value)

		self.tag2 = "bb", "xyz123"

		self.blob_encoding = "ascii"

		self.data = [
			(("c", "cc", "ccc"), slob.MIME_TEXT, "Hello C 1"),
			("a", slob.MIME_TEXT, "Hello A 12"),
			("z", slob.MIME_TEXT, "Hello Z 123"),
			("b", slob.MIME_TEXT, "Hello B 1234"),
			("d", slob.MIME_TEXT, "Hello D 12345"),
			("uuu", slob.MIME_HTML, "<html><body>Hello U!</body></html>"),
			((("yy", "frag1"),), slob.MIME_HTML, '<h1 name="frag1">Section 1</h1>'),
		]

		self.all_keys = []

		self.data_as_dict = {}

		for k, t, v in self.data:
			if isinstance(k, str):
				k = (k,)  # noqa: PLW2901
			for key in k:
				if isinstance(key, tuple):
					key, fragment = key  # noqa: PLW2901
				else:
					fragment = ""
				self.all_keys.append(key)
				self.data_as_dict[key] = (t, v, fragment)
			writer.add(v.encode(self.blob_encoding), *k, content_type=t)
		self.all_keys.sort()

		writer.finalize()
		self.w = writer

	def test_header(self):
		with slob.MultiFileReader(self.path) as f:
			header = slob.read_header(f)

		for key, value in self.tags.items():
			self.assertEqual(header.tags[key], value)

		self.assertEqual(self.w.encoding, slob.UTF8)
		self.assertEqual(header.encoding, self.w.encoding)

		self.assertEqual(header.compression, self.w.compression)

		for i, content_type in enumerate(header.content_types):
			self.assertEqual(self.w.content_types[content_type], i)

		self.assertEqual(header.blob_count, len(self.data))

	def test_content(self):
		with slob.open(self.path) as r:
			self.assertEqual(len(r), len(self.all_keys))
			self.assertRaises(IndexError, r.__getitem__, len(self.all_keys))
			for i, item in enumerate(r):
				self.assertEqual(item.key, self.all_keys[i])
				content_type, value, fragment = self.data_as_dict[item.key]
				self.assertEqual(item.content_type, content_type)
				self.assertEqual(item.content.decode(self.blob_encoding), value)
				self.assertEqual(item.fragment, fragment)


class TestSort(BaseTest):
	def setUp(self):
		BaseTest.setUp(self)

		self.path = os.path.join(self.tmpdir.name, "test.slob")

		writer = self.create(self.path)
		data = [
			"Ф, ф",
			"Ф ф",
			"Ф",
			"Э",
			"Е е",
			"г",
			"н",
			"ф",
			"а",
			"Ф, Ф",
			"е",
			"Е",
			"Ее",
			"ё",
			"Ё",
			"Её",
			"Е ё",
			"А",
			"э",
			"ы",
		]

		self.data_sorted = sorted(data, key=slob.sortkey(slob.IDENTICAL))

		for k in data:
			v = ";".join(unicodedata.name(c) for c in k)
			writer.add(v.encode("ascii"), k)

		writer.finalize()

		self.r = slob.open(self.path)

	def test_sort_order(self):
		for i in range(len(self.r)):
			self.assertEqual(self.r[i].key, self.data_sorted[i])

	def tearDown(self):
		self.r.close()
		BaseTest.tearDown(self)


class TestSortKey(BaseTest):
	def setUp(self):
		BaseTest.setUp(self)

		self.data = [
			"Ф, ф",
			"Ф ф",
			"Ф",
			"Э",
			"Е е",
			"г",
			"н",
			"ф",
			"а",
			"Ф, Ф",
			"е",
			"Е",
			"Ее",
			"ё",
			"Ё",
			"Её",
			"Е ё",
			"А",
			"э",
			"ы",
		]
		self.data_sorted = [
			"а",
			"А",
			"г",
			"е",
			"Е",
			"ё",
			"Ё",
			"Е е",
			"Ее",
			"Е ё",
			"Её",
			"н",
			"ф",
			"Ф",
			"Ф ф",
			"Ф, ф",
			"Ф, Ф",
			"ы",
			"э",
			"Э",
		]

	def test_sort_order(self):
		for locName in (
			# en_US_POSIX on Mac OS X
			# https://github.com/ilius/pyglossary/issues/458
			"en_US_POSIX",
			"en_US",
			"en_CA",
			"fa_IR.UTF-8",
		):
			icu.Locale.setDefault(icu.Locale(locName))
			slob.sortkey.cache_clear()
			data_sorted = sorted(self.data, key=slob.sortkey(slob.IDENTICAL))
			self.assertEqual(self.data_sorted, data_sorted)


class TestFind(BaseTest):
	def setUp(self):
		BaseTest.setUp(self)

		self.path = os.path.join(self.tmpdir.name, "test.slob")

		writer = self.create(self.path)
		data = [
			"Cc",
			"aA",
			"aa",
			"Aa",
			"Bb",
			"cc",
			"Äā",
			"ăÀ",
			"a\u00a0a",
			"a-a",
			"a\u2019a",
			"a\u2032a",
			"a,a",
			"a a",
		]

		for k in data:
			v = ";".join(unicodedata.name(c) for c in k)
			writer.add(v.encode("ascii"), k)

		writer.finalize()

		self.r = slob.open(self.path)

	def get(self, d, key):
		return [item.content.decode("ascii") for item in d[key]]

	def test_find_identical(self):
		d = self.r.as_dict(slob.IDENTICAL)
		self.assertEqual(
			self.get(d, "aa"),
			["LATIN SMALL LETTER A;LATIN SMALL LETTER A"],
		)
		self.assertEqual(
			self.get(d, "a-a"),
			["LATIN SMALL LETTER A;HYPHEN-MINUS;LATIN SMALL LETTER A"],
		)
		self.assertEqual(
			self.get(d, "aA"),
			["LATIN SMALL LETTER A;LATIN CAPITAL LETTER A"],
		)
		self.assertEqual(
			self.get(d, "Äā"),
			[
				"LATIN CAPITAL LETTER A WITH DIAERESIS;"
				"LATIN SMALL LETTER A WITH MACRON",
			],
		)
		self.assertEqual(
			self.get(d, "a a"),
			["LATIN SMALL LETTER A;SPACE;LATIN SMALL LETTER A"],
		)

	def test_find_quaternary(self):
		d = self.r.as_dict(slob.QUATERNARY)
		self.assertEqual(
			self.get(d, "a\u2032a"),
			["LATIN SMALL LETTER A;PRIME;LATIN SMALL LETTER A"],
		)
		self.assertEqual(
			self.get(d, "a a"),
			[
				"LATIN SMALL LETTER A;SPACE;LATIN SMALL LETTER A",
				"LATIN SMALL LETTER A;NO-BREAK SPACE;LATIN SMALL LETTER A",
			],
		)

	def test_find_tertiary(self):
		d = self.r.as_dict(slob.TERTIARY)
		self.assertEqual(
			self.get(d, "aa"),
			[
				"LATIN SMALL LETTER A;SPACE;LATIN SMALL LETTER A",
				"LATIN SMALL LETTER A;NO-BREAK SPACE;LATIN SMALL LETTER A",
				"LATIN SMALL LETTER A;HYPHEN-MINUS;LATIN SMALL LETTER A",
				"LATIN SMALL LETTER A;COMMA;LATIN SMALL LETTER A",
				"LATIN SMALL LETTER A;RIGHT SINGLE QUOTATION MARK;LATIN SMALL LETTER A",
				"LATIN SMALL LETTER A;PRIME;LATIN SMALL LETTER A",
				"LATIN SMALL LETTER A;LATIN SMALL LETTER A",
			],
		)

	def test_find_secondary(self):
		d = self.r.as_dict(slob.SECONDARY)
		self.assertEqual(
			self.get(d, "aa"),
			[
				"LATIN SMALL LETTER A;SPACE;LATIN SMALL LETTER A",
				"LATIN SMALL LETTER A;NO-BREAK SPACE;LATIN SMALL LETTER A",
				"LATIN SMALL LETTER A;HYPHEN-MINUS;LATIN SMALL LETTER A",
				"LATIN SMALL LETTER A;COMMA;LATIN SMALL LETTER A",
				"LATIN SMALL LETTER A;RIGHT SINGLE QUOTATION MARK;LATIN SMALL LETTER A",
				"LATIN SMALL LETTER A;PRIME;LATIN SMALL LETTER A",
				"LATIN SMALL LETTER A;LATIN SMALL LETTER A",
				"LATIN SMALL LETTER A;LATIN CAPITAL LETTER A",
				"LATIN CAPITAL LETTER A;LATIN SMALL LETTER A",
			],
		)

	def test_find_primary(self):
		d = self.r.as_dict(slob.PRIMARY)

		expected = [
			"LATIN SMALL LETTER A;SPACE;LATIN SMALL LETTER A",
			"LATIN SMALL LETTER A;NO-BREAK SPACE;LATIN SMALL LETTER A",
			"LATIN SMALL LETTER A;HYPHEN-MINUS;LATIN SMALL LETTER A",
			"LATIN SMALL LETTER A;COMMA;LATIN SMALL LETTER A",
			"LATIN SMALL LETTER A;RIGHT SINGLE QUOTATION MARK;LATIN SMALL LETTER A",
			"LATIN SMALL LETTER A;PRIME;LATIN SMALL LETTER A",
			"LATIN SMALL LETTER A;LATIN SMALL LETTER A",
			"LATIN SMALL LETTER A;LATIN CAPITAL LETTER A",
			"LATIN CAPITAL LETTER A;LATIN SMALL LETTER A",
			"LATIN SMALL LETTER A WITH BREVE;LATIN CAPITAL LETTER A WITH GRAVE",
			"LATIN CAPITAL LETTER A WITH DIAERESIS;LATIN SMALL LETTER A WITH MACRON",
		]
		self.assertEqual(
			self.get(d, "aa"),
			expected,
		)

	def tearDown(self):
		self.r.close()
		BaseTest.tearDown(self)


class TestPrefixFind(BaseTest):
	def setUp(self):
		BaseTest.setUp(self)

		self.path = os.path.join(self.tmpdir.name, "test.slob")
		self.data = ["a", "ab", "abc", "abcd", "abcde"]
		writer = self.create(self.path)
		for k in self.data:
			writer.add(k.encode("ascii"), k)
		writer.finalize()

	def test(self):
		with slob.open(self.path) as r:
			for i, k in enumerate(self.data):
				d = r.as_dict(slob.IDENTICAL, len(k))
				self.assertEqual(
					[cast("slob.Blob", v).content.decode("ascii") for v in d[k]],
					self.data[i:],
				)


class TestAlias(BaseTest):
	def setUp(self):
		BaseTest.setUp(self)

		self.path = os.path.join(self.tmpdir.name, "test.slob")

	def test_alias(self):
		too_many_redirects = []
		target_not_found = []

		def observer(event):
			if event.name == "too_many_redirects":
				too_many_redirects.append(event.data)
			elif event.name == "alias_target_not_found":
				target_not_found.append(event.data)

		w = self.create(self.path, observer=observer)
		data = ["z", "b", "q", "a", "u", "g", "p", "n"]
		for k in data:
			v = ";".join(unicodedata.name(c) for c in k)
			w.add(v.encode("ascii"), k)

		w.add_alias("w", "u")
		w.add_alias("small u", "u")
		w.add_alias("y1", "y2")
		w.add_alias("y2", "y3")
		w.add_alias("y3", "z")
		w.add_alias("ZZZ", "YYY")

		w.add_alias("l3", "l1")
		w.add_alias("l1", "l2")
		w.add_alias("l2", "l3")

		w.add_alias("a1", ("a", "a-frag1"))
		w.add_alias("a2", "a1")
		w.add_alias("a3", ("a2", "a-frag2"))

		w.add_alias("g1", "g")
		w.add_alias("g2", ("g1", "g-frag1"))

		w.add_alias("n or p", "n")
		w.add_alias("n or p", "p")

		w.finalize()

		self.assertEqual(too_many_redirects, ["l1", "l2", "l3"])
		self.assertEqual(target_not_found, ["l2", "l3", "l1", "YYY"])

		with slob.open(self.path) as r:
			d = r.as_dict()

			def get(key):
				return [item.content.decode("ascii") for item in d[key]]

			self.assertEqual(get("w"), ["LATIN SMALL LETTER U"])
			self.assertEqual(get("small u"), ["LATIN SMALL LETTER U"])
			self.assertEqual(get("y1"), ["LATIN SMALL LETTER Z"])
			self.assertEqual(get("y2"), ["LATIN SMALL LETTER Z"])
			self.assertEqual(get("y3"), ["LATIN SMALL LETTER Z"])
			self.assertEqual(get("ZZZ"), [])
			self.assertEqual(get("l1"), [])
			self.assertEqual(get("l2"), [])
			self.assertEqual(get("l3"), [])

			self.assertEqual(len(list(d["n or p"])), 2)

			item_a1 = cast("slob.Blob", next(d["a1"]))
			self.assertEqual(item_a1.content, b"LATIN SMALL LETTER A")
			self.assertEqual(item_a1.fragment, "a-frag1")

			item_a2 = cast("slob.Blob", next(d["a2"]))
			self.assertEqual(item_a2.content, b"LATIN SMALL LETTER A")
			self.assertEqual(item_a2.fragment, "a-frag1")

			item_a3 = cast("slob.Blob", next(d["a3"]))
			self.assertEqual(item_a3.content, b"LATIN SMALL LETTER A")
			self.assertEqual(item_a3.fragment, "a-frag1")

			item_g1 = cast("slob.Blob", next(d["g1"]))
			self.assertEqual(item_g1.content, b"LATIN SMALL LETTER G")
			self.assertEqual(item_g1.fragment, "")

			item_g2 = cast("slob.Blob", next(d["g2"]))
			self.assertEqual(item_g2.content, b"LATIN SMALL LETTER G")
			self.assertEqual(item_g2.fragment, "g-frag1")


class TestBlobId(BaseTest):
	def test(self):
		max_i = 2**32 - 1
		max_j = 2**16 - 1
		i_values = [0, max_i] + [random.randint(1, max_i - 1) for _ in range(100)]
		j_values = [0, max_j] + [random.randint(1, max_j - 1) for _ in range(100)]
		for i in i_values:
			for j in j_values:
				self.assertEqual(slob.unmeld_ints(slob.meld_ints(i, j)), (i, j))


class TestMultiFileReader(BaseTest):
	def test_read_all(self):
		fnames = []
		for name in "abcdef":
			path = os.path.join(self.tmpdir.name, name)
			fnames.append(path)
			with slob.fopen(path, "wb") as f:
				f.write(name.encode(slob.UTF8))
		with slob.MultiFileReader(*fnames) as m:
			self.assertEqual(m.read().decode(slob.UTF8), "abcdef")

	def test_seek_and_read(self):
		def mkfile(basename, content):
			part = os.path.join(self.tmpdir.name, basename)
			with slob.fopen(part, "wb") as f:
				f.write(content)
			return part

		content = b"abc\nd\nefgh\nij"
		part1 = mkfile("1", content[:4])
		part2 = mkfile("2", content[4:5])
		part3 = mkfile("3", content[5:])

		with slob.MultiFileReader(part1, part2, part3) as m:
			self.assertEqual(m.size, len(content))
			m.seek(2)
			self.assertEqual(m.read(2), content[2:4])
			m.seek(1)
			self.assertEqual(m.read(len(content) - 2), content[1:-1])
			m.seek(-1, whence=io.SEEK_END)
			self.assertEqual(m.read(10), content[-1:])

			m.seek(4)
			m.seek(-2, whence=io.SEEK_CUR)
			self.assertEqual(m.read(3), content[2:5])


class TestFormatErrors(BaseTest):
	def test_wrong_file_type(self):
		name = os.path.join(self.tmpdir.name, "1")
		with slob.fopen(name, "wb") as f:
			f.write(b"123")
		self.assertRaises(slob.UnknownFileFormat, slob.open, name)

	def test_truncated_file(self):
		name = os.path.join(self.tmpdir.name, "1")

		writer = self.create(name)
		writer.add(b"123", "a")
		writer.add(b"234", "b")
		writer.finalize()

		with slob.fopen(name, "rb") as f:
			all_bytes = f.read()

		with slob.fopen(name, "wb") as f:
			f.write(all_bytes[:-1])

		self.assertRaises(slob.IncorrectFileSize, slob.open, name)

		with slob.fopen(name, "wb") as f:
			f.write(all_bytes)
			f.write(b"\n")

		self.assertRaises(slob.IncorrectFileSize, slob.open, name)


class TestTooLongText(BaseTest):
	def setUp(self):
		BaseTest.setUp(self)
		self.path = os.path.join(self.tmpdir.name, "test.slob")

	def test_too_long(self):
		rejected_keys = []
		rejected_aliases = []
		rejected_alias_targets = []
		rejected_tags = []
		rejected_content_types = []

		def observer(event):
			if event.name == "key_too_long":
				rejected_keys.append(event.data)
			elif event.name == "alias_too_long":
				rejected_aliases.append(event.data)
			elif event.name == "alias_target_too_long":
				rejected_alias_targets.append(event.data)
			elif event.name == "tag_name_too_long":
				rejected_tags.append(event.data)
			elif event.name == "content_type_too_long":
				rejected_content_types.append(event.data)

		long_tag_name = "t" * (slob.MAX_TINY_TEXT_LEN + 1)
		long_tag_value = "v" * (slob.MAX_TINY_TEXT_LEN + 1)
		long_content_type = "T" * (slob.MAX_TEXT_LEN + 1)
		long_key = "c" * (slob.MAX_TEXT_LEN + 1)
		long_frag = "d" * (slob.MAX_TINY_TEXT_LEN + 1)
		key_with_long_frag = ("d", long_frag)
		tag_with_long_name = (long_tag_name, "t3 value")
		tag_with_long_value = ("t1", long_tag_value)
		long_alias = "f" * (slob.MAX_TEXT_LEN + 1)
		alias_with_long_frag = ("i", long_frag)
		long_alias_target = long_key
		long_alias_target_frag = key_with_long_frag

		w = self.create(self.path, observer=observer)
		w.tag(*tag_with_long_value)
		w.tag("t2", "t2 value")
		w.tag(*tag_with_long_name)

		data = ["a", "b", long_key, key_with_long_frag]

		for k in data:
			v = k.encode("ascii") if isinstance(k, str) else "#".join(k).encode("ascii")
			w.add(v, k)

		w.add_alias("e", "a")
		w.add_alias(long_alias, "a")
		w.add_alias(alias_with_long_frag, "a")
		w.add_alias("g", long_alias_target)
		w.add_alias("h", long_alias_target_frag)

		w.add(b"Hello", "hello", content_type=long_content_type)
		w.finalize()

		self.assertEqual(
			rejected_keys,
			[long_key, key_with_long_frag],
		)
		self.assertEqual(
			rejected_aliases,
			[long_alias, alias_with_long_frag],
		)
		self.assertEqual(
			rejected_alias_targets,
			[long_alias_target, long_alias_target_frag],
		)
		self.assertEqual(
			rejected_tags,
			[tag_with_long_name],
		)
		self.assertEqual(
			rejected_content_types,
			[long_content_type],
		)

		with slob.open(self.path) as r:
			self.assertEqual(r.tags["t2"], "t2 value")
			self.assertNotIn(tag_with_long_name[0], r.tags)
			self.assertIn(tag_with_long_value[0], r.tags)
			self.assertEqual(r.tags[tag_with_long_value[0]], "")
			d = r.as_dict()
			self.assertIn("a", d)
			self.assertIn("b", d)
			self.assertNotIn(long_key, d)
			self.assertNotIn(key_with_long_frag[0], d)
			self.assertIn("e", d)
			self.assertNotIn(long_alias, d)
			self.assertNotIn("g", d)

		self.assertRaises(
			ValueError,
			set_tag_value,
			self.path,
			"t1",
			"ы" * 128,
		)


class TestEditTag(BaseTest):
	def setUp(self):
		BaseTest.setUp(self)
		self.path = os.path.join(self.tmpdir.name, "test.slob")
		writer = self.create(self.path)
		writer.tag("a", "123456")
		writer.tag("b", "654321")
		writer.finalize()

	def test_edit_existing_tag(self):
		with slob.open(self.path) as f:
			self.assertEqual(f.tags["a"], "123456")
			self.assertEqual(f.tags["b"], "654321")
		set_tag_value(self.path, "b", "efg")
		set_tag_value(self.path, "a", "xyz")
		with slob.open(self.path) as f:
			self.assertEqual(f.tags["a"], "xyz")
			self.assertEqual(f.tags["b"], "efg")

	def test_edit_nonexisting_tag(self):
		self.assertRaises(TagNotFound, set_tag_value, self.path, "z", "abc")


class TestBinItemNumberLimit(BaseTest):
	def setUp(self):
		BaseTest.setUp(self)
		self.path = os.path.join(self.tmpdir.name, "test.slob")

	def test_writing_more_then_max_number_of_bin_items(self):
		writer = self.create(self.path)
		for _ in range(slob.MAX_BIN_ITEM_COUNT + 2):
			writer.add(b"a", "a")
		self.assertEqual(writer.bin_count, 2)
		writer.finalize()


if __name__ == "__main__":
	unittest.main()
