import os
import unittest
from os.path import join

from glossary_v2_test import TestGlossaryBase

from pyglossary.glossary_v2 import ConvertArgs, Glossary


class TestGlossaryQuickDic6(TestGlossaryBase):
	def __init__(self, *args, **kwargs):
		TestGlossaryBase.__init__(self, *args, **kwargs)

		self.dataFileCRC32 |= {
			"100-en-de-v4.txt.quickdic": "9d4ccc13",
			"100-en-de-v4.txt.quickdic.txt": "2dc4fc17",
			"100-en-fa.txt.quickdic": "2bd483df",
			"100-en-fa.txt.quickdic.txt": "50994fb5",
		}

		os.environ["QUICKDIC_CREATION_TIME"] = "1730579400"

	@staticmethod
	def _readTxtHeadwords(filename: str) -> list[str]:
		glos = Glossary()
		try:
			glos.directRead(filename)
			return [entry.l_term[0] for entry in glos if not entry.isData()]
		finally:
			glos.cleanup()
			glos.clear()

	def convert_txt_quickdic(self, fname, sha1sum, **convertArgs):
		self.convert(
			f"{fname}.txt",
			f"{fname}-2.quickdic",
			sha1sum=sha1sum,
			**convertArgs,
		)

	def convert_quickdic_txt(self, fname, fname2, **convertArgs):
		self.convert(
			f"{fname}.quickdic",
			f"{fname}-2.txt",
			compareText=f"{fname2}.txt",
			**convertArgs,
		)

	def test_convert_txt_quickdic_1(self):
		self.convert_txt_quickdic(
			"100-en-de-v4",
			"c8d9694624bace08e6e999db75c9156776f257c9",
		)

	def test_convert_quickdic_txt_1(self):
		self.convert_quickdic_txt(
			"100-en-de-v4.txt",
			"100-en-de-v4.txt.quickdic",
		)

	def test_convert_txt_quickdic_2(self):
		self.convert_txt_quickdic(
			"100-en-fa",
			"371ac30d5ddedffe0a1c54b8a050aef62e5b91a5",
		)

	def test_convert_quickdic_txt_2(self):
		self.convert_quickdic_txt(
			"100-en-fa.txt",
			"100-en-fa.txt.quickdic",
		)

	def test_convert_txt_quickdic6_txt_preserves_order(self):
		# QuickDic 6 sorts its index, not the stored entries, so a round trip
		# keeps the source order.
		fname = "100-en-de-v4"
		expected = self._readTxtHeadwords(self.downloadFile(f"{fname}.txt"))
		# The source must not already be sorted, otherwise the test cannot
		# detect a reordering.
		self.assertNotEqual(expected, sorted(expected, key=str.lower))

		quickdicName = f"{fname}-roundtrip.quickdic"
		self.convert(
			f"{fname}.txt",
			quickdicName,
		)

		outputFilename = self.newTempFilePath(f"{fname}-roundtrip.txt")
		glos = self.glos = Glossary()
		glos.convert(
			ConvertArgs(
				inputFilename=join(self.tempDir, quickdicName),
				outputFilename=outputFilename,
			),
		)
		self.assertEqual(self._readTxtHeadwords(outputFilename), expected)

	def test_convert_txt_quickdic6_sort_writes_sorted_entries(self):
		# With --sort, entries are sorted before writing, so the stored
		# order and the round-trip output follow the sorted order.
		fname = "100-en-de-v4"
		self.convert(
			f"{fname}.txt",
			f"{fname}-sorted.txt",
			sort=True,
		)
		expected = self._readTxtHeadwords(join(self.tempDir, f"{fname}-sorted.txt"))
		self.assertEqual(len(expected), 100)

		self.convert(
			f"{fname}.txt",
			f"{fname}-sorted.quickdic",
			sort=True,
		)
		outputFilename = self.newTempFilePath(f"{fname}-sorted-roundtrip.txt")
		glos = self.glos = Glossary()
		glos.convert(
			ConvertArgs(
				inputFilename=join(self.tempDir, f"{fname}-sorted.quickdic"),
				outputFilename=outputFilename,
			),
		)
		self.assertEqual(self._readTxtHeadwords(outputFilename), expected)


if __name__ == "__main__":
	unittest.main()
