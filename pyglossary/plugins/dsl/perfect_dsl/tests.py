# -*- coding: utf-8 -*-
# perfect_dsl/tests.py
#
""" test everything."""
#
# Copyright (C) 2016 Ratijas <ratijas.t@me.com>
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


import unittest

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from perfect_dsl import (
    BRACKET_L,
    BRACKET_R,
    PerfectDSLParser,
    Stash,
    parse,
    put_brackets_away,
)


class StashTestCase(unittest.TestCase):
    def setUp(self):
        self.prefix = 'dsl'
        self.stash = Stash(self.prefix)

    def testStash(self):
        self.stash.clear()
        line = '...{,,,}+++'
        line = self.stash.save(line, line.index('{'), line.index('}') + 1)
        self.assertEquals(line, '...\0&dsl.0;+++')
        self.assertEquals(self.stash.stash[0], '{,,,}')

    def testStashNested(self):
        self.stash.clear()
        before = '...[,,,{...}+++]---'
        after = '...\0&dsl.1;---'
        line = before
        line = self.stash.save(line, line.index('{'), line.index('}') + 1)
        line = self.stash.save(line, line.index('['), line.index(']') + 1)
        self.assertEquals(line, after)
        self.assertEquals(self.stash.pop(line), before)

    def testStashFlat(self):
        self.stash.clear()
        before = '...[,,,]+++{---}...'
        after = '...\0&dsl.0;+++\0&dsl.1;...'
        line = before
        line = self.stash.save(line, line.index('['), line.index(']') + 1)
        line = self.stash.save(line, line.index('{'), line.index('}') + 1)
        self.assertEquals(line, after)
        self.assertEquals(self.stash.pop(line), before)

    def testStashMixed(self):
        self.stash.clear()
        before = '...(***[,,,]+++{---}###)...'
        after = '...\0&dsl.2;...'
        line = before
        line = self.stash.save(line, line.index('['), line.index(']') + 1)
        line = self.stash.save(line, line.index('{'), line.index('}') + 1)
        line = self.stash.save(line, line.index('('), line.index(')') + 1)
        self.assertEquals(line, after)
        self.assertNotIn('\0', self.stash.stash[2])
        self.assertEquals(self.stash.pop(line), before)


