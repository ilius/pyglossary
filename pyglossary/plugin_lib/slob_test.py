#!/usr/bin/env python3
import sys
import os
from os.path import dirname, abspath
import unittest
import random
import unicodedata
import logging
import tempfile

rootDir = dirname(dirname(dirname(abspath(__file__))))
sys.path.insert(0, rootDir)

from pyglossary.plugin_lib.slob import *
from pyglossary.core_test import MockLogHandler


mockLog = MockLogHandler()
log = logging.getLogger("pyglossary")
log.addHandler(mockLog)


class BaseTest(unittest.TestCase):
	def _observer(self, event: "slob.WriterEvent"):
		log.info(f"slob: {event.name}{': ' + event.data if event.data else ''}")
		# self._writers = []

	def create(self, *args, observer=None, **kwargs):
		if observer is None:
			observer = self._observer
		w = Writer(*args, observer=observer, **kwargs)
		# self._writers.append(w)
		return w


class TestReadWrite(BaseTest):

	def setUp(self):

		self.tmpdir = tempfile.TemporaryDirectory(prefix='test')
		self.path = os.path.join(self.tmpdir.name, 'test.slob')

		with self.create(self.path) as w:

			self.tags = {
				'a': 'abc',
				'bb': 'xyz123',
				'ccc': 'lkjlk',
			}
			for name, value in self.tags.items():
				w.tag(name, value)

			self.tag2 = 'bb', 'xyz123'

			self.blob_encoding = 'ascii'

			self.data = [
				(('c', 'cc', 'ccc'), MIME_TEXT, 'Hello C 1'),
				('a', MIME_TEXT, 'Hello A 12'),
				('z', MIME_TEXT, 'Hello Z 123'),
				('b', MIME_TEXT, 'Hello B 1234'),
				('d', MIME_TEXT, 'Hello D 12345'),
				('uuu', MIME_HTML, '<html><body>Hello U!</body></html>'),
				((('yy', 'frag1'),), MIME_HTML, '<h1 name="frag1">Section 1</h1>'),
			]

			self.all_keys = []

			self.data_as_dict = {}

			for k, t, v in self.data:
				if isinstance(k, str):
					k = (k,)
				for key in k:
					if isinstance(key, tuple):
						key, fragment = key
					else:
						fragment = ''
					self.all_keys.append(key)
					self.data_as_dict[key] = (t, v, fragment)
				w.add(v.encode(self.blob_encoding), *k, content_type=t)
			self.all_keys.sort()

		self.w = w

	def test_header(self):
		with MultiFileReader(self.path) as f:
			header = read_header(f)

		for key, value in self.tags.items():
			self.assertEqual(header.tags[key], value)

		self.assertEqual(self.w.encoding, UTF8)
		self.assertEqual(header.encoding, self.w.encoding)

		self.assertEqual(header.compression, self.w.compression)

		for i, content_type in enumerate(header.content_types):
			self.assertEqual(self.w.content_types[content_type], i)

		self.assertEqual(header.blob_count, len(self.data))

	def test_content(self):
		with open(self.path) as r:
			self.assertEqual(len(r), len(self.all_keys))
			self.assertRaises(IndexError, r.__getitem__, len(self.all_keys))
			for i, item in enumerate(r):
				self.assertEqual(item.key, self.all_keys[i])
				content_type, value, fragment = self.data_as_dict[item.key]
				self.assertEqual(
					item.content_type, content_type)
				self.assertEqual(
					item.content.decode(self.blob_encoding), value)
				self.assertEqual(
					item.fragment, fragment)

	def tearDown(self):
		self.tmpdir.cleanup()


class TestSort(BaseTest):
	def setUp(self):
		self.tmpdir = tempfile.TemporaryDirectory(prefix='test')
		self.path = os.path.join(self.tmpdir.name, 'test.slob')

		with self.create(self.path) as w:
			data = [
				'Ф, ф',
				'Ф ф',
				'Ф',
				'Э',
				'Е е',
				'г',
				'н',
				'ф',
				'а',
				'Ф, Ф',
				'е',
				'Е',
				'Ее',
				'ё',
				'Ё',
				'Её',
				'Е ё',
				'А',
				'э',
				'ы'
			]

			self.data_sorted = sorted(data, key=sortkey(IDENTICAL))

			for k in data:
				v = ';'.join(unicodedata.name(c) for c in k)
				w.add(v.encode('ascii'), k)

		self.r = open(self.path)

	def test_sort_order(self):
		for i in range(len(self.r)):
			self.assertEqual(self.r[i].key, self.data_sorted[i])

	def tearDown(self):
		self.r.close()
		self.tmpdir.cleanup()


