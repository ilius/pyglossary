import sys
import unittest
from os.path import abspath, dirname

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from pyglossary.xml_utils import xml_escape


class Test_xml_escape(unittest.TestCase):
	def test(self):
		f = xml_escape
		self.assertEqual(f(""), "")
		self.assertEqual(f("abc"), "abc")
		self.assertEqual(f('"a"'), "&quot;a&quot;")
		self.assertEqual(f("'a'"), "&apos;a&apos;")
		self.assertEqual(f('"a"', quotation=False), '"a"')
		self.assertEqual(f("'a'", quotation=False), "'a'")
		self.assertEqual(f("R&D"), "R&amp;D")
		self.assertEqual(f("<-->"), "&lt;--&gt;")


if __name__ == "__main__":
	unittest.main()
