import sys
from os.path import dirname, abspath
import unittest

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from tests.glossary_test import TestGlossaryBase
from pyglossary.entry import Entry


class TestGlossarySlob(TestGlossaryBase):
	def __init__(self, *args, **kwargs):
		TestGlossaryBase.__init__(self, *args, **kwargs)

		self.dataFileCRC32.update({
			"100-en-fa-res.slob": "0216d006",
			"100-en-fa-res-slob.txt": "c73100b3",
			"100-en-fa-res-slob-sort.txt": "8253fe96",
		})

	def test_convert_txt_slob_1(self):
		fname = "100-en-fa"
		self.convert(
			f"{fname}.txt",
			f"{fname}.slob",
			compareBinary=f"",
			# slob file is different each time (and so its sha1sum and md5sum)
		)

	def convert_slob_txt(self, fname, fname2, resFiles, **convertArgs):
		resFilesPath = {
			resFileName: self.newTempFilePath(f"{fname}-2.txt_res/{resFileName}")
			for resFileName in resFiles
		}

		self.convert(
			f"{fname}.slob",
			f"{fname}-2.txt",
			compareText=f"{fname2}.txt",
			**convertArgs
		)

		for resFileName in resFiles:
			fpath1 = self.downloadFile(f"res/{resFileName}")
			fpath2 = resFilesPath[resFileName]
			self.compareBinaryFiles(fpath1, fpath2)

	def test_convert_slob_txt_1(self):
		self.convert_slob_txt(
			"100-en-fa-res",
			"100-en-fa-res-slob",
			resFiles=[
				"stardict.png",
				"test.json",
			],
		)

	def test_convert_slob_txt_2(self):
		self.convert_slob_txt(
			"100-en-fa-res",
			"100-en-fa-res-slob",
			resFiles=[
				"stardict.png",
				"test.json",
			],
			direct=False,
		)

	def test_convert_slob_txt_2(self):
		self.convert_slob_txt(
			"100-en-fa-res",
			"100-en-fa-res-slob",
			resFiles=[
				"stardict.png",
				"test.json",
			],
			sqlite=True,
		)

	def test_convert_slob_txt_2(self):
		self.convert_slob_txt(
			"100-en-fa-res",
			"100-en-fa-res-slob-sort",
			resFiles=[
				"stardict.png",
				"test.json",
			],
			sort=True,
		)


if __name__ == "__main__":
	unittest.main()
