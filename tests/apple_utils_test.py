import sys
import unittest
from os.path import abspath, dirname

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from pyglossary.apple_utils import substituteAppleCSS


class Test_substituteAppleCSS(unittest.TestCase):
	def test_remove(self):
		css = b""".test { -webkit-text-combine: horizontal; color: black }
.test2 {
	-apple-color-filter: none;
}"""
		fixed_expected = b""".test {color: black }
.test2 {
}"""
		fixed_actual = substituteAppleCSS(css)
		self.assertEqual(fixed_actual, fixed_expected)

	def test_1(self):
		css = b"""html.apple_display-separateview
{
	-webkit-column-width: 25em;
	-webkit-column-rule-color: LightGrey;
	-webkit-column-rule-style: solid;
	-webkit-column-rule-width: 1px;
}

span.sn
{
	-webkit-text-combine: horizontal;
	vertical-align: -6%;
}
"""
		fixed_expected = b"""html.apple_display-separateview
{
	column-width: 25em;
	column-rule-color: LightGrey;
	column-rule-style: solid;
	column-rule-width: 1px;
}

span.sn
{
vertical-align: -6%;
}
"""
		fixed_actual = substituteAppleCSS(css)
		self.assertEqual(fixed_actual, fixed_expected)