class TestFind(BaseTest):

	def setUp(self):

		self.tmpdir = tempfile.TemporaryDirectory(prefix='test')
		self.path = os.path.join(self.tmpdir.name, 'test.slob')

		with self.create(self.path) as w:
			data = [
				'Cc', 'aA', 'aa', 'Aa', 'Bb', 'cc', 'Äā', 'ăÀ',
				'a\u00A0a', 'a-a', 'a\u2019a', 'a\u2032a', 'a,a', 'a a',
			]

			for k in data:
				v = ';'.join(unicodedata.name(c) for c in k)
				w.add(v.encode('ascii'), k)

		self.r = open(self.path)

	def get(self, d, key):
		return list(item.content.decode('ascii') for item in d[key])

	def test_find_identical(self):
		d = self.r.as_dict(IDENTICAL)
		self.assertEqual(
			self.get(d, 'aa'),
			['LATIN SMALL LETTER A;LATIN SMALL LETTER A'])
		self.assertEqual(
			self.get(d, 'a-a'),
			['LATIN SMALL LETTER A;HYPHEN-MINUS;LATIN SMALL LETTER A'])
		self.assertEqual(
			self.get(d, 'aA'),
			['LATIN SMALL LETTER A;LATIN CAPITAL LETTER A'])
		self.assertEqual(
			self.get(d, 'Äā'),
			[
				'LATIN CAPITAL LETTER A WITH DIAERESIS;'
				'LATIN SMALL LETTER A WITH MACRON',
			],
		)
		self.assertEqual(
			self.get(d, 'a a'),
			['LATIN SMALL LETTER A;SPACE;LATIN SMALL LETTER A'])

	def test_find_quaternary(self):
		d = self.r.as_dict(QUATERNARY)
		self.assertEqual(
			self.get(d, 'a\u2032a'),
			['LATIN SMALL LETTER A;PRIME;LATIN SMALL LETTER A'])
		self.assertEqual(
			self.get(d, 'a a'),
			[
				'LATIN SMALL LETTER A;SPACE;LATIN SMALL LETTER A',
				'LATIN SMALL LETTER A;NO-BREAK SPACE;LATIN SMALL LETTER A',
			],
		)

	def test_find_tertiary(self):
		d = self.r.as_dict(TERTIARY)
		self.assertEqual(
			self.get(d, 'aa'),
			[
				'LATIN SMALL LETTER A;SPACE;LATIN SMALL LETTER A',
				'LATIN SMALL LETTER A;NO-BREAK SPACE;LATIN SMALL LETTER A',
				'LATIN SMALL LETTER A;HYPHEN-MINUS;LATIN SMALL LETTER A',
				'LATIN SMALL LETTER A;COMMA;LATIN SMALL LETTER A',
				'LATIN SMALL LETTER A;RIGHT SINGLE QUOTATION MARK;LATIN SMALL LETTER A',
				'LATIN SMALL LETTER A;PRIME;LATIN SMALL LETTER A',
				'LATIN SMALL LETTER A;LATIN SMALL LETTER A',
			],
		)

	def test_find_secondary(self):
		d = self.r.as_dict(SECONDARY)
		self.assertEqual(
			self.get(d, 'aa'),
			[
				'LATIN SMALL LETTER A;SPACE;LATIN SMALL LETTER A',
				'LATIN SMALL LETTER A;NO-BREAK SPACE;LATIN SMALL LETTER A',
				'LATIN SMALL LETTER A;HYPHEN-MINUS;LATIN SMALL LETTER A',
				'LATIN SMALL LETTER A;COMMA;LATIN SMALL LETTER A',
				'LATIN SMALL LETTER A;RIGHT SINGLE QUOTATION MARK;LATIN SMALL LETTER A',
				'LATIN SMALL LETTER A;PRIME;LATIN SMALL LETTER A',
				'LATIN SMALL LETTER A;LATIN SMALL LETTER A',
				'LATIN SMALL LETTER A;LATIN CAPITAL LETTER A',
				'LATIN CAPITAL LETTER A;LATIN SMALL LETTER A',
			],
		)

	def test_find_primary(self):
		d = self.r.as_dict(PRIMARY)

		self.assertEqual(
			self.get(d, 'aa'),
			[
				'LATIN SMALL LETTER A;SPACE;LATIN SMALL LETTER A',
				'LATIN SMALL LETTER A;NO-BREAK SPACE;LATIN SMALL LETTER A',
				'LATIN SMALL LETTER A;HYPHEN-MINUS;LATIN SMALL LETTER A',
				'LATIN SMALL LETTER A;COMMA;LATIN SMALL LETTER A',
				'LATIN SMALL LETTER A;RIGHT SINGLE QUOTATION MARK;LATIN SMALL LETTER A',
				'LATIN SMALL LETTER A;PRIME;LATIN SMALL LETTER A',
				'LATIN SMALL LETTER A;LATIN SMALL LETTER A',
				'LATIN SMALL LETTER A;LATIN CAPITAL LETTER A',
				'LATIN CAPITAL LETTER A;LATIN SMALL LETTER A',
				'LATIN SMALL LETTER A WITH BREVE;LATIN CAPITAL LETTER A WITH GRAVE',
				'LATIN CAPITAL LETTER A WITH DIAERESIS;LATIN SMALL LETTER A WITH MACRON',
			],
		)

	def tearDown(self):
		self.r.close()
		self.tmpdir.cleanup()


