import plistlib
import sys
import unittest
from os.path import abspath, dirname, join

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from glossary_v2_test import TestGlossaryBase

from pyglossary.glossary_v2 import ConvertArgs, Glossary


class TestGlossaryAppleDict(TestGlossaryBase):
	def __init__(self, *args, **kwargs):
		TestGlossaryBase.__init__(self, *args, **kwargs)

		hashDict = {
			"appledict-src/002-no-morphology-v3.txt": "d8086fe8",
			"appledict-src/002-no-morphology-v3a/002-no-morphology-v3a.css": "6818c1e5",
			"appledict-src/002-no-morphology-v3a/002-no-morphology-v3a.plist": "706d1d9c",
			"appledict-src/002-no-morphology-v3a/002-no-morphology-v3a.xml": "707994d6",
			"appledict-src/002-no-morphology-v3a/Makefile": "ecd42350",
		}
		self.dataFileCRC32 |= hashDict

	def comparePlist(self, fpath1, fpath2):
		with open(fpath1, "rb") as file:
			data1 = plistlib.loads(file.read())
		with open(fpath2, "rb") as file:
			data2 = plistlib.loads(file.read())
		self.assertEqual(data1, data2)

	def test_tabfile_without_morpho_to_appledict_source(self):
		self.glos = Glossary()

		inputName = "002-no-morphology-v3"
		outputName = "002-no-morphology-v3a"
		inputFilepath = self.downloadFile(f"appledict-src/{inputName}.txt")
		outputDirPath = self.newTempFilePath(f"{outputName}")

		expectedFiles = {
			name: self.downloadFile(f"appledict-src/{outputName}/{name}")
			for name in [
				f"{outputName}.xml",
				f"{outputName}.css",
				"Makefile",
			]
		}

		result = self.glos.convert(
			ConvertArgs(
				inputFilename=inputFilepath,
				outputFilename=outputDirPath,
				inputFormat="Tabfile",
				outputFormat="AppleDict",
			)
		)
		self.assertIsNotNone(result)
		self.assertEqual(result, outputDirPath)

		for fname, fpath in expectedFiles.items():
			self.compareTextFiles(
				join(outputDirPath, fname),
				fpath,
			)

		self.comparePlist(
			join(outputDirPath, f"{outputName}.plist"),
			self.downloadFile(f"appledict-src/{outputName}/{outputName}.plist"),
		)

	def test_appledict_source_read_entry_count_matches_tabfile(self):
		inputName = "002-no-morphology-v3"
		inputFilepath = self.downloadFile(f"appledict-src/{inputName}.txt")

		gl_tab = Glossary()
		gl_tab.directRead(inputFilepath, formatName="Tabfile")
		n_tab = sum(1 for e in gl_tab if not e.isData())
		gl_tab.cleanup()

		outputDirPath = self.newTempFilePath("appledict_roundtrip.apple")
		self.glos = Glossary()
		self.glos.convert(
			ConvertArgs(
				inputFilename=inputFilepath,
				outputFilename=outputDirPath,
				inputFormat="Tabfile",
				outputFormat="AppleDict",
			)
		)

		gl_rd = Glossary()
		self.glos = gl_rd
		gl_rd.directRead(outputDirPath)
		n_rd = sum(1 for e in gl_rd if not e.isData())
		self.assertEqual(n_rd, n_tab)


if __name__ == "__main__":
	unittest.main()
