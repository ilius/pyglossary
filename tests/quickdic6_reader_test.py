import sys
import unittest
from os.path import abspath, dirname

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from pyglossary.plugins.quickdic6.reader import Reader


class ExtractRowsTest(unittest.TestCase):
	def test_deep_chain(self):
		# Some dictionaries contain very deep chains of index entries.
		count = 2000
		index_entries = []
		rows = []
		for i in range(count):
			start_index = len(rows)
			rows.append((1, i))
			rows.append((1, i + 1) if i + 1 < count else (0, 42))
			index_entries.append((f"t{i}", start_index, 1, "", []))

		index = (
			"en",
			"en",
			"en",
			"",
			False,
			0,
			index_entries,
			[],
			rows,
		)
		reader = Reader(None)
		self.assertEqual(
			reader._extract_rows_from_indexentry(index, 0),
			[(0, 42)],
		)


if __name__ == "__main__":
	unittest.main()