class PerfectDSLParserTestCase(unittest.TestCase):
    def setUp(self):
        self.split_join = lambda x: PerfectDSLParser.join_paragraphs(
            *PerfectDSLParser.split_line_by_paragraphs(x))

    def testStartsWithStandaloneClosed(self):
        before = """[/p]..."""
        after = """..."""
        self.assertEquals(parse(before), after)

    def testStandaloneClosedAtTheBeginning(self):
        before = """...[/p],,,"""
        after = """...,,,"""
        self.assertEquals(parse(before), after)

    def testStandaloneClosedAtTheBeginningBeforeMarkup(self):
        before = """...[/p],,,[i][c]+++[/c][/i]---"""
        after = """...,,,[i][c]+++[/c][/i]---"""
        self.assertEquals(parse(before), after)

    def testEndsWithStandaloneOpened(self):
        before = """...[i]"""
        after = """..."""
        self.assertEquals(parse(before), after)

    def testStandaloneOpenedAtTheEnd(self):
        before = """...[i],,,"""
        after = """...,,,"""
        self.assertEquals(parse(before), after)

    def testStandaloneOpenedAtTheEndAfterMarkup(self):
        before = """...[i][c],,,[/c][/i]+++[i]---"""
        after = """...[i][c],,,[/c][/i]+++---"""
        self.assertEquals(parse(before), after)

    def testWrongOrder2(self):
        before = """...[i][c],,,[/i][/c]+++"""
        after = """...[i][c],,,[/c][/i]+++"""
        self.assertEquals(parse(before), after)

    def testWrongOrder3(self):
        before = """...[i][c],,,[b]+++[/i][/c][/b]---"""
        after = """...[i][c],,,[b]+++[/b][/c][/i]---"""
        self.assertEquals(parse(before), after)

    def testOpenOneCloseAnother(self):
        before = """...[i],,,[/p]+++"""
        after = """...[i],,,[/i]+++"""
        self.assertEquals(parse(before), after)

    def testStartsWtihClosingAndEndsWithOpening(self):
        before = """[/c]...[i]"""
        after = """..."""
        self.assertEquals(parse(before), after)

    def testValidEmptyTagsDestructionOne(self):
        before = """...[i][/i],,,"""
        after = """...,,,"""
        self.assertEquals(parse(before), after)

    def testValidEmptyTagsDestructionMany(self):
        before = """...[b][c][i][/i][/c][/b],,,"""
        after = """...,,,"""
        self.assertEquals(parse(before), after)

    def testBrokenEmptyTagsDestructionMany(self):
        before = """...[b][i][c][/b][/c][/i],,,"""
        after = """...,,,"""
        self.assertEquals(parse(before), after)

    def testNestedWithBrokenOutter(self):
        before = """[i][p]...[/p][/c]"""
        after = """[i][p]...[/p][/i]"""
        self.assertEquals(parse(before), after)

    def testHorriblyBrokenTags(self):
        before = """[/c]...[i][/p],,,[/i]+++[b]"""
        after = """...[i],,,[/i]+++"""
        self.assertEquals(parse(before), after)

    def testWrongOrder2_WithConent(self):
        before = """[b]...[c red]...[/b]...[/c]"""
        after = """[b]...[c red]...[/c][/b][c red]...[/c]"""
        self.assertEquals(parse(before), after)

    def testWrongOrderWithTextBefore(self):
        before = "[c]...[i],,,[/c][/i]"
        after = "[c]...[i],,,[/i][/c]"
        self.assertEquals(parse(before), after)

    def testRespect_m_TagsProperly(self):
        before = """ [m1]for tags like: [p]n[/c][/i][/p], the line needs scan again[/m]"""
        after = """ [m1]for tags like: [p]n[/p], the line needs scan again[/m]"""
        self.assertEquals(parse(before), after)

    def testNoTagsDoNothing(self):
        before = after = """no tags, do nothing"""
        self.assertEquals(parse(before), after)

    def testValidNestedTags(self):
        before = after = """...[b][i][c]...[/c][/i][/b]..."""
        self.assertEquals(parse(before), after)

    def testBrokenNestedTags(self):
        before = """...[b][i][c]...[/b][/c][/i]..."""
        after = """...[b][i][c]...[/c][/i][/b]..."""
        self.assertEquals(parse(before), after)

    def testEscapedBrackets(self):
        before = after = r"""on \[the\] top"""
        self.assertEquals(parse(before), after)

    def testPoorlyEscapedBracketsWithTags(self):
        before = r"""...\[c],,,[/c]+++"""
        after = r"""...\[c],,,+++"""
        self.assertEquals(parse(before), after)

    def testPoorlyEscapedBracketsWithTags2(self):
        before = r"""on \[the\] [b]roof[/b]]"""
        after = r"""on \[the\] [b]roof[/b]]"""
        self.assertEquals(parse(before), after)

    def testValidRealDictionaryArticle(self):
        # zh => ru, http://bkrs.info/slovo.php?ch=和田
        before = after = """和田
[m1][p]г. и уезд[/p] Хотан ([i]Синьцзян-Уйгурский[c] авт.[/c] р-н, КНР[/i])[/m]\
[m2][*][ex]和田玉 Хотанский нефрит[/ex][/*][/m]"""
        self.assertEquals(parse(before), after)

    def testBrokenRealDictionaryArticle(self):
        # zh => ru, http://bkrs.info/slovo.php?ch=一一相应
        before = """一一相应
yīyī xiāngyìng
[m1][c][i]мат.[/c][/i] взаимнооднозначное соответствие[/m]"""
        after = """一一相应
yīyī xiāngyìng
[m1][c][i]мат.[/i][/c] взаимнооднозначное соответствие[/m]"""
        self.assertEquals(parse(before), after)

    def testBrokenManyRealDictionaryArticle(self):
        # zh => ru, http://bkrs.info/slovo.php?ch=一轮
        before = """一轮
yīlún
[m1]1) одна очередь[/m][m1]2) цикл ([i]в 12 лет[/i])[/m][m1]3) диск ([c][i]напр.[/c] луны[/i])[/m]\
[m1]4) [c] [i]спорт[/c][/i] раунд, круг ([i]встречи спортсменов[/i])[/m]\
[m1]5) [c] [i]дипл.[/c][/i] раунд ([i]переговоров[/i])[/m]"""
        after = """一轮
yīlún
[m1]1) одна очередь[/m][m1]2) цикл ([i]в 12 лет[/i])[/m][m1]3) диск ([c][i]напр.[/i][/c][i] луны[/i])[/m]\
[m1]4) [c] [i]спорт[/i][/c] раунд, круг ([i]встречи спортсменов[/i])[/m]\
[m1]5) [c] [i]дипл.[/i][/c] раунд ([i]переговоров[/i])[/m]"""
        self.assertEquals(parse(before), after)

    def testSameTagsNested(self):
        self.skipTest(NotImplemented)
        before = "...[p],,,[p]+++[/p]---[/p]```"
        after = "...[p],,,+++---[/p]```"
        self.assertEquals(parse(before), after)

    def testParagpaphSplittingNoTags(self):
        before = "..."
        after = (["..."], [])
        self.assertEquals(PerfectDSLParser.split_line_by_paragraphs(before), after)
        self.assertEquals(PerfectDSLParser.join_paragraphs(*after), before)
        self.assertEquals(self.split_join(before), before)

    def testParagraphSplittingOneTag(self):
        before = "[m1]...[/m]"
        after = (["", "...", ""], ["[m1]", "[/m]"])
        self.assertEquals(PerfectDSLParser.split_line_by_paragraphs(before), after)
        self.assertEquals(PerfectDSLParser.join_paragraphs(*after), before)
        self.assertEquals(self.split_join(before), before)

    def testParagraphSplittingManyTags(self):
        before = "...[m1],,,[/m]+++[m2]```[/m]***"
        after = (["...", ",,,", "+++", "```", "***"], ["[m1]", "[/m]", "[m2]", "[/m]"])
        self.assertEquals(PerfectDSLParser.split_line_by_paragraphs(before), after)
        self.assertEquals(PerfectDSLParser.join_paragraphs(*after), before)
        self.assertEquals(self.split_join(before), before)


