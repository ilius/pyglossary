import logging
import sys
import unittest
from os.path import abspath, dirname

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from glossary_v2_errors_test import TestGlossaryErrors

from pyglossary.glossary_v2 import ConvertArgs, Error, Glossary, ReadError


class TestGlossarySecurity(TestGlossaryErrors):
	def __init__(self, *args, **kwargs):
		TestGlossaryErrors.__init__(self, *args, **kwargs)
		self.mockLog.setLevel(logging.INFO)

	def test_convert_1(self):
		glos = Glossary()
		with self.assertRaisesRegex(Error, "Unable to detect output format!"):
			glos.convert(
				ConvertArgs(
					inputFilename="os.system('abcd')",
					outputFilename="os.system('abcd -l')",
				)
			)

	def test_convert_2(self):
		glos = Glossary()
		with self.assertRaisesRegex(Error, "Unable to detect output format!"):
			glos.convert(
				ConvertArgs(
					inputFilename="os.system('abcd');test.txt",
					outputFilename="os.system('abcd -l')",
				)
			)

	def test_convert_3(self):
		glos = Glossary()
		with self.assertRaisesRegex(ReadError, "No such file or directory: "):
			glos.convert(
				ConvertArgs(
					inputFilename="os.system('abcd');test.txt",
					outputFilename="os.system('abcd -l');test.csv",
				)
			)

	def test_convert_4(self):
		glos = Glossary()
		with self.assertRaisesRegex(Error, "Unable to detect output format!"):
			glos.convert(
				ConvertArgs(
					inputFilename="test.txt\nos.system('abcd')",
					outputFilename="test.csv\nos.system('abcd -l')",
				)
			)


if __name__ == "__main__":
	unittest.main()
