import unittest

from pyglossary.plugins.babylon_bgl.bgl_text import fixImgLinks, wrapResourceLinks
from pyglossary.plugins.babylon_bgl.reader_debug import isASCII


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

	def test_wrapResourceLinks(self):
		resources = frozenset({"ABC123.png", "audio/word.wav"})
		defi = (
			"<IMG src='ABC123.png'>"
			"<a href=\"sound://word.wav\">play</a>"
		)
		wrapped = wrapResourceLinks(defi, resources)
		self.assertIn("\x1eABC123.png\x1f", wrapped)
		self.assertIn("\x1eaudio/word.wav\x1f", wrapped)

	def test_wrapResourceLinks_roundtrip_with_fixImgLinks(self):
		resources = frozenset({"test.png"})
		defi = "<img src='test.png'>"
		wrapped = wrapResourceLinks(defi, resources)
		self.assertEqual(fixImgLinks(wrapped), defi)

	def test_wrapResourceLinks_skips_unknown(self):
		resources = frozenset({"known.png"})
		defi = "<img src='other.png'>"
		self.assertEqual(wrapResourceLinks(defi, resources), defi)
