import plistlib
import sys
import unittest
from os.path import abspath, dirname, join

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from glossary_v2_test import TestGlossaryBase

from pyglossary.glossary import Glossary


class TestGlossaryAppleDict(TestGlossaryBase):
	def __init__(self, *args, **kwargs):
		TestGlossaryBase.__init__(self, *args, **kwargs)

		hashDict = {
			"appledict-src/002-no-morphology-v3.txt": "d8086fe8",
			"appledict-src/002-no-morphology-v3/002-no-morphology-v3.css": "6818c1e5",
			"appledict-src/002-no-morphology-v3/002-no-morphology-v3.plist": "f9f6ff31",
			"appledict-src/002-no-morphology-v3/002-no-morphology-v3.xml": "707994d6",
			"appledict-src/002-no-morphology-v3/Makefile": "65f736b6",
		}
		self.dataFileCRC32.update(hashDict)

	def comparePlist(self, fpath1, fpath2):
		with open(fpath1, "rb") as _file:
			data1 = plistlib.loads(_file.read())
		with open(fpath2, "rb") as _file:
			data2 = plistlib.loads(_file.read())
		self.assertEqual(data1, data2)

	def test_tabfile_without_morpho_to_appledict_source(self):
		self.glos = Glossary()

		baseName = "002-no-morphology-v3"
		inputFilepath = self.downloadFile(f"appledict-src/{baseName}.txt")
		outputDirPath = self.newTempFilePath(f"{baseName}")

		expectedFiles = {
			name: self.downloadFile(f"appledict-src/{baseName}/{name}")
			for name in [
				f"{baseName}.xml",
				f"{baseName}.css",
				"Makefile",
			]
		}

		result = self.glos.convert(
			inputFilename=inputFilepath,
			outputFilename=outputDirPath,
			inputFormat="Tabfile",
			outputFormat="AppleDict",
		)
		self.assertIsNotNone(result)
		self.assertEqual(result, outputDirPath)

		for fname, fpath in expectedFiles.items():
			self.compareTextFiles(
				join(outputDirPath, fname),
				fpath,
			)

		self.comparePlist(
			join(outputDirPath, f"{baseName}.plist"),
			self.downloadFile(f"appledict-src/{baseName}/{baseName}.plist"),
		)


if __name__ == "__main__":
	unittest.main()
