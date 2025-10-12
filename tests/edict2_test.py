from __future__ import annotations

import sys
import unittest
from io import BytesIO
from os.path import abspath, dirname
from typing import TYPE_CHECKING, cast

import lxml.html
from lxml import etree as ET

if TYPE_CHECKING:
	from pyglossary.lxml_types import T_htmlfile

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from pyglossary.plugins.edict2.conv import render_syllables
from pyglossary.plugins.edict2.pinyin import convert


class PinyinTest(unittest.TestCase):
	@staticmethod
	def render(pinyin: str) -> str:
		pinyin_list, tones = zip(*map(convert, pinyin.split()), strict=False)
		f = BytesIO()
		with ET.htmlfile(f, encoding="utf-8") as _hf:  # noqa: PLR1702
			hf = cast("T_htmlfile", _hf)
			render_syllables(hf, pinyin_list, tones)

		result = f.getvalue().decode("utf-8")

		# remove html tags
		return lxml.html.fromstring(result).text_content()

	def test_pinyin_names(self):
		self.assertEqual(self.render("Chang2 an1"), "Cháng'ān")
		self.assertEqual(self.render("Sun1 Zhong1 shan1"), "Sūn Zhōngshān")
		self.assertEqual(self.render("A1 Q Zheng4 zhuan4"), "ĀQ Zhèngzhuàn")
		self.assertEqual(self.render("Q tan2"), "Qtán")
		self.assertEqual(self.render("E1 mi2 tuo2 Fo2"), "Ēmítuó Fó")

	def test_pinyin_apostrophes(self):
		self.assertEqual(self.render("qi3 e2"), "qǐ'é")
		self.assertEqual(self.render("e2"), "é")
		self.assertEqual(self.render("Li3 An1"), "Lǐ Ān")

	def test_pinyin_umlaut_u(self):
		self.assertEqual(self.render("gui1 nü"), "guīnü")
		self.assertEqual(self.render("hu1 lüe4"), "hūlüè")


if __name__ == "__main__":
	unittest.main()