class TestPrefixFind(BaseTest):
	def setUp(self):
		self.tmpdir = tempfile.TemporaryDirectory(prefix='test')
		self.path = os.path.join(self.tmpdir.name, 'test.slob')
		self.data = ['a', 'ab', 'abc', 'abcd', 'abcde']
		with self.create(self.path) as w:
			for k in self.data:
				w.add(k.encode('ascii'), k)

	def tearDown(self):
		self.tmpdir.cleanup()

	def test(self):
		with open(self.path) as r:
			for i, k in enumerate(self.data):
				d = r.as_dict(IDENTICAL, len(k))
				self.assertEqual(
					[v.content.decode('ascii') for v in d[k]],
					self.data[i:],
				)


class TestAlias(BaseTest):
	def setUp(self):
		self.tmpdir = tempfile.TemporaryDirectory(prefix='test')
		self.path = os.path.join(self.tmpdir.name, 'test.slob')

	def tearDown(self):
		self.tmpdir.cleanup()

	def test_alias(self):
		too_many_redirects = []
		target_not_found = []

		def observer(event):
			if event.name == 'too_many_redirects':
				too_many_redirects.append(event.data)
			elif event.name == 'alias_target_not_found':
				target_not_found.append(event.data)

		with self.create(self.path, observer=observer) as w:
			data = ['z', 'b', 'q', 'a', 'u', 'g', 'p', 'n']
			for k in data:
				v = ';'.join(unicodedata.name(c) for c in k)
				w.add(v.encode('ascii'), k)

			w.add_alias('w', 'u')
			w.add_alias('y1', 'y2')
			w.add_alias('y2', 'y3')
			w.add_alias('y3', 'z')
			w.add_alias('ZZZ', 'YYY')

			w.add_alias('l3', 'l1')
			w.add_alias('l1', 'l2')
			w.add_alias('l2', 'l3')

			w.add_alias('a1', ('a', 'a-frag1'))
			w.add_alias('a2', 'a1')
			w.add_alias('a3', ('a2', 'a-frag2'))

			w.add_alias('g1', 'g')
			w.add_alias('g2', ('g1', 'g-frag1'))

		self.assertEqual(too_many_redirects, ['l1', 'l2', 'l3'])
		self.assertEqual(target_not_found, ['l2', 'l3', 'l1', 'YYY'])

		with open(self.path) as r:
			d = r.as_dict()

			def get(key):
				return [
					item.content.decode('ascii')
					for item in d[key]
				]

			self.assertEqual(get('w'), ['LATIN SMALL LETTER U'])
			self.assertEqual(get('y1'), ['LATIN SMALL LETTER Z'])
			self.assertEqual(get('y2'), ['LATIN SMALL LETTER Z'])
			self.assertEqual(get('y3'), ['LATIN SMALL LETTER Z'])
			self.assertEqual(get('ZZZ'), [])
			self.assertEqual(get('l1'), [])
			self.assertEqual(get('l2'), [])
			self.assertEqual(get('l3'), [])

			item_a1 = next(d['a1'])
			self.assertEqual(item_a1.content, b'LATIN SMALL LETTER A')
			self.assertEqual(item_a1.fragment, 'a-frag1')

			item_a2 = next(d['a2'])
			self.assertEqual(item_a2.content, b'LATIN SMALL LETTER A')
			self.assertEqual(item_a2.fragment, 'a-frag1')

			item_a3 = next(d['a3'])
			self.assertEqual(item_a3.content, b'LATIN SMALL LETTER A')
			self.assertEqual(item_a3.fragment, 'a-frag1')

			item_g1 = next(d['g1'])
			self.assertEqual(item_g1.content, b'LATIN SMALL LETTER G')
			self.assertEqual(item_g1.fragment, '')

			item_g2 = next(d['g2'])
			self.assertEqual(item_g2.content, b'LATIN SMALL LETTER G')
			self.assertEqual(item_g2.fragment, 'g-frag1')


