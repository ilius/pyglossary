import logging
import sys

skip_module = False
if sys.version_info < (3, 10):
	logging.getLogger("pyglossary-test").warning(
		f"Skipping {__file__} due to old Python version (need 3.10).",
	)
	skip_module = True

import os
import unittest

from glossary_v2_test import TestGlossaryBase


class TestGlossarySlob(TestGlossaryBase):
	def __init__(self, *args, **kwargs):
		TestGlossaryBase.__init__(self, *args, **kwargs)

		self.dataFileCRC32.update(
			{
				"100-en-fa-res.slob": "0216d006",
				"100-en-fa-res-slob.txt": "c73100b3",
				"100-en-fa-res-slob-sort.txt": "8253fe96",
				"300-ru-en.txt": "77cfee2f",
			},
		)

	def setUp(self):
		if skip_module:
			self.skipTest("module is skipped")
		TestGlossaryBase.setUp(self)

	def test_convert_txt_slob_1(self):
		fname = "100-en-fa"
		os.environ["SLOB_TIMESTAMP"] = "2023-01-01T12:00:00.000000+00:00"
		self.convert(
			f"{fname}.txt",
			f"{fname}.slob",
			# sha1sum="",
			# compareBinary="",
			# slob file is different each time (and so its sha1sum and md5sum)
			# even with same exact tags!
			# writeOptions={"compression": ""},
		)

	def test_convert_txt_slob_2_file_size_approx(self):
		fname = "300-ru-en"
		file_size_approx = 25000
		files = [
			(35852, self.newTempFilePath("300-ru-en.slob")),
			(35687, self.newTempFilePath("300-ru-en.1.slob")),
			(33856, self.newTempFilePath("300-ru-en.2.slob")),
			(29413, self.newTempFilePath("300-ru-en.3.slob")),
		]
		self.convert(
			f"{fname}.txt",
			f"{fname}.slob",
			writeOptions={
				"file_size_approx": file_size_approx,
				"file_size_approx_check_num_entries": 1,
			},
			compareBinary="",
			# slob file is different each time (and so its sha1sum and md5sum)
		)
		for size, fpath in files:
			with open(fpath, mode="rb") as _file:
				actualSize = len(_file.read())
			delta = actualSize - size
			self.assertLess(
				delta,
				100,
				msg=f"size expected={size} actual={actualSize}, file {fpath}",
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
			**convertArgs,
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

	def test_convert_slob_txt_3(self):
		self.convert_slob_txt(
			"100-en-fa-res",
			"100-en-fa-res-slob",
			resFiles=[
				"stardict.png",
				"test.json",
			],
			sqlite=True,
		)

	def test_convert_slob_txt_4(self):
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
