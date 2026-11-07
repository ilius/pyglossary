import sys
import unittest
from os.path import abspath, dirname

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from pyglossary.plugins.quickdic6.quickdic import QuickDic

NORMALIZER_RULES = (
	":: Any-Latin; ' ' > ; :: Lower; :: NFD; :: [:Nonspacing Mark:] Remove; :: NFC ;"
)


class AddIndexTest(unittest.TestCase):
	def test_add_index(self):
		dic = QuickDic(
			name="test",
			sources=[],
			pairs=[
				(0, [("apple", "a"), ("Apple", "b")]),
				(1, [("apple", "c")]),
				(2, [("", "d"), ("  ", "e")]),
			],
			texts=[],
			htmls=[
				(0, "apple", "<div>0</div>"),
				(0, "apple", "<div>0b</div>"),
				(1, "Café", "<div>1</div>"),
			],
		)
		dic.indices = None
		dic.add_index(
			"en",
			"English",
			"en",
			NORMALIZER_RULES,
			synonyms={
				"apple": ["apfel", "", "apple"],
				"missing": ["ignored"],
			},
		)

		self.assertEqual(len(dic.indices), 1)
		(
			short_name,
			long_name,
			iso,
			normalizer_rules,
			swap_flag,
			main_token_count,
			index_entries,
			stop_list,
			rows,
		) = dic.indices[0]
		self.assertEqual(short_name, "en")
		self.assertEqual(long_name, "English")
		self.assertEqual(iso, "en")
		self.assertEqual(normalizer_rules, NORMALIZER_RULES)
		self.assertFalse(swap_flag)
		self.assertEqual(stop_list, [])
		self.assertEqual(main_token_count, len(index_entries))

		entries = {entry[0]: entry for entry in index_entries}
		self.assertNotIn("", entries)

		apple = entries["apple"]
		self.assertEqual(apple[3], "")
		self.assertEqual(apple[4], [0, 1])

		apple_upper = entries["Apple"]
		self.assertEqual(apple_upper[3], "apple")

		cafe = entries["Café"]
		self.assertEqual(cafe[3], "cafe")
		self.assertEqual(cafe[4], [2])

		apfel = entries["apfel"]
		self.assertEqual(apfel[4], [0, 1])

		self.assertNotIn("missing", entries)
		self.assertNotIn("ignored", entries)
		self.assertTrue(rows)

	def test_add_index_empty(self):
		dic = QuickDic(
			name="test",
			sources=[],
			pairs=[],
			texts=[],
			htmls=[],
		)
		dic.add_index("en", "English", "en", NORMALIZER_RULES)

		self.assertEqual(len(dic.indices), 1)
		self.assertEqual(dic.indices[0][6], [])
		self.assertEqual(dic.indices[0][7], [])
		self.assertEqual(dic.indices[0][8], [])


if __name__ == "__main__":
	unittest.main()
