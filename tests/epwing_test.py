from __future__ import annotations

import sys
import tempfile
import unittest
from os.path import abspath, dirname
from pathlib import Path

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from pyglossary.plugins.epwing.converter import (
	EpwingBook,
	EpwingExtractor,
	EpwingSubbook,
)

PAGE_SIZE = 2048


def jis(text: str) -> bytes:
	encoded = text.encode("euc_jp")
	return bytes(byte & 0x7F for byte in encoded)


def put_position(page: bytearray, offset: int, position: tuple[int, int]) -> None:
	page[offset : offset + 4] = position[0].to_bytes(4, "big")
	page[offset + 4 : offset + 6] = position[1].to_bytes(2, "big")


def put_content(page: bytearray, offset: int, content: bytes) -> None:
	page[offset : offset + len(content)] = content


def make_book(path: Path) -> None:
	title = jis("広辞苑　第四版")
	catalog = bytearray(16 + 2 * 164)
	catalog[:2] = (1).to_bytes(2, "big")
	catalog[2:4] = (3).to_bytes(2, "big")
	record = memoryview(catalog)[16:180]
	record[2 : 2 + len(title)] = title
	record[82:90] = b"KOUJIEN "
	record[94:96] = (1).to_bytes(2, "big")
	extra = memoryview(catalog)[180:344]
	extra[4:12] = b"HONMON  "
	path.joinpath("CATALOGS").write_bytes(catalog)

	data_dir = path / "KOUJIEN" / "DATA"
	data_dir.mkdir(parents=True)
	pages = [bytearray(PAGE_SIZE) for _ in range(6)]

	# Index table: grouped, fixed-length, and variable-length word indexes.
	pages[0][1] = 3
	for index, (index_id, start_page) in enumerate(((0x90, 3), (0x91, 5), (0x92, 6))):
		offset = 16 + index * 16
		pages[0][offset] = index_id
		pages[0][offset + 2 : offset + 6] = start_page.to_bytes(4, "big")
		pages[0][offset + 6 : offset + 10] = (1).to_bytes(4, "big")

	heading1 = (2, 10)
	text1 = (2, 100)
	heading2 = (2, 300)
	text2 = (2, 400)
	put_content(pages[1], heading1[1], b"\x1f\x02" + jis("あ") + b"\x1f\x0a")
	put_content(pages[1], heading2[1], b"\x1f\x02" + jis("い") + b"\x1f\x0a")
	entry_start = b"\x1f\x09\x00\x01\x1f\x41\x01\x30"
	entry_end = b"\x1f\x09\x00\x01\x1f\x41\x01\x30"
	put_content(
		pages[1],
		text1[1],
		entry_start
		+ jis("説明")
		+ b"\x1f\x0a\x1f\x04"
		+ jis("Ａ！")
		+ b"\x1f\x05\x1f\x39"
		+ bytes(44)
		+ jis("後")
		+ b"\x1f\x3c"
		+ bytes(18)
		+ jis("先")
		+ b"\xa1\x21"
		+ entry_end,
	)
	put_content(pages[1], text2[1], entry_start + jis("本文") + entry_end)

	# Intermediate fixed-length index leading to a grouped leaf.
	pages[2][0] = 0x00
	pages[2][1] = 2
	pages[2][2:4] = (1).to_bytes(2, "big")
	pages[2][4:6] = jis("あ")
	pages[2][6:10] = (4).to_bytes(4, "big")
	pages[3][0] = 0xB0
	pages[3][2:4] = (2).to_bytes(2, "big")
	pages[3][4:10] = b"\x80\x02\x00\x00" + jis("あ")
	pages[3][10:14] = b"\xc0\x02" + jis("あ")
	put_position(pages[3], 14, text1)
	put_position(pages[3], 20, heading1)

	# Fixed-length leaf repeats the same article position and must be deduplicated.
	pages[4][0] = 0xA0
	pages[4][1] = 2
	pages[4][2:4] = (1).to_bytes(2, "big")
	pages[4][4:6] = jis("あ")
	put_position(pages[4], 6, text1)
	put_position(pages[4], 12, heading1)

	# Variable-length leaf points to another article.
	pages[5][0] = 0xA0
	pages[5][2:4] = (1).to_bytes(2, "big")
	pages[5][4] = 2
	pages[5][5:7] = jis("い")
	put_position(pages[5], 7, text2)
	put_position(pages[5], 13, heading2)

	data_dir.joinpath("HONMON").write_bytes(b"".join(pages))


class EpwingTest(unittest.TestCase):
	def test_uncompressed_entries(self) -> None:
		with tempfile.TemporaryDirectory() as temp_dir:
			path = Path(temp_dir)
			make_book(path)
			book = EpwingBook(str(path))

			self.assertEqual(book.subbooks[0].title, "広辞苑　第四版")
			self.assertEqual(
				list(book.subbooks[0].entries()),
				[
					{"heading": "い", "text": "本文"},
					{"heading": "あ", "text": "説明\nA!後先{{w_41249}}"},
				],
			)

	def test_compressed_honmon_is_rejected(self) -> None:
		subbook = EpwingSubbook("unused", "unused", 1, "HONMON", 0x11)
		with self.assertRaisesRegex(NotImplementedError, "Compressed EPWING"):
			list(subbook.entries())

	def test_unknown_gaiji_is_replaced(self) -> None:
		self.assertEqual(EpwingExtractor().translate("{{w_12345}}"), "�")


if __name__ == "__main__":
	unittest.main()
