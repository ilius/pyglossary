#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from os.path import join, dirname, abspath
import sys
import unittest


rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from pyglossary.html_utils import *


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
		self.case("&#160;", "&#160;")
		self.case("&nbsp;", "&nbsp;")

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


def benchmark_main():
	import timeit
	from random import choice
	from english_words import english_words_set
	english_words_list = list(english_words_set)
	textList = []

	for i in range(20):
		text = ""
		for j in range(10):
			text += choice(english_words_list) + " "
		textList.append(text)

	print("avg length:", sum(len(text) for text in textList) / len(textList))

	def run_benchmark1():
		for text in textList:
			unescape_unicode(text)

	print("benchmark 1:", timeit.timeit("run_benchmark1()", globals=locals()))


if __name__ == "__main__":
	if "-b" in sys.argv:
		benchmark_main()
	else:
		unittest.main()
