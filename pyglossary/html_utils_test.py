#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from os.path import join, dirname, abspath
import sys
import unittest


rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from pyglossary.html_utils import unescape_unicode


class UnescapeUnicodeTest(unittest.TestCase):
	def case(self, text, expected):
		actual = unescape_unicode(text)
		self.assertEqual(actual, expected)

	def test(self):
		self.case("&lt;", "&lt;")
		self.case("&gt;", "&gt;")
		self.case("&amp;", "&amp;")
		self.case("&quot;", "&quot;")
		self.case("&#x27;", "&#x27;")

		self.case("&lt;&aacute;&gt;", "&lt;á&gt;")

		self.case("/w&#601;&#720;ki&#331;ti&#720;m/", "/wəːkiŋtiːm/")

		# Babylon dictionaries contain a lot of non-standard entity,
		# references for example, csdot, fllig, nsm, cancer, thlig,
		# tsdot, upslur...
		self.case("&lt;&etilde;", "&lt;ẽ")
		self.case("&lt;&frac13;", "&lt;⅓")
		self.case("&lt;&frac23;", "&lt;⅔")
		self.case("&lt;&itilde;", "&lt;ĩ")
		self.case("&lt;&ldash;", "&lt;–")
		self.case("&lt;&uring;", "&lt;ů")
		self.case("&lt;&utilde;", "&lt;ũ")
		self.case("&lt;&wring;", "&lt;ẘ")
		self.case("&lt;&xfrac13;", "&lt;⅓")
		self.case("&lt;&ycirc;", "&lt;ŷ")
		self.case("&lt;&ygrave;", "&lt;ỳ")
		self.case("&lt;&yring;", "&lt;ẙ")
		self.case("&lt;&ytilde;", "&lt;ỹ")


if __name__ == "__main__":
	unittest.main()
