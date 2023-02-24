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
			"appledict-bin/006-en-oxfjord_v10.11_c2_t3.dictionary/Contents/Info.plist": "328abb6f",
			"appledict-bin/006-en-oxfjord_v10.5_c0_t0.dictionary/Contents/Body.data": "5a37f87c",
			"appledict-bin/006-en-oxfjord_v10.5_c0_t0.dictionary/Contents/DefaultStyle.css": "6818c1e5",
			"appledict-bin/006-en-oxfjord_v10.5_c0_t0.dictionary/Contents/EntryID.data": "7d842b1f",
			"appledict-bin/006-en-oxfjord_v10.5_c0_t0.dictionary/Contents/EntryID.index": "2100ef84",
			"appledict-bin/006-en-oxfjord_v10.5_c0_t0.dictionary/Contents/Info.plist": "a64cac40",
			"appledict-bin/006-en-oxfjord_v10.5_c0_t0.dictionary/Contents/KeyText.data": "157fa9dc",
			"appledict-bin/006-en-oxfjord_v10.5_c0_t0.dictionary/Contents/KeyText.index": "7b3a1616",
			"appledict-bin/006-en-oxfjord_v10.5_c0_t0.dictionary/Contents/style.css": "c243b56a",
			"appledict-bin/006-en-oxfjord_v10.5_c1_t0.dictionary/Contents/Body.data": "4ff5c387",
			"appledict-bin/006-en-oxfjord_v10.5_c1_t0.dictionary/Contents/DefaultStyle.css": "6818c1e5",
			"appledict-bin/006-en-oxfjord_v10.5_c1_t0.dictionary/Contents/EntryID.data": "143bb934",
			"appledict-bin/006-en-oxfjord_v10.5_c1_t0.dictionary/Contents/EntryID.index": "2100ef84",
			"appledict-bin/006-en-oxfjord_v10.5_c1_t0.dictionary/Contents/Info.plist": "19ccc9a3",
			"appledict-bin/006-en-oxfjord_v10.5_c1_t0.dictionary/Contents/KeyText.data": "3cafdb79",
			"appledict-bin/006-en-oxfjord_v10.5_c1_t0.dictionary/Contents/KeyText.index": "7b3a1616",
			"appledict-bin/006-en-oxfjord_v10.5_c1_t0.dictionary/Contents/style.css": "c243b56a",
			"appledict-bin/006-en-oxfjord_v10.6_c0_t0.dictionary/Contents/Body.data": "5a37f87c",
			"appledict-bin/006-en-oxfjord_v10.6_c0_t0.dictionary/Contents/DefaultStyle.css": "6818c1e5",
			"appledict-bin/006-en-oxfjord_v10.6_c0_t0.dictionary/Contents/EntryID.data": "7d842b1f",
			"appledict-bin/006-en-oxfjord_v10.6_c0_t0.dictionary/Contents/EntryID.index": "283bf8ca",
			"appledict-bin/006-en-oxfjord_v10.6_c0_t0.dictionary/Contents/Info.plist": "9f3d43c5",
			"appledict-bin/006-en-oxfjord_v10.6_c0_t0.dictionary/Contents/KeyText.data": "b1d739d1",
			"appledict-bin/006-en-oxfjord_v10.6_c0_t0.dictionary/Contents/KeyText.index": "9d203f95",
			"appledict-bin/006-en-oxfjord_v10.6_c0_t0.dictionary/Contents/style.css": "c243b56a",
			"appledict-bin/006-en-oxfjord_v10.6_c0_t1.dictionary/Contents/Body.data": "5a37f87c",
			"appledict-bin/006-en-oxfjord_v10.6_c0_t1.dictionary/Contents/DefaultStyle.css": "6818c1e5",
			"appledict-bin/006-en-oxfjord_v10.6_c0_t1.dictionary/Contents/EntryID.data": "7d842b1f",
			"appledict-bin/006-en-oxfjord_v10.6_c0_t1.dictionary/Contents/EntryID.index": "283bf8ca",
			"appledict-bin/006-en-oxfjord_v10.6_c0_t1.dictionary/Contents/Info.plist": "72e78f7f",
			"appledict-bin/006-en-oxfjord_v10.6_c0_t1.dictionary/Contents/KeyText.data": "ecd3db8f",
			"appledict-bin/006-en-oxfjord_v10.6_c0_t1.dictionary/Contents/KeyText.index": "a5419863",
			"appledict-bin/006-en-oxfjord_v10.6_c0_t1.dictionary/Contents/style.css": "c243b56a",
			"appledict-bin/006-en-oxfjord_v10.6_c0_t2.dictionary/Contents/Body.data": "5a37f87c",
			"appledict-bin/006-en-oxfjord_v10.6_c0_t2.dictionary/Contents/DefaultStyle.css": "6818c1e5",
			"appledict-bin/006-en-oxfjord_v10.6_c0_t2.dictionary/Contents/EntryID.data": "7d842b1f",
			"appledict-bin/006-en-oxfjord_v10.6_c0_t2.dictionary/Contents/EntryID.index": "aa54093b",
			"appledict-bin/006-en-oxfjord_v10.6_c0_t2.dictionary/Contents/Info.plist": "f777ce61",
			"appledict-bin/006-en-oxfjord_v10.6_c0_t2.dictionary/Contents/KeyText.data": "aa707de9",
			"appledict-bin/006-en-oxfjord_v10.6_c0_t2.dictionary/Contents/KeyText.index": "583ef99c",
			"appledict-bin/006-en-oxfjord_v10.6_c0_t2.dictionary/Contents/style.css": "c243b56a",
			"appledict-bin/006-en-oxfjord_v10.6_c0_t3.dictionary/Contents/Body.data": "5a37f87c",
			"appledict-bin/006-en-oxfjord_v10.6_c0_t3.dictionary/Contents/DefaultStyle.css": "6818c1e5",
			"appledict-bin/006-en-oxfjord_v10.6_c0_t3.dictionary/Contents/EntryID.data": "7d842b1f",
			"appledict-bin/006-en-oxfjord_v10.6_c0_t3.dictionary/Contents/EntryID.index": "2100ef84",
			"appledict-bin/006-en-oxfjord_v10.6_c0_t3.dictionary/Contents/Info.plist": "a64cac40",
			"appledict-bin/006-en-oxfjord_v10.6_c0_t3.dictionary/Contents/KeyText.data": "b1d739d1",
			"appledict-bin/006-en-oxfjord_v10.6_c0_t3.dictionary/Contents/KeyText.index": "8f455ad3",
			"appledict-bin/006-en-oxfjord_v10.6_c0_t3.dictionary/Contents/style.css": "c243b56a",
			"appledict-bin/006-en-oxfjord_v10.6_c1_t0.dictionary/Contents/Body.data": "4ff5c387",
			"appledict-bin/006-en-oxfjord_v10.6_c1_t0.dictionary/Contents/DefaultStyle.css": "6818c1e5",
			"appledict-bin/006-en-oxfjord_v10.6_c1_t0.dictionary/Contents/EntryID.data": "143bb934",
			"appledict-bin/006-en-oxfjord_v10.6_c1_t0.dictionary/Contents/EntryID.index": "283bf8ca",
			"appledict-bin/006-en-oxfjord_v10.6_c1_t0.dictionary/Contents/Info.plist": "b3b8cc1e",
			"appledict-bin/006-en-oxfjord_v10.6_c1_t0.dictionary/Contents/KeyText.data": "1217019f",
			"appledict-bin/006-en-oxfjord_v10.6_c1_t0.dictionary/Contents/KeyText.index": "9d203f95",
			"appledict-bin/006-en-oxfjord_v10.6_c1_t0.dictionary/Contents/style.css": "c243b56a",
			"appledict-bin/006-en-oxfjord_v10.6_c1_t1.dictionary/Contents/Body.data": "4ff5c387",
			"appledict-bin/006-en-oxfjord_v10.6_c1_t1.dictionary/Contents/DefaultStyle.css": "6818c1e5",
			"appledict-bin/006-en-oxfjord_v10.6_c1_t1.dictionary/Contents/EntryID.data": "143bb934",
			"appledict-bin/006-en-oxfjord_v10.6_c1_t1.dictionary/Contents/EntryID.index": "283bf8ca",
			"appledict-bin/006-en-oxfjord_v10.6_c1_t1.dictionary/Contents/Info.plist": "66f32b83",
			"appledict-bin/006-en-oxfjord_v10.6_c1_t1.dictionary/Contents/KeyText.data": "3ac9185f",
			"appledict-bin/006-en-oxfjord_v10.6_c1_t1.dictionary/Contents/KeyText.index": "a5419863",
			"appledict-bin/006-en-oxfjord_v10.6_c1_t1.dictionary/Contents/style.css": "c243b56a",
			"appledict-bin/006-en-oxfjord_v10.6_c1_t2.dictionary/Contents/Body.data": "4ff5c387",
			"appledict-bin/006-en-oxfjord_v10.6_c1_t2.dictionary/Contents/DefaultStyle.css": "6818c1e5",
			"appledict-bin/006-en-oxfjord_v10.6_c1_t2.dictionary/Contents/EntryID.data": "143bb934",
			"appledict-bin/006-en-oxfjord_v10.6_c1_t2.dictionary/Contents/EntryID.index": "aa54093b",
			"appledict-bin/006-en-oxfjord_v10.6_c1_t2.dictionary/Contents/Info.plist": "d5e3f05c",
			"appledict-bin/006-en-oxfjord_v10.6_c1_t2.dictionary/Contents/KeyText.data": "2152eba1",
			"appledict-bin/006-en-oxfjord_v10.6_c1_t2.dictionary/Contents/KeyText.index": "583ef99c",
			"appledict-bin/006-en-oxfjord_v10.6_c1_t2.dictionary/Contents/style.css": "c243b56a",
			"appledict-bin/006-en-oxfjord_v10.6_c1_t3.dictionary/Contents/Body.data": "4ff5c387",
			"appledict-bin/006-en-oxfjord_v10.6_c1_t3.dictionary/Contents/DefaultStyle.css": "6818c1e5",
			"appledict-bin/006-en-oxfjord_v10.6_c1_t3.dictionary/Contents/EntryID.data": "143bb934",
			"appledict-bin/006-en-oxfjord_v10.6_c1_t3.dictionary/Contents/EntryID.index": "2100ef84",
			"appledict-bin/006-en-oxfjord_v10.6_c1_t3.dictionary/Contents/Info.plist": "19ccc9a3",
			"appledict-bin/006-en-oxfjord_v10.6_c1_t3.dictionary/Contents/KeyText.data": "1217019f",
			"appledict-bin/006-en-oxfjord_v10.6_c1_t3.dictionary/Contents/KeyText.index": "8f455ad3",
			"appledict-bin/006-en-oxfjord_v10.6_c1_t3.dictionary/Contents/style.css": "c243b56a",
			"appledict-bin/006-en-oxfjord_v10.6_c2_t0.dictionary/Contents/Body.data": "03fe72e8",
			"appledict-bin/006-en-oxfjord_v10.6_c2_t0.dictionary/Contents/DefaultStyle.css": "6818c1e5",
			"appledict-bin/006-en-oxfjord_v10.6_c2_t0.dictionary/Contents/EntryID.data": "d31adec1",
			"appledict-bin/006-en-oxfjord_v10.6_c2_t0.dictionary/Contents/EntryID.index": "a7596f9d",
			"appledict-bin/006-en-oxfjord_v10.6_c2_t0.dictionary/Contents/Info.plist": "9a125c89",
			"appledict-bin/006-en-oxfjord_v10.6_c2_t0.dictionary/Contents/KeyText.data": "d4417c62",
			"appledict-bin/006-en-oxfjord_v10.6_c2_t0.dictionary/Contents/KeyText.index": "e8977c3f",
			"appledict-bin/006-en-oxfjord_v10.6_c2_t0.dictionary/Contents/style.css": "c243b56a",
			"appledict-bin/006-en-oxfjord_v10.6_c2_t1.dictionary/Contents/Body.data": "03fe72e8",
			"appledict-bin/006-en-oxfjord_v10.6_c2_t1.dictionary/Contents/DefaultStyle.css": "6818c1e5",
			"appledict-bin/006-en-oxfjord_v10.6_c2_t1.dictionary/Contents/EntryID.data": "d31adec1",
			"appledict-bin/006-en-oxfjord_v10.6_c2_t1.dictionary/Contents/EntryID.index": "a7596f9d",
			"appledict-bin/006-en-oxfjord_v10.6_c2_t1.dictionary/Contents/Info.plist": "2b2fd516",
			"appledict-bin/006-en-oxfjord_v10.6_c2_t1.dictionary/Contents/KeyText.data": "705b9e64",
			"appledict-bin/006-en-oxfjord_v10.6_c2_t1.dictionary/Contents/KeyText.index": "795e2a60",
			"appledict-bin/006-en-oxfjord_v10.6_c2_t1.dictionary/Contents/style.css": "c243b56a",
			"appledict-bin/006-en-oxfjord_v10.6_c2_t2.dictionary/Contents/Body.data": "03fe72e8",
			"appledict-bin/006-en-oxfjord_v10.6_c2_t2.dictionary/Contents/DefaultStyle.css": "6818c1e5",
			"appledict-bin/006-en-oxfjord_v10.6_c2_t2.dictionary/Contents/EntryID.data": "d31adec1",
			"appledict-bin/006-en-oxfjord_v10.6_c2_t2.dictionary/Contents/EntryID.index": "d3519154",
			"appledict-bin/006-en-oxfjord_v10.6_c2_t2.dictionary/Contents/Info.plist": "9592dc7a",
			"appledict-bin/006-en-oxfjord_v10.6_c2_t2.dictionary/Contents/KeyText.data": "fc65f101",
			"appledict-bin/006-en-oxfjord_v10.6_c2_t2.dictionary/Contents/KeyText.index": "4a8208d3",
			"appledict-bin/006-en-oxfjord_v10.6_c2_t2.dictionary/Contents/style.css": "c243b56a",
			"appledict-bin/006-en-oxfjord_v10.6_c2_t3.dictionary/Contents/Body.data": "03fe72e8",
			"appledict-bin/006-en-oxfjord_v10.6_c2_t3.dictionary/Contents/DefaultStyle.css": "6818c1e5",
			"appledict-bin/006-en-oxfjord_v10.6_c2_t3.dictionary/Contents/EntryID.data": "d31adec1",
			"appledict-bin/006-en-oxfjord_v10.6_c2_t3.dictionary/Contents/EntryID.index": "6eea272c",
			"appledict-bin/006-en-oxfjord_v10.6_c2_t3.dictionary/Contents/Info.plist": "51b7296a",
			"appledict-bin/006-en-oxfjord_v10.6_c2_t3.dictionary/Contents/KeyText.data": "d4417c62",
			"appledict-bin/006-en-oxfjord_v10.6_c2_t3.dictionary/Contents/KeyText.index": "59f9ab67",
			"appledict-bin/006-en-oxfjord_v10.6_c2_t3.dictionary/Contents/style.css": "c243b56a",
			"appledict-bin/expected_KeyText.data_006-en-oxfjord_v10.11_c2_t3.txt": "5190e4f7",
			"appledict-bin/expected_KeyText.data_006-en-oxfjord_v10.5_c0_t0.txt": "7e013e9e",
			"appledict-bin/expected_KeyText.data_006-en-oxfjord_v10.5_c1_t0.txt": "73d2290a",
			"appledict-bin/expected_KeyText.data_006-en-oxfjord_v10.6_c0_t0.txt": "f0bd0914",
			"appledict-bin/expected_KeyText.data_006-en-oxfjord_v10.6_c0_t1.txt": "f0bd0914",
			"appledict-bin/expected_KeyText.data_006-en-oxfjord_v10.6_c0_t2.txt": "f0e2d3d9",
			"appledict-bin/expected_KeyText.data_006-en-oxfjord_v10.6_c0_t3.txt": "f0bd0914",
			"appledict-bin/expected_KeyText.data_006-en-oxfjord_v10.6_c1_t0.txt": "b9c95875",
			"appledict-bin/expected_KeyText.data_006-en-oxfjord_v10.6_c1_t1.txt": "b9c95875",
			"appledict-bin/expected_KeyText.data_006-en-oxfjord_v10.6_c1_t2.txt": "4c642aac",
			"appledict-bin/expected_KeyText.data_006-en-oxfjord_v10.6_c1_t3.txt": "b9c95875",
			"appledict-bin/expected_KeyText.data_006-en-oxfjord_v10.6_c2_t0.txt": "5190e4f7",
			"appledict-bin/expected_KeyText.data_006-en-oxfjord_v10.6_c2_t1.txt": "5190e4f7",
			"appledict-bin/expected_KeyText.data_006-en-oxfjord_v10.6_c2_t2.txt": "0934f333",
			"appledict-bin/expected_KeyText.data_006-en-oxfjord_v10.6_c2_t3.txt": "5190e4f7",
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
