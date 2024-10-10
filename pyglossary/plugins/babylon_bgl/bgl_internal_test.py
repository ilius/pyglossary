import unittest

from pyglossary.plugins.babylon_bgl.bgl_reader_debug import isASCII


class BglInternalTest(unittest.TestCase):
	def test_isASCII(self):
		f = isASCII
		self.assertEqual(f(""), True)
		self.assertEqual(f("abc"), True)
		self.assertEqual(f("xyz"), True)
		self.assertEqual(f("ABC"), True)
		self.assertEqual(f("XYZ"), True)
		self.assertEqual(f("1234567890"), True)
		self.assertEqual(f("\n\r\t"), True)
		self.assertEqual(f("\x80"), False)
		self.assertEqual(f("abc\x80"), False)
		self.assertEqual(f("abc\xff"), False)