class TestBlobId(BaseTest):
	def test(self):
		max_i = 2**32 - 1
		max_j = 2**16 - 1
		i_values = [0, max_i] + [
			random.randint(1, max_i - 1)
			for _ in range(100)
		]
		j_values = [0, max_j] + [
			random.randint(1, max_j - 1)
			for _ in range(100)
		]
		for i in i_values:
			for j in j_values:
				self.assertEqual(unmeld_ints(meld_ints(i, j)), (i, j))


class TestMultiFileReader(BaseTest):
	def setUp(self):
		self.tmpdir = tempfile.TemporaryDirectory(prefix='test')

	def tearDown(self):
		self.tmpdir.cleanup()

	def test_read_all(self):
		fnames = []
		for name in 'abcdef':
			path = os.path.join(self.tmpdir.name, name)
			fnames.append(path)
			with fopen(path, 'wb') as f:
				f.write(name.encode(UTF8))
		with MultiFileReader(fnames) as m:
			self.assertEqual(m.read().decode(UTF8), 'abcdef')

	def test_seek_and_read(self):
		def mkfile(basename, content):
			part = os.path.join(self.tmpdir.name, basename)
			with fopen(part, 'wb') as f:
				f.write(content)
			return part

		content = b'abc\nd\nefgh\nij'
		part1 = mkfile('1', content[:4])
		part2 = mkfile('2', content[4:5])
		part3 = mkfile('3', content[5:])

		with MultiFileReader(part1, part2, part3) as m:
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
	def setUp(self):
		self.tmpdir = tempfile.TemporaryDirectory(prefix='test')

	def tearDown(self):
		self.tmpdir.cleanup()

	def test_wrong_file_type(self):
		name = os.path.join(self.tmpdir.name, '1')
		with fopen(name, 'wb') as f:
			f.write(b'123')
		self.assertRaises(UnknownFileFormat, open, name)

	def test_truncated_file(self):
		name = os.path.join(self.tmpdir.name, '1')

		with self.create(name) as f:
			f.add(b'123', 'a')
			f.add(b'234', 'b',)

		with fopen(name, 'rb') as f:
			all_bytes = f.read()

		with fopen(name, 'wb') as f:
			f.write(all_bytes[:-1])

		self.assertRaises(IncorrectFileSize, open, name)

		with fopen(name, 'wb') as f:
			f.write(all_bytes)
			f.write(b'\n')

		self.assertRaises(IncorrectFileSize, open, name)


class TestFindParts(BaseTest):
	def setUp(self):
		self.tmpdir = tempfile.TemporaryDirectory(prefix='test')

	def tearDown(self):
		self.tmpdir.cleanup()

	def test_find_parts(self):
		names = [
			os.path.join(self.tmpdir.name, name)
			for name in ('abc-1', 'abc-2', 'abc-3')
		]
		for name in names:
			with fopen(name, 'wb'):
				pass
		parts = find_parts(os.path.join(self.tmpdir.name, 'abc'))
		self.assertEqual(names, parts)