class PutBracketsAwayTestCase(unittest.TestCase):
    def setUp(self):
        self.tests = []
        tags = frozenset({
            'b',
            '\'',
            'c',
            'i',
            'sup',
            'sub',
            'ex',
            'p',
            r'\*',
            ('m', '\d'),
        })
        self.tags = {t if isinstance(t, tuple) else (t, '') for t in tags}

    def testStandaloneLeftEscapedAtTheBeginning(self):
        before = "[..."
        after = "%s..." % BRACKET_L
        self.assertEquals(put_brackets_away(before, self.tags), after)

    def testStandaloneRightEscapedAtTheBeginning(self):
        before = "]..."
        after = "%s..." % BRACKET_R
        self.assertEquals(put_brackets_away(before, self.tags), after)

    def testStandaloneLeftEscaped(self):
        before = r"...\[,,,"
        after = r"...\%s,,," % BRACKET_L
        self.assertEquals(put_brackets_away(before, self.tags), after)

    def testStandaloneRightEscaped(self):
        before = r"...\],,,"
        after = r"...\%s,,," % BRACKET_R
        self.assertEquals(put_brackets_away(before, self.tags), after)

    def testStandaloneLeftNonEscaped(self):
        before = "...[,,,"
        after = "...%s,,," % BRACKET_L
        self.assertEquals(put_brackets_away(before, self.tags), after)

    def testStandaloneRightNonEscaped(self):
        before = "...],,,"
        after = "...%s,,," % BRACKET_R
        self.assertEquals(put_brackets_away(before, self.tags), after)

    def testStandaloneLeftNonEscapedBeforeTagName(self):
        before = "...[p ,,,"
        after = "...%sp ,,," % BRACKET_L
        self.assertEquals(put_brackets_away(before, self.tags), after)

    def testStandaloneRightNonEscapedAfterTagName(self):
        before = "c]..."
        after = "c%s..." % BRACKET_R
        self.assertEquals(put_brackets_away(before, self.tags), after)

    def testPairEscaped(self):
        before = r"...\[the\],,,"
        after = r"...\%sthe\%s,,," % (BRACKET_L, BRACKET_R)
        self.assertEquals(put_brackets_away(before, self.tags), after)

    def testPairEscapedAroundTagName(self):
        before = r"...\[i\],,,"
        after = r"...\%si\%s,,," % (BRACKET_L, BRACKET_R)
        self.assertEquals(put_brackets_away(before, self.tags), after)

    def testPairEscapedAroundClosingTagName(self):
        before = r"...\[/i\],,,"
        after = r"...\%s/i\%s,,," % (BRACKET_L, BRACKET_R)
        self.assertEquals(put_brackets_away(before, self.tags), after)

    def testMixed(self):
        before = r"[i]...\[on \]\[the] to[p][/i]"
        after = r"[i]...\{L}on \{R}\{L}the{R} to[p][/i]".format(L=BRACKET_L, R=BRACKET_R)
        self.assertEquals(put_brackets_away(before, self.tags), after)

    def testEverythingEscaped(self):
        before = """ change it to \[b\]...\[c\]...\[/c\]\[/b\]\[c\]...\[/c\]"""
        after = before
        self.assertEquals(parse(before), after)


if __name__ == '__main__':
    unittest.main()
