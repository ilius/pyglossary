import os
import unicodedata
import unittest
from typing import TYPE_CHECKING, cast

from glossary_v2_test import TestGlossaryBase

from pyglossary.plugins.aard2_slob._slob_obj import Slob
from pyglossary.plugins.aard2_slob._writer import Writer as SlobWriter

if TYPE_CHECKING:
	from pyglossary.plugins.aard2_slob._blob import Blob


class TestGlossarySlobWrite(TestGlossaryBase):
	def __init__(self, *args, **kwargs):
		TestGlossaryBase.__init__(self, *args, **kwargs)

		self.dataFileCRC32 |= {
			"300-ru-en.txt": "77cfee2f",
		}

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

	def test_finalize_resolve_aliases(self):
		path = os.path.join(self.tempDir, "aliases.slob")
		too_many_redirects = []
		target_not_found = []

		def observer(event):
			if event.name == "too_many_redirects":
				too_many_redirects.append(event.data)
			elif event.name == "alias_target_not_found":
				target_not_found.append(event.data)

		w = SlobWriter(path, observer=observer)
		data = ["z", "b", "q", "a", "u", "g", "p", "n"]
		for k in data:
			value = ";".join(unicodedata.name(c) for c in k)
			w.add(value.encode("ascii"), k)

		w.add_alias("w", "u")
		w.add_alias("small u", "u")
		w.add_alias("y1", "y2")
		w.add_alias("y2", "y3")
		w.add_alias("y3", "z")
		w.add_alias("ZZZ", "YYY")

		w.add_alias("l3", "l1")
		w.add_alias("l1", "l2")
		w.add_alias("l2", "l3")

		w.add_alias("a1", ("a", "a-frag1"))
		w.add_alias("a2", "a1")
		w.add_alias("a3", ("a2", "a-frag2"))

		w.add_alias("g1", "g")
		w.add_alias("g2", ("g1", "g-frag1"))

		w.add_alias("n or p", "n")
		w.add_alias("n or p", "p")

		w.finalize()

		self.assertEqual(set(too_many_redirects), {"l1", "l2", "l3"})
		self.assertEqual(
			set(target_not_found),
			{"l1", "l2", "l3", "YYY"},
		)

		with Slob(path) as reader:
			d = reader.as_dict()

			def get(key):
				return [item.content.decode("ascii") for item in d[key]]

			self.assertEqual(get("w"), ["LATIN SMALL LETTER U"])
			self.assertEqual(get("small u"), ["LATIN SMALL LETTER U"])
			self.assertEqual(get("y1"), ["LATIN SMALL LETTER Z"])
			self.assertEqual(get("y2"), ["LATIN SMALL LETTER Z"])
			self.assertEqual(get("y3"), ["LATIN SMALL LETTER Z"])
			self.assertEqual(get("ZZZ"), [])
			self.assertEqual(get("l1"), [])
			self.assertEqual(get("l2"), [])
			self.assertEqual(get("l3"), [])
			self.assertEqual(len(list(d["n or p"])), 2)

			item_a1 = cast("Blob", next(d["a1"]))
			self.assertEqual(item_a1.content, b"LATIN SMALL LETTER A")
			self.assertEqual(item_a1.fragment, "a-frag1")

			item_a2 = cast("Blob", next(d["a2"]))
			self.assertEqual(item_a2.content, b"LATIN SMALL LETTER A")
			self.assertEqual(item_a2.fragment, "a-frag1")

			item_a3 = cast("Blob", next(d["a3"]))
			self.assertEqual(item_a3.content, b"LATIN SMALL LETTER A")
			self.assertEqual(item_a3.fragment, "a-frag1")

			item_g1 = cast("Blob", next(d["g1"]))
			self.assertEqual(item_g1.content, b"LATIN SMALL LETTER G")
			self.assertEqual(item_g1.fragment, "")

			item_g2 = cast("Blob", next(d["g2"]))
			self.assertEqual(item_g2.content, b"LATIN SMALL LETTER G")
			self.assertEqual(item_g2.fragment, "g-frag1")

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
