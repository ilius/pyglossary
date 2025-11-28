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

from pyglossary.plugins.edict2.conv import (
	render_definition_no_links,
	render_definition_with_links,
	render_syllables,
)
from pyglossary.plugins.edict2.pinyin import convert


class PinyinTest(unittest.TestCase):
	@staticmethod
	def render(pinyin: str) -> str:
		pinyin_list, tones = zip(*map(convert, pinyin.split()), strict=False)
		f = BytesIO()
		with ET.htmlfile(f, encoding="utf-8") as hf_:  # noqa: PLR1702
			hf = cast("T_htmlfile", hf_)
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


class DefinitionLinkTest(unittest.TestCase):
	@staticmethod
	def render_no_links(definition: str) -> str:
		f = BytesIO()
		with ET.htmlfile(f, encoding="utf-8") as hf_:
			hf = cast("T_htmlfile", hf_)
			render_definition_no_links(hf, definition=definition)

		return f.getvalue().decode("utf-8")

	@staticmethod
	def render_with_links_simplified(definition: str) -> str:
		f = BytesIO()
		with ET.htmlfile(f, encoding="utf-8") as hf_:
			hf = cast("T_htmlfile", hf_)
			render_definition_with_links(
				hf,
				definition=definition,
				traditional_title=False,
			)

		return f.getvalue().decode("utf-8")

	@staticmethod
	def render_with_links_traditional(definition: str) -> str:
		f = BytesIO()
		with ET.htmlfile(f, encoding="utf-8") as hf_:
			hf = cast("T_htmlfile", hf_)
			render_definition_with_links(
				hf,
				definition=definition,
				traditional_title=True,
			)

		return f.getvalue().decode("utf-8")

	def test_links_created_simplified(self):
		self.assertEqual(
			self.render_with_links_simplified("CL:個|个[ge4],隻|只[zhi1]/"),
			'<li>CL:<a href="bword://个">個|个[ge4]</a>,<a href="bword://只">隻|只[zhi1]</a>/</li>',
		)
		self.assertEqual(
			self.render_with_links_simplified(
				"provincial 解元[jie4 yuan2], metropolitan 會元|会元[hui4 yuan2] and palace 狀元|状元[zhuang4 yuan2]"
			),
			'<li>provincial <a href="bword://解元">解元[jie4 yuan2]</a>, metropolitan <a href="bword://会元">會元|会元[hui4 yuan2]</a> and palace <a href="bword://状元">狀元|状元[zhuang4 yuan2]</a></li>',
		)

	def test_links_created_traditional(self):
		self.assertEqual(
			self.render_with_links_traditional("CL:個|个[ge4],隻|只[zhi1]/"),
			'<li>CL:<a href="bword://個">個|个[ge4]</a>,<a href="bword://隻">隻|只[zhi1]</a>/</li>',
		)
		self.assertEqual(
			self.render_with_links_traditional(
				"provincial 解元[jie4 yuan2], metropolitan 會元|会元[hui4 yuan2] and palace 狀元|状元[zhuang4 yuan2]"
			),
			'<li>provincial <a href="bword://解元">解元[jie4 yuan2]</a>, metropolitan <a href="bword://會元">會元|会元[hui4 yuan2]</a> and palace <a href="bword://狀元">狀元|状元[zhuang4 yuan2]</a></li>',
		)

	def test_no_links(self):
		for defn in (
			"CL:個|个[ge4],隻|只[zhi1]/",
			"provincial 解元[jie4 yuan2], metropolitan 會元|会元[hui4 yuan2] and palace 狀元|状元[zhuang4 yuan2]",
		):
			self.assertEqual(self.render_no_links(defn), f"<li>{defn}</li>")


if __name__ == "__main__":
	unittest.main()
