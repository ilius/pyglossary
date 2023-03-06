import sys
import unittest
from os.path import abspath, dirname, join

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from pyglossary.glossary import Glossary
from pyglossary.plugins.appledict_bin import Reader
from tests.glossary_v2_test import TestGlossaryBase


class TestGlossaryAppleDictBin(TestGlossaryBase):
	def __init__(self, *args, **kwargs):
		TestGlossaryBase.__init__(self, *args, **kwargs)

		self.dataFileCRC32.update({
			"appledict-bin/002-simple.txt": "32a1dbc4",
			"appledict-bin/002-simple.txt_res/style.css": "a83210cb",

			"appledict-bin/006-en-oxfjord_v10.11_c2_t3.txt": "2d3844bf",
			"appledict-bin/006-en-oxfjord_v10.11_c2_t3.txt_res/style.css": "6818c1e5",
		})

		self.addDirCRC32("appledict-bin/002-simple.dictionary", {
			"Contents/Info.plist": "fa73dd65",
			"Contents/Body.data": "3c073986",
			"Contents/DefaultStyle.css": "a83210cb",
			"Contents/EntryID.data": "37305249",
			"Contents/EntryID.index": "8c30a3fa",
			"Contents/Images/_internal_dictionary.png": "da4d4eb1",
			"Contents/KeyText.data": "aefe15e0",
			"Contents/KeyText.index": "b723c5b2",
			"Contents/MyDictionary.xsl": "023de1ea",
			"Contents/MyDictionary_prefs.html": "09a9f6e9",
		})
		self.addDirCRC32("appledict-bin/006-en-oxfjord_v10.11_c2_t3.dictionary", {
			"Contents/Info.plist": "328abb6f",
			"Contents/Resources/Body.data": "03fe72e8",
			"Contents/Resources/DefaultStyle.css": "6818c1e5",
			"Contents/Resources/EntryID.data": "d31adec1",
			"Contents/Resources/EntryID.index": "6eea272c",
			"Contents/Resources/KeyText.data": "d4417c62",
			"Contents/Resources/KeyText.index": "59f9ab67",
			"Contents/Resources/style.css": "c243b56a",
		})

	def test_fix_links(self):
		glos = Glossary()
		reader = Reader(glos)
		f = reader.fixLinksInDefi
		self.assertEqual(
			f('foo <a id="123" href="hello">test</a> bar'),
			'foo <a id="123" href="bword://hello">test</a> bar',
		)
		self.assertEqual(
			f('foo <a href="http://github.com" id="123">test</a> bar'),
			'foo <a href="http://github.com" id="123">test</a> bar',
		)
		self.assertEqual(
			f('foo <a href="https://github.com" id="123">test</a> bar'),
			'foo <a href="https://github.com" id="123">test</a> bar',
		)
		self.assertEqual(
			f('foo <a id="123" href="hello">test</a> bar'),
			'foo <a id="123" href="bword://hello">test</a> bar',
		)
		self.assertEqual(
			f('foo <a id="123" href="x-dictionary:d:hello">test</a> bar'),
			'foo <a id="123" href="bword://hello">test</a> bar',
		)
		self.assertEqual(
			f(
				'<a href="x-dictionary:r:123:com.apple.dictionary.no.oup'
				'#xpointer(//*[@id=\'234\'])" title="test">',
			),
			'<a href="bword://test" title="test">',
		)

	def convert_appledict_binary_to_txt(self, baseName: str, files: "list[str]"):
		self.glos = Glossary()
		inputDirPath = self.downloadDir(
			f"appledict-bin/{baseName}.dictionary",
			files,
		)
		outputFilePath = self.newTempFilePath(f"{baseName}.txt")
		expectedOutputFilePath = self.downloadFile(
			f"appledict-bin/{baseName}.txt",
		)
		expectedStylePath = self.downloadFile(
			f"appledict-bin/{baseName}.txt_res/style.css",
		)

		result = self.glos.convert(
			inputFilename=inputDirPath,
			outputFilename=outputFilePath,
			inputFormat="AppleDictBin",
			outputFormat="Tabfile",
		)
		self.assertIsNotNone(result)
		self.assertEqual(result, outputFilePath)

		self.compareTextFiles(
			outputFilePath,
			expectedOutputFilePath,
		)
		self.compareTextFiles(
			join(outputFilePath + "_res", "style.css"),
			expectedStylePath,
		)

	def test_appledict_binary_to_txt_0(self):
		baseName = "002-simple"
		files = [
			"Contents/Body.data",
			"Contents/DefaultStyle.css",
			"Contents/EntryID.data",
			"Contents/EntryID.index",
			"Contents/Images/_internal_dictionary.png",
			"Contents/Info.plist",
			"Contents/KeyText.data",
			"Contents/KeyText.index",
			"Contents/MyDictionary.xsl",
			"Contents/MyDictionary_prefs.html",
		]
		self.convert_appledict_binary_to_txt(baseName, files)


	def test_appledict_binary_to_txt_1(self):
		baseName = "006-en-oxfjord_v10.11_c2_t3"
		files = [
			"Contents/Info.plist",
			"Contents/Resources/Body.data",
			"Contents/Resources/DefaultStyle.css",
			"Contents/Resources/EntryID.data",
			"Contents/Resources/EntryID.index",
			"Contents/Resources/KeyText.data",
			"Contents/Resources/KeyText.index",
			"Contents/Resources/style.css",
		]
		self.convert_appledict_binary_to_txt(baseName, files)


if __name__ == "__main__":
	unittest.main()