class TestTooLongText(BaseTest):
	def setUp(self):
		self.tmpdir = tempfile.TemporaryDirectory(prefix='test')
		self.path = os.path.join(self.tmpdir.name, 'test.slob')

	def tearDown(self):
		self.tmpdir.cleanup()

	def test_too_long(self):
		rejected_keys = []
		rejected_aliases = []
		rejected_alias_targets = []
		rejected_tags = []
		rejected_content_types = []

		def observer(event):
			if event.name == 'key_too_long':
				rejected_keys.append(event.data)
			elif event.name == 'alias_too_long':
				rejected_aliases.append(event.data)
			elif event.name == 'alias_target_too_long':
				rejected_alias_targets.append(event.data)
			elif event.name == 'tag_name_too_long':
				rejected_tags.append(event.data)
			elif event.name == 'content_type_too_long':
				rejected_content_types.append(event.data)

		long_tag_name = 't' * (MAX_TINY_TEXT_LEN + 1)
		long_tag_value = 'v' * (MAX_TINY_TEXT_LEN + 1)
		long_content_type = 'T' * (MAX_TEXT_LEN + 1)
		long_key = 'c' * (MAX_TEXT_LEN + 1)
		long_frag = 'd' * (MAX_TINY_TEXT_LEN + 1)
		key_with_long_frag = ('d', long_frag)
		tag_with_long_name = (long_tag_name, 't3 value')
		tag_with_long_value = ('t1', long_tag_value)
		long_alias = 'f' * (MAX_TEXT_LEN + 1)
		alias_with_long_frag = ('i', long_frag)
		long_alias_target = long_key
		long_alias_target_frag = key_with_long_frag

		with self.create(self.path, observer=observer) as w:

			w.tag(*tag_with_long_value)
			w.tag('t2', 't2 value')
			w.tag(*tag_with_long_name)

			data = ['a', 'b', long_key, key_with_long_frag]

			for k in data:
				if isinstance(k, str):
					v = k.encode('ascii')
				else:
					v = '#'.join(k).encode('ascii')
				w.add(v, k)

			w.add_alias('e', 'a')
			w.add_alias(long_alias, 'a')
			w.add_alias(alias_with_long_frag, 'a')
			w.add_alias('g', long_alias_target)
			w.add_alias('h', long_alias_target_frag)

			w.add(b'Hello', 'hello', content_type=long_content_type)

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

		with open(self.path) as r:
			self.assertEqual(r.tags['t2'], 't2 value')
			self.assertFalse(tag_with_long_name[0] in r.tags)
			self.assertTrue(tag_with_long_value[0] in r.tags)
			self.assertEqual(r.tags[tag_with_long_value[0]], '')
			d = r.as_dict()
			self.assertTrue('a' in d)
			self.assertTrue('b' in d)
			self.assertFalse(long_key in d)
			self.assertFalse(key_with_long_frag[0] in d)
			self.assertTrue('e' in d)
			self.assertFalse(long_alias in d)
			self.assertFalse('g' in d)

		self.assertRaises(
			ValueError,
			set_tag_value,
			self.path,
			't1',
			'ы' * 128,
		)


class TestEditTag(BaseTest):
	def setUp(self):
		self.tmpdir = tempfile.TemporaryDirectory(prefix='test')
		self.path = os.path.join(self.tmpdir.name, 'test.slob')
		with self.create(self.path) as w:
			w.tag('a', '123456')
			w.tag('b', '654321')

	def tearDown(self):
		self.tmpdir.cleanup()

	def test_edit_existing_tag(self):
		with open(self.path) as f:
			self.assertEqual(f.tags['a'], '123456')
			self.assertEqual(f.tags['b'], '654321')
		set_tag_value(self.path, 'b', 'efg')
		set_tag_value(self.path, 'a', 'xyz')
		with open(self.path) as f:
			self.assertEqual(f.tags['a'], 'xyz')
			self.assertEqual(f.tags['b'], 'efg')

	def test_edit_nonexisting_tag(self):
		self.assertRaises(TagNotFound, set_tag_value, self.path, 'z', 'abc')


class TestBinItemNumberLimit(BaseTest):
	def setUp(self):
		self.tmpdir = tempfile.TemporaryDirectory(prefix='test')
		self.path = os.path.join(self.tmpdir.name, 'test.slob')

	def tearDown(self):
		self.tmpdir.cleanup()

	def test_writing_more_then_max_number_of_bin_items(self):
		with self.create(self.path) as w:
			for _ in range(MAX_BIN_ITEM_COUNT + 2):
				w.add(b'a', 'a')
			self.assertEqual(w.bin_count, 2)


if __name__ == '__main__':
	unittest.main()
