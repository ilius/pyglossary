import plistlib
import sys
import unittest
from os.path import abspath, dirname, join

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from pyglossary.glossary import Glossary
from tests.glossary_test import TestGlossaryBase


class TestGlossaryAppleDict(TestGlossaryBase):
	def __init__(self, *args, **kwargs):
		TestGlossaryBase.__init__(self, *args, **kwargs)

		self.dataFileCRC32.update({
			"appledict-src/002-no-morphology.txt": "4afadab4",
			"appledict-src/002-no-morphology/002-no-morphology.css": "6818c1e5",
			"appledict-src/002-no-morphology/002-no-morphology.plist": "7007f286",
			"appledict-src/002-no-morphology/002-no-morphology.xml": "f34df9ac",
			"appledict-src/002-no-morphology/Makefile": "ddc31a07",
		})

	def comparePlist(self, fpath1, fpath2):
		with open(fpath1, "rb") as _file:
			data1 = plistlib.loads(_file.read())
		with open(fpath2, "rb") as _file:
			data2 = plistlib.loads(_file.read())
		self.assertEqual(data1, data2)

	def test_tabfile_without_morpho_to_appledict_source(self):
		self.glos = Glossary()

		baseName = "002-no-morphology"
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

		self.glos.setInfo("name", "002-no-morphology.txt")
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
