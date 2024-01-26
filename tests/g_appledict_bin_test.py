import sys
import unittest
from os.path import abspath, dirname, join

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from glossary_v2_test import TestGlossaryBase

from pyglossary.glossary import Glossary


class TestGlossaryAppleDictBin(TestGlossaryBase):
	def __init__(self, *args, **kwargs):
		TestGlossaryBase.__init__(self, *args, **kwargs)

		hashDict = {
			"appledict-bin/002-simple.txt": "32a1dbc4",
			"appledict-bin/002-simple.txt_res/style.css": "a83210cb",
			"appledict-bin/006-en-oxfjord_v10.11_c2_t3.txt": "2d3844bf",
			"appledict-bin/006-en-oxfjord_v10.11_c2_t3.txt_res/style.css": "14c3cf2c",
		}
		self.dataFileCRC32.update(hashDict)

		self.addDirCRC32(
			"appledict-bin/002-simple.dictionary",
			{
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
			},
		)
		self.addDirCRC32(
			"appledict-bin/006-en-oxfjord_v10.11_c2_t3.dictionary",
			{
				"Contents/Info.plist": "328abb6f",
				"Contents/Resources/Body.data": "03fe72e8",
				"Contents/Resources/DefaultStyle.css": "c243b56a",
				"Contents/Resources/EntryID.data": "d31adec1",
				"Contents/Resources/EntryID.index": "6eea272c",
				"Contents/Resources/KeyText.data": "d4417c62",
				"Contents/Resources/KeyText.index": "59f9ab67",
			},
		)

	def convert_appledict_binary_to_txt(
		self,
		baseName: str,
		files: "list[str]",
		html_full: bool = False,
		resFiles: "dict[str, str] | None" = None,
	):
		if resFiles is None:
			resFiles = {}
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
			readOptions={
				"html_full": html_full,
			},
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
		for relPath, inputRelPath in resFiles.items():
			self.compareBinaryFiles(
				join(outputFilePath + "_res", relPath),
				join(inputDirPath, inputRelPath),
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
		_internal = "Images/_internal_dictionary.png"
		resFiles = {
			_internal: f"Contents/{_internal}",
		}
		self.convert_appledict_binary_to_txt(baseName, files, resFiles=resFiles)

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
		]
		self.convert_appledict_binary_to_txt(baseName, files)


if __name__ == "__main__":
	unittest.main()
