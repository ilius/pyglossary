import os
import unittest
from os.path import join

from glossary_v2_test import TestGlossaryBase

from pyglossary.glossary_v2 import Glossary
from pyglossary.plugins.quickdic6.reader import Reader


class TestQuickDic6SortModule(TestGlossaryBase):
	@staticmethod
	def _readTxtHeadwords(filename: str) -> list[str]:
		glos = Glossary()
		try:
			glos.directRead(filename)
			return [entry.l_term[0] for entry in glos if not entry.isData()]
		finally:
			glos.cleanup()
			glos.clear()

	def test_sort_key_quickdic6_matches_index_order(self):
		# This fixture has no duplicate headwords or alternate headwords.
		fname = "100-en-de-v4"
		self.convert(
			f"{fname}.txt",
			f"{fname}-sort-key.quickdic",
		)
		dic = Reader.quickdic_from_path(
			join(self.tempDir, f"{fname}-sort-key.quickdic"),
		)
		expected = [entry[0] for entry in dic.indices[0][6]]
		self.assertEqual(len(expected), 100)
		self.assertEqual(len(expected), len(set(expected)))

		for sqlite in (None, True, False):
			outputName = f"{fname}-sort-key-{sqlite}.txt"
			self.convert(
				f"{fname}.txt",
				outputName,
				sort=True,
				sortKeyName="quickdic6",
				sqlite=sqlite,
			)
			self.assertEqual(
				self._readTxtHeadwords(join(self.tempDir, outputName)),
				expected,
				msg=f"{sqlite=}",
			)

		os.environ["NO_SQLITE"] = "1"
		try:
			outputName = f"{fname}-sort-key-nosqlite.txt"
			self.convert(
				f"{fname}.txt",
				outputName,
				sort=True,
				sortKeyName="quickdic6",
				sqlite=False,
			)
			self.assertEqual(
				self._readTxtHeadwords(join(self.tempDir, outputName)),
				expected,
			)
		finally:
			del os.environ["NO_SQLITE"]


if __name__ == "__main__":
	unittest.main()
