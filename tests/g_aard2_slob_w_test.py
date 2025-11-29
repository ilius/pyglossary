import os
import unittest

from glossary_v2_test import TestGlossaryBase


class TestGlossarySlobWrite(TestGlossaryBase):
	def __init__(self, *args, **kwargs):
		TestGlossaryBase.__init__(self, *args, **kwargs)

		self.dataFileCRC32.update(
			{
				"300-ru-en.txt": "77cfee2f",
			},
		)

	def setUp(self):
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
		if os.getenv("SKIP_TEST_SLOB_WRITE_FILE_SIZE_APPROX"):
			print("skipping test_convert_txt_slob_2_file_size_approx")
			return
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
			with open(fpath, mode="rb") as file:
				actualSize = len(file.read())
			delta = actualSize - size
			self.assertLess(
				delta,
				100,
				msg=f"size expected={size} actual={actualSize}, file {fpath}",
			)


if __name__ == "__main__":
	unittest.main()
