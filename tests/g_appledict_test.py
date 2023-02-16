import shutil
import sys
from os.path import dirname, abspath, join
import unittest

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from tests.glossary_test import TestGlossaryBase
from pyglossary.glossary import Glossary


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

	def test_tabfile_without_morpho_to_appledict_source(self):
		self.glos = Glossary()

		baseName = "002-no-morphology"
		inputFilepath = self.downloadFile(f"appledict-src/{baseName}.txt")
		outputDirPath = self.newTempFilePath(f"{baseName}")

		expectedFiles = {
			name: self.downloadFile(f"appledict-src/{baseName}/{name}")
			for name in [
				f"{baseName}.xml",
				# f"{baseName}.plist",  # different each time
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
