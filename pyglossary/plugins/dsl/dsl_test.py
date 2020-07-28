# -*- coding: utf-8 -*-
#
# Copyright © 2016 Ratijas <ratijas.t@me.com>
# Copyright © 2016-2017 Saeed Rasooli <saeed.gnu@gmail.com>
#
# This program is a free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# You can get a copy of GNU General Public License along this program
# But you can always get it from http://www.gnu.org/licenses/gpl.txt
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
"""
test everything.
"""


import unittest

import os
from os.path import dirname, realpath
import sys
from functools import partial

rootDir = dirname(dirname(dirname(dirname(realpath(__file__)))))
sys.path.insert(0, rootDir)

from pyglossary.plugins.dsl import layer, tag
from pyglossary.plugins.dsl.main import (
	process_closing_tags,
	DSLParser,
	BRACKET_L,
	BRACKET_R,
)

tag_i = tag.Tag("i", "i")
tag_m = tag.Tag("m1", "m")
tag_p = tag.Tag("p", "p")
tag_s = tag.Tag("s", "s")


def parse(line, tags=None):
	"""parse DSL markup.

	WARNING!
	`parse` function is not optimal because it creates new parser instance
	on each call.
	consider cache one [per thread] instance of DSLParser in your code.
	"""
	if tags:
		parser = DSLParser(tags)
	else:
		parser = DSLParser()
	return parser.parse(line)


class LayerTestCase(unittest.TestCase):
	def setUp(self):
		pass

	def test_new_layer(self):
		stack = []
		lay = layer.Layer(stack)
		self.assertEqual(1, len(stack))
		self.assertEqual(lay, stack[0])

	def test_was_opened_AND_close_tags(self):
		stack = []
		l1, l2 = layer.Layer(stack), layer.Layer(stack)
		l1.text = "..."
		l2.tags, l2.text = {tag_i}, ",,,"

		self.assertTrue(tag.was_opened(stack, tag_i))
		self.assertFalse(tag.was_opened(stack, tag.Tag("c green", "c")))

		layer.close_tags(stack, {tag_i}, len(stack) - 1)

		expected = []
		lay = layer.Layer(expected)
		lay.text = "...[i],,,[/i]"
		self.assertEqual(expected, stack)

	def test_close_layer(self):
		stack = []
		l1, l2, l3 = layer.Layer(stack), layer.Layer(stack), layer.Layer(stack)
		l1.tags, l1.text = {tag_m}, "..."
		l2.tags, l2.text = {tag_i}, ",,,"
		l3.tags, l3.text = {tag_p, tag_s}, "+++"

		expected = []
		l1, l2 = layer.Layer(expected), layer.Layer(expected)
		l1.tags, l1.text = {tag_m}, "..."
		l2.tags = {tag_i}
		l2.text = f",,,[{tag_p.opening}][{tag_s.opening}]" \
			f"+++[/{tag_s.closing}][/{tag_p.closing}]"

		layer.close_layer(stack)
		self.assertEqual(expected, stack)


class CanonicalOrderTestCase(unittest.TestCase):
	def setUp(self):
		pass

	def test_no_tags(self):
		tags = {}
		expected = []
		result = tag.canonical_order(tags)
		self.assertEqual(expected, result)

	def test_one_tag_not_predefined(self):
		tags = {tag_p}
		expected = [tag_p]
		result = tag.canonical_order(tags)
		self.assertEqual(expected, result)

	def test_one_tag_predefined(self):
		tags = {tag_i}
		expected = [tag_i]
		result = tag.canonical_order(tags)
		self.assertEqual(expected, result)

	def test_many_tags_not_predefined(self):
		tags = {tag_p, tag_s}
		expected = [tag_p, tag_s]
		result = tag.canonical_order(tags)
		self.assertEqual(expected, result)

	def test_many_tags_predefined(self):
		tags = {tag_m, tag_p}
		expected = [tag_m, tag_p]
		result = tag.canonical_order(tags)
		self.assertEqual(expected, result)

	def test_many_tags_mixed(self):
		tags = {tag_m, tag_i, tag_s, tag_p}
		expected = [tag_m, tag_i, tag_p, tag_s]
		result = tag.canonical_order(tags)
		self.assertEqual(expected, result)


