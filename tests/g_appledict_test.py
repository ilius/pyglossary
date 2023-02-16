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
			"appledict-src/002-no-morphology.xml": "60044894",
		})

	def test_tabfile_without_morpho_to_appledict_source(self):
		self.glos = Glossary()

		baseName = "002-no-morphology"
		inputFilepath = self.downloadFile(f"appledict-src/{baseName}.txt")

		expectedOutputFilePath = self.downloadFile(f"appledict-src/{baseName}.xml")

		outputDirPath = self.glos.convert(
			inputFilename=inputFilepath,
			outputFilename=f"{baseName}-actual",
			inputFormat="Tabfile",
			outputFormat="AppleDict",
		)

		actualOutputFilePath = join(outputDirPath, f"{baseName}-actual.xml")

		self.compareTextFiles(
			actualOutputFilePath,
			expectedOutputFilePath,
		)

		shutil.rmtree(outputDirPath)
