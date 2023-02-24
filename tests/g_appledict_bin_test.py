import sys
import unittest
from os.path import abspath, dirname, join

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from pyglossary.glossary import Glossary
from pyglossary.plugins.appledict_bin import Reader
from tests.glossary_test import TestGlossaryBase


class TestGlossaryAppleDictBin(TestGlossaryBase):
	def __init__(self, *args, **kwargs):
		TestGlossaryBase.__init__(self, *args, **kwargs)

		self.dataFileCRC32.update({
			"appledict-bin/002-simple.dictionary/Contents/Body.data": "3c073986",
			"appledict-bin/002-simple.dictionary/Contents/DefaultStyle.css": "a83210cb",
			"appledict-bin/002-simple.dictionary/Contents/EntryID.data": "37305249",
			"appledict-bin/002-simple.dictionary/Contents/EntryID.index": "8c30a3fa",
			"appledict-bin/002-simple.dictionary/Contents/Images/_internal_dictionary.png": "da4d4eb1",
			"appledict-bin/002-simple.dictionary/Contents/Info.plist": "fa73dd65",
			"appledict-bin/002-simple.dictionary/Contents/KeyText.data": "aefe15e0",
			"appledict-bin/002-simple.dictionary/Contents/KeyText.index": "b723c5b2",
			"appledict-bin/002-simple.dictionary/Contents/MyDictionary.xsl": "023de1ea",
			"appledict-bin/002-simple.dictionary/Contents/MyDictionary_prefs.html": "09a9f6e9",
			"appledict-bin/002-simple.txt": "32a1dbc4",
			"appledict-bin/002-simple.txt_res/style.css": "a83210cb",

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

	def test_appledict_binary_to_txt(self):
		self.glos = Glossary()

		baseName = "002-simple"
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

	def test_raw_key_text(self):
		v = '10.5'
		for c in range(2):
			for t in range(1):
				baseName = f'006-en-oxfjord_v{v}_c{c}_t{t}'
				self.test_oxfjord_KeyText_variant(baseName, '')
		v = '10.6'
		for c in range(0, 3):
			for t in range(0, 4):
				baseName = f'006-en-oxfjord_v{v}_c{c}_t{t}'
				self.test_oxfjord_KeyText_variant(baseName, '')
		v = '10.11'
		baseName = f'006-en-oxfjord_v{v}_c{2}_t{3}'
		self.test_oxfjord_KeyText_variant(baseName, 'Resources/')

	def test_oxfjord_KeyText_variant(self, baseName, subfolder):
		inputDirPath = self.downloadDir(
			f"appledict-bin/{baseName}.dictionary",
			[
				"Contents/Info.plist",
				f"Contents/{subfolder}Body.data",
				f"Contents/{subfolder}DefaultStyle.css",
				f"Contents/{subfolder}EntryID.data",
				f"Contents/{subfolder}EntryID.index",
				f"Contents/{subfolder}Images/_internal_dictionary.png",
				f"Contents/{subfolder}KeyText.data",
				f"Contents/{subfolder}KeyText.index",
				f"Contents/{subfolder}MyDictionary.xsl",
				f"Contents/{subfolder}MyDictionary_prefs.html",
			],
		)
		glos = Glossary()
		reader = Reader(glos)
		metadata = reader.parseMetadata(join(inputDirPath, 'Contents/Info.plist'))
		reader.setMetadata(metadata)
		key_text_data = reader.getKeyTextDataFromFile(
			join(inputDirPath, f'Contents/{subfolder}KeyText.data'),
			reader._properties)

		actualKeyTextOutputPath = f'{baseName}_KeyText.data_test.txt'
		expectedKeyTextOutputPath = f'expected_KeyText.data_{baseName}.txt'
		with open(actualKeyTextOutputPath, 'w') as fid:
			for article_address in sorted(key_text_data.keys()):
				fid.write(f'{article_address}\t{key_text_data[article_address]}\n')
		self.compareTextFiles(
			actualKeyTextOutputPath,
			expectedKeyTextOutputPath,
		)


if __name__ == "__main__":
	unittest.main()