class ProcessClosingTagsTestCase(unittest.TestCase):
	def setUp(self):
		pass

	def test_index_of_layer_containing_tag(self):
		stack = []
		l1, l2, l3 = layer.Layer(stack), layer.Layer(stack), layer.Layer(stack)
		l1.tags, l1.text = {tag_m}, "..."
		l2.tags, l2.text = {tag_i, tag_s}, ",,,"
		l3.tags, l3.text = {tag_p}, "---"

		fn = partial(tag.index_of_layer_containing_tag, stack)
		self.assertEqual(0, fn(tag_m.closing))
		self.assertEqual(1, fn(tag_i.closing))
		self.assertEqual(1, fn(tag_s.closing))
		self.assertEqual(2, fn(tag_p.closing))

	def test_close_one(self):
		stack = []
		l1, l2 = layer.Layer(stack), layer.Layer(stack)
		l1.tags, l1.text = (), "..."
		l2.tags, l2.text = {tag_p}, ",,,"

		expected = []
		lay = layer.Layer(expected)
		lay.text = f"...[{tag_p.opening}],,,[/{tag_p.closing}]"
		lay.tags = ()

		closings = {tag_p.closing}
		process_closing_tags(stack, closings)
		self.assertEqual(expected, stack)


class PutBracketsAwayTestCase(unittest.TestCase):
	def setUp(self):
		tags = frozenset({
			"b",
			"'",
			"c",
			"i",
			"sup",
			"sub",
			"ex",
			"p",
			"*",
			("m", r"\d"),
		})
		parser = DSLParser(tags)
		self.put_brackets_away = parser.put_brackets_away

	def testStandaloneLeftEscapedAtTheBeginning(self):
		before = "[..."
		after = f"{BRACKET_L}..."
		self.assertEqual(after, self.put_brackets_away(before))

	def testStandaloneRightEscapedAtTheBeginning(self):
		before = "]..."
		after = f"{BRACKET_R}..."
		self.assertEqual(after, self.put_brackets_away(before))

	def testStandaloneLeftEscaped(self):
		before = r"...\[,,,"
		after = fr"...\{BRACKET_L},,,"
		self.assertEqual(after, self.put_brackets_away(before))

	def testStandaloneRightEscaped(self):
		before = r"...\],,,"
		after = fr"...\{BRACKET_R},,,"
		self.assertEqual(after, self.put_brackets_away(before))

	def testStandaloneLeftNonEscaped(self):
		before = "...[,,,"
		after = f"...{BRACKET_L},,,"
		self.assertEqual(after, self.put_brackets_away(before))

	def testStandaloneRightNonEscaped(self):
		before = "...],,,"
		after = f"...{BRACKET_R},,,"
		self.assertEqual(after, self.put_brackets_away(before))

	def testStandaloneLeftNonEscapedBeforeTagName(self):
		before = "...[p ,,,"
		after = f"...{BRACKET_L}p ,,,"
		self.assertEqual(after, self.put_brackets_away(before))

	def testStandaloneRightNonEscapedAfterTagName(self):
		before = "c]..."
		after = f"c{BRACKET_R}..."
		self.assertEqual(after, self.put_brackets_away(before))

	def testPairEscaped(self):
		before = r"...\[the\],,,"
		after = fr"...\{BRACKET_L}the\{BRACKET_R},,,"
		self.assertEqual(after, self.put_brackets_away(before))

	def testPairEscapedAroundTagName(self):
		before = r"...\[i\],,,"
		after = fr"...\{BRACKET_L}i\{BRACKET_R},,,"
		self.assertEqual(after, self.put_brackets_away(before))

	def testPairEscapedAroundClosingTagName(self):
		before = r"...\[/i\],,,"
		after = fr"...\{BRACKET_L}/i\{BRACKET_R},,,"
		self.assertEqual(after, self.put_brackets_away(before))

	def testMixed(self):
		L, R = BRACKET_L, BRACKET_R
		before = r"[i]...\[on \]\[the] to[p][/i]"
		after = fr"[i]...\{L}on \{R}\{L}the{R} to[p][/i]"
		self.assertEqual(after, self.put_brackets_away(before))

	def testEverythingEscaped(self):
		before = r" change it to \[b\]...\[c\]...\[/c\]\[/b\]\[c\]...\[/c\]"
		after = before
		self.assertEqual(after, parse(before))


