import gzip
import io
import os
import sys
import tempfile
import unittest
import warnings
from os.path import abspath, dirname

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from pyglossary.plugins.babylon_bgl.bgl_gzip import GzipFile  # noqa: E402


class TestBglGzip(unittest.TestCase):
	def test_write_read_roundtrip(self):
		buf = io.BytesIO()
		with GzipFile(fileobj=buf, mode="wb", filename="sample.txt", mtime=0) as gz:
			self.assertEqual(gz.write(b"hello "), 6)
			self.assertEqual(gz.write(memoryview(b"world")), 5)
			gz.flush()
			self.assertTrue(gz.writable())
			self.assertFalse(gz.readable())
			self.assertTrue(gz.seekable())
			self.assertFalse(gz.closed)
			self.assertRaises(OSError, gz.read, 1)
			self.assertRaises(OSError, gz.read1, 1)
			self.assertRaises(OSError, gz.peek, 1)
			self.assertRaises(OSError, gz.rewind)
			self.assertRaises(OSError, gz.seek, 0)
			with warnings.catch_warnings():
				warnings.simplefilter("ignore", DeprecationWarning)
				self.assertTrue(gz.filename.endswith(".gz"))

		self.assertFalse(buf.closed)
		buf.seek(0)
		with GzipFile(fileobj=buf, mode="rb") as gz:
			self.assertIn("<gzip", repr(gz))
			self.assertTrue(gz.readable())
			self.assertFalse(gz.writable())
			with warnings.catch_warnings():
				warnings.simplefilter("ignore", DeprecationWarning)
				self.assertEqual(gz.filename, gz.name)
			self.assertEqual(gz.peek(1)[:1], b"h")
			self.assertEqual(gz.mtime, 0)
			self.assertEqual(gz.read(0), b"")
			self.assertEqual(gz.read1(3), b"hel")
			self.assertEqual(gz.readline(), b"lo world")
			gz.rewind()
			self.assertEqual(gz.read(2), b"he")
			self.assertEqual(gz.read1(), b"llo world")
			self.assertEqual(gz.seek(0), 0)
			self.assertEqual(gz.read(), b"hello world")
			self.assertEqual(gz.readline(), b"")
			gz.close()
			self.assertTrue(gz.closed)
			gz.close()

	def test_write_seek(self):
		buf = io.BytesIO()
		with GzipFile(fileobj=buf, mode="wb", mtime=0) as gz:
			gz.write(b"hello")
			self.assertEqual(gz.seek(7), 7)
			self.assertEqual(gz.seek(1, io.SEEK_CUR), 8)
			self.assertRaises(ValueError, gz.seek, 0, io.SEEK_END)
			self.assertRaises(OSError, gz.seek, 0)
		buf.seek(0)
		with GzipFile(fileobj=buf, mode="rb") as gz:
			self.assertEqual(gz.read(), b"hello\x00\x00\x00")

	def test_mode_variants(self):
		with self.assertRaises(ValueError):
			GzipFile(fileobj=io.BytesIO(), mode="wt")
		with self.assertRaises(ValueError):
			GzipFile(fileobj=io.BytesIO(), mode="zb")
		with self.assertRaises(OSError):
			GzipFile(fileobj=io.BytesIO(), mode="rb", compresslevel=1).write(b"x")

		buf = io.BytesIO()
		with warnings.catch_warnings():
			warnings.simplefilter("ignore", FutureWarning)
			gz = GzipFile(fileobj=buf, mode="w", mtime=0)
		gz.write(b"data")
		gz.close()
		buf.seek(0)
		with GzipFile(fileobj=buf, mode="r") as gz:
			self.assertEqual(gz.read(), b"data")

	def test_filename_only(self):
		fd, path = tempfile.mkstemp(suffix=".gz")
		os.close(fd)
		try:
			with GzipFile(filename=path, mode="wb", mtime=0) as gz:
				self.assertGreaterEqual(gz.fileno(), 0)
				gz.write(b"file data")
			with GzipFile(filename=path, mode="rb") as gz:
				self.assertEqual(gz.name, path)
				self.assertEqual(gz.read(), b"file data")
		finally:
			os.unlink(path)

	def test_write_header_variants(self):
		for compresslevel, filename in (
			(1, "fast"),
			(5, "normal"),
			(9, "日本"),
		):
			with self.subTest(compresslevel=compresslevel, filename=filename):
				buf = io.BytesIO()
				with GzipFile(
					fileobj=buf,
					mode="wb",
					filename=filename,
					mtime=None,
					compresslevel=compresslevel,
				) as gz:
					gz.write(b"data")
				buf.seek(0)
				with GzipFile(fileobj=buf, mode="rb") as gz:
					self.assertEqual(gz.read(), b"data")

	def test_write_without_mode_warns(self):
		class WriteBuffer(io.BytesIO):
			mode = "wb"

		buf = WriteBuffer()
		with warnings.catch_warnings(record=True) as caught:
			warnings.simplefilter("always")
			gz = GzipFile(fileobj=buf, mtime=0)
		self.assertTrue(any(issubclass(w.category, FutureWarning) for w in caught))
		gz.write(b"data")
		gz.close()

	def test_write_after_close(self):
		buf = io.BytesIO()
		gz = GzipFile(fileobj=buf, mode="wb", mtime=0)
		gz.close()
		self.assertRaises(ValueError, gz.write, b"x")

	def test_write_seek_large(self):
		buf = io.BytesIO()
		with GzipFile(fileobj=buf, mode="wb", mtime=0) as gz:
			gz.seek(2048)
		buf.seek(0)
		with GzipFile(fileobj=buf, mode="rb") as gz:
			self.assertEqual(gz.read(), b"\x00" * 2048)

	def test_read_fileobj_with_non_string_name(self):
		class NamedBuffer(io.BytesIO):
			name = 123

		buf = NamedBuffer(gzip.compress(b"data", mtime=0))
		with GzipFile(fileobj=buf, mode="rb") as gz:
			self.assertEqual(gz.read(), b"data")

	def test_read_chunked_fileobj(self):
		class ChunkedReader:
			def __init__(self, data):
				self._data = data
				self._pos = 0

			def read(self, size=-1):
				if size < 0:
					size = len(self._data) - self._pos
				size = min(size, 4)
				data = self._data[self._pos : self._pos + size]
				self._pos += len(data)
				return data

			def seek(self, pos, whence=0):
				if whence == 0:
					self._pos = pos
				elif whence == 1:
					self._pos += pos
				else:
					self._pos = len(self._data) + pos
				return self._pos

		data = gzip.compress(b"chunked data", mtime=0)
		with GzipFile(fileobj=ChunkedReader(data), mode="rb") as gz:
			self.assertEqual(gz.read(), b"chunked data")

	def test_read_truncated_deflate(self):
		data = gzip.compress(b"some data that is truncated", mtime=0)
		buf = io.BytesIO(data[:-10])
		with GzipFile(fileobj=buf, mode="rb") as gz:
			self.assertRaises(EOFError, gz.read)

	def test_missing_member_header(self):
		buf = io.BytesIO(b"\x1f\x8b\x08")
		with GzipFile(fileobj=buf, mode="rb") as gz:
			self.assertRaises(EOFError, gz.read)

	def test_read_short_header(self):
		buf = io.BytesIO(b"\x1f\x8b")
		with GzipFile(fileobj=buf, mode="rb") as gz:
			self.assertRaises(EOFError, gz.read)


if __name__ == "__main__":
	unittest.main()
