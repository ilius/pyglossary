import sys
from os.path import dirname, abspath, join
import unittest

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from tests.glossary_test import TestGlossaryBase, dataDir
from pyglossary.glossary import Glossary
from pyglossary.plugins.appledict_bin import Reader


class TestGlossaryAppleDictBin(TestGlossaryBase):
	def __init__(self, *args, **kwargs):
		TestGlossaryBase.__init__(self, *args, **kwargs)

		self.dataFileCRC32.update({
			"appledict-bin/002-appledict-bin-no-morphology.dictionary/Contents/Body.data": "3c073986",
			"appledict-bin/002-appledict-bin-no-morphology.dictionary/Contents/DefaultStyle.css": "a83210cb",
			"appledict-bin/002-appledict-bin-no-morphology.dictionary/Contents/EntryID.data": "37305249",
			"appledict-bin/002-appledict-bin-no-morphology.dictionary/Contents/EntryID.index": "8c30a3fa",
			"appledict-bin/002-appledict-bin-no-morphology.dictionary/Contents/Images/_internal_dictionary.png": "da4d4eb1",
			"appledict-bin/002-appledict-bin-no-morphology.dictionary/Contents/Info.plist": "fa73dd65",
			"appledict-bin/002-appledict-bin-no-morphology.dictionary/Contents/KeyText.data": "aefe15e0",
			"appledict-bin/002-appledict-bin-no-morphology.dictionary/Contents/KeyText.index": "b723c5b2",
			"appledict-bin/002-appledict-bin-no-morphology.dictionary/Contents/MyDictionary.xsl": "023de1ea",
			"appledict-bin/002-appledict-bin-no-morphology.dictionary/Contents/MyDictionary_prefs.html": "09a9f6e9",
			"appledict-bin/002-appledict-bin-no-morphology.txt": "4afadab4",
			"appledict-bin/002-appledict-bin-no-morphology.txt_res/style.css": "a83210cb"
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
				'#xpointer(//*[@id=\'234\'])" title="test">'
			),
			'<a href="bword://test" title="test">',
		)

	def test_appledict_binary_to_txt(self):
		self.glos = Glossary()

		baseName = "002-appledict-bin-no-morphology"
		inputDirPath = self.downloadDir(
			f"appledict-bin/{baseName}.dictionary",
			[
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
			],
		)
		outputFilePath = self.newTempFilePath(f"{baseName}.txt")
		expectedOutputFilePath = self.downloadFile(f"appledict-bin/{baseName}.txt")

		result = self.glos.convert(
			inputFilename=inputDirPath,
			outputFilename=outputFilePath,
			inputFormat="AppleDictBin",
			outputFormat="Tabfile",
		)

		self.compareTextFiles(
			outputFilePath,
			expectedOutputFilePath,
		)