class DSLParserTestCase(unittest.TestCase):
	def setUp(self):
		self.split_join = lambda x: DSLParser.join_paragraphs(
			*DSLParser.split_line_by_paragraphs(x))

	def testStartsWithStandaloneClosed(self):
		before = """[/p]..."""
		after = """..."""
		self.assertEqual(after, parse(before))

	def testStandaloneClosedAtTheBeginning(self):
		before = """...[/p],,,"""
		after = """...,,,"""
		self.assertEqual(after, parse(before))

	def testStandaloneClosedAtTheBeginningBeforeMarkup(self):
		before = """...[/p],,,[i][b]+++[/b][/i]---"""
		after = """...,,,[i][b]+++[/b][/i]---"""
		self.assertEqual(after, parse(before))

	def testEndsWithStandaloneOpened(self):
		before = """...[i]"""
		after = """..."""
		self.assertEqual(after, parse(before))

	def testStandaloneOpenedAtTheEnd(self):
		before = """...[i],,,"""
		after = """...,,,"""
		self.assertEqual(after, parse(before))

	def testStandaloneOpenedAtTheEndAfterMarkup(self):
		before = """...[i][b],,,[/b][/i]+++[i]---"""
		after = """...[i][b],,,[/b][/i]+++---"""
		self.assertEqual(after, parse(before))

	def testWrongOrder2(self):
		before = """...[i][b],,,[/i][/b]+++"""
		after = """...[i][b],,,[/b][/i]+++"""
		self.assertEqual(after, parse(before))

	def testWrongOrder3(self):
		before = """...[i][c],,,[b]+++[/i][/c][/b]---"""
		after = """...[p],,,[b]+++[/b][/p]---"""
		self.assertEqual(after, parse(before))

	def testOpenOneCloseAnother(self):
		before = """...[i],,,[/p]+++"""
		after = """...,,,+++"""
		self.assertEqual(after, parse(before))

	def testStartsWtihClosingAndEndsWithOpening(self):
		before = """[/c]...[i]"""
		after = """..."""
		self.assertEqual(after, parse(before))

	def testValidEmptyTagsDestructionOne(self):
		before = """...[i][/i],,,"""
		after = """...,,,"""
		self.assertEqual(after, parse(before))

	def testValidEmptyTagsDestructionMany(self):
		before = """...[b][c][i][/i][/c][/b],,,"""
		after = """...,,,"""
		self.assertEqual(after, parse(before))

	def testBrokenEmptyTagsDestructionMany(self):
		before = """...[b][i][c][/b][/c][/i],,,"""
		after = """...,,,"""
		self.assertEqual(after, parse(before))

	def testNestedWithBrokenOutter(self):
		before = """[i][p]...[/p][/c]"""
		after = """[p]...[/p]"""
		self.assertEqual(after, parse(before))

	def testHorriblyBrokenTags(self):
		before = """[/c]...[i][/p],,,[/i]+++[b]"""
		after = """...[i],,,[/i]+++"""
		self.assertEqual(after, parse(before))

	def testWrongOrder2_WithConent(self):
		before = """[b]...[c red]...[/b]...[/c]"""
		after = """[b]...[c red]...[/c][/b][c red]...[/c]"""
		self.assertEqual(after, parse(before))

	def testWrongOrderWithTextBefore(self):
		before = "[c]...[i],,,[/c][/i]"
		after = "[c]...[i],,,[/i][/c]"
		self.assertEqual(after, parse(before))

	def testRespect_m_TagsProperly(self):
		before = " [m1]for tags like: [p]n[/c][/i][/p]" \
			", the line needs scan again[/m]"
		after = " [m1]for tags like: [p]n[/p], the line needs scan again[/m]"
		self.assertEqual(after, parse(before))

	def testNoTagsDoNothing(self):
		before = after = """no tags, do nothing"""
		self.assertEqual(after, parse(before))

	def testValidNestedTags(self):
		before = """...[i][c][b]...[/b][/c][/i]..."""
		after = """...[b][p]...[/p][/b]..."""
		self.assertEqual(after, parse(before))

	def testBrokenNestedTags(self):
		before = """...[b][i][c]...[/b][/c][/i]..."""
		after = """...[b][p]...[/p][/b]..."""
		self.assertEqual(after, parse(before))

	def testEscapedBrackets(self):
		before = after = r"""on \[the\] top"""
		self.assertEqual(after, parse(before))

	def testPoorlyEscapedBracketsWithTags(self):
		before = r"""...\[c],,,[/c]+++"""
		after = r"""...\[c],,,+++"""
		self.assertEqual(after, parse(before))

	def testPoorlyEscapedBracketsWithTags2(self):
		before = r"""on \[the\] [b]roof[/b]]"""
		after = r"""on \[the\] [b]roof[/b]]"""
		self.assertEqual(after, parse(before))

	def testValidRealDictionaryArticle(self):
		# zh => ru, http://bkrs.info/slovo.php?ch=和田
		before = after = "和田\n" \
			"[m1][p]г. и уезд[/p] Хотан ([i]Синьцзян-Уйгурский[c] авт.[/c]" \
			" р-н, КНР[/i])[/m]" \
			"[m2][*][ex]和田玉 Хотанский нефрит[/ex][/*][/m]"
		self.assertEqual(after, parse(before))

	def testBrokenRealDictionaryArticle(self):
		# zh => ru, http://bkrs.info/slovo.php?ch=一一相应
		before = """一一相应
yīyī xiāngyìng
[m1][c][i]мат.[/c][/i] взаимнооднозначное соответствие[/m]"""
		after = """一一相应
yīyī xiāngyìng
[m1][p]мат.[/p] взаимнооднозначное соответствие[/m]"""
		self.assertEqual(after, parse(before))

	def testBrokenManyRealDictionaryArticle(self):
		# zh => ru, http://bkrs.info/slovo.php?ch=一轮
		before = "一轮\nyīlún\n" \
			"[m1]1) одна очередь[/m][m1]2) цикл ([i]в 12 лет[/i])[/m][m1]" \
			"3) диск ([c][i]напр.[/c] луны[/i])[/m]" \
			"[m1]4) [c] [i]спорт[/c][/i] раунд, круг" \
			" ([i]встречи спортсменов[/i])[/m]" \
			"[m1]5) [c] [i]дипл.[/c][/i] раунд ([i]переговоров[/i])[/m]"
		after = "一轮\nyīlún\n" \
			"[m1]1) одна очередь[/m][m1]2) цикл ([i]в 12 лет[/i])[/m][m1]3)" \
			" диск ([i][c]напр.[/c] луны[/i])[/m]" \
			"[m1]4) [c] [i]спорт[/i][/c] раунд, круг" \
			" ([i]встречи спортсменов[/i])[/m]" \
			"[m1]5) [c] [i]дипл.[/i][/c] раунд ([i]переговоров[/i])[/m]"
		self.assertEqual(after, parse(before))

	def testSameTagsNested(self):
		before = "...[p],,,[p]+++[/p]---[/p]```"
		after = "...[p],,,+++[/p]---```"
		self.assertEqual(after, parse(before))

	def testOneLastTextLetter(self):
		before = after = "b"
		self.assertEqual(after, parse(before))

	def testOneLastTextLetterAfterTag(self):
		before = after = "...[b],,,[/b]b"
		self.assertEqual(after, parse(before))

	def testTagMInsideAnotherTag(self):
		# tag order.
		before = "[c][m1]...[/m][/c]"
		after = "[m1][c]...[/c][/m]"
		self.assertEqual(after, parse(before))

	def testTagMInsideAnotherTagAfterText(self):
		before = "[c]...[m1],,,[/m][/c]"
		after = "[c]...[/c][m1][c],,,[/c][/m]"
		self.assertEqual(after, parse(before))

	def testTagMDeepInside(self):
		before = "...[i],,,[b]+++[c green][/b]---[m1]```[/i][/c][/m]..."
		after = "...[i],,,[b]+++[/b][c green]---[/c][/i][m1][i][c green]" \
			"```[/c][/i][/m]..."
		self.assertEqual(after, parse(before))

	def testTagMInsideBroken(self):
		before = "[m1][*]- [ref]...[/ref][/m][m1]- [ref],,,[/ref][/*][/m]"
		after = "[m1][*]- [ref]...[/ref][/*][/m][m1][*]- [ref],,,[/ref][/*][/m]"
		self.assertEqual(after, parse(before))


if __name__ == "__main__":
	unittest.main()
