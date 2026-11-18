from __future__ import annotations

import os
import shutil
import unittest
from os.path import join
from unittest import mock

from glossary_v2_test import TestGlossaryBase

from pyglossary.glossary_v2 import Glossary
from pyglossary.plugin_lib import readmdict
from pyglossary.plugins.octopus_mdict.reader import Reader

FIXTURE = "8-en-en.mdx"
LINKS_FIXTURE = "5-en-en-links.mdx"
NOTITLE_FIXTURE = "2-en-en-title-placeholder.mdx"


def _entries(
	glos: Glossary,
) -> tuple[list[tuple[tuple[str, ...], str]], dict[str, bytes]]:
	rows: list[tuple[tuple[str, ...], str]] = []
	data: dict[str, bytes] = {}
	for entry in glos:
		if entry.isData():
			data[entry.getFileName()] = entry.data
		else:
			rows.append((tuple(entry.l_term), entry.defi))
	return rows, data


class TestGlossaryOctopusMdict(TestGlossaryBase):
	def __init__(self, *args, **kwargs):
		TestGlossaryBase.__init__(self, *args, **kwargs)

		self.dataFile |= {
			FIXTURE,
			"8-en-en.mdd",
			LINKS_FIXTURE,
			"5-en-en-links.mdd",
			NOTITLE_FIXTURE,
			"2-en-en-no-title.mdx",
		}

	def _read(self, filename: str, **readOptions) -> Glossary:
		glos = self.glos = Glossary()
		glos.directRead(
			self.downloadFile(filename),
			formatName="OctopusMdict",
			**readOptions,
		)
		return glos

	def test_read_fixture(self):
		glos = self._read(FIXTURE)
		rows, data = _entries(glos)

		self.assertEqual(len(rows) + len(data), 8)
		self.assertEqual(
			rows,
			[
				(
					("apple",),
					'<a href="fruit">see fruit</a> <img src=".img/icon.png"> <audio controls src="audio/hello.mp3"></audio>',
				),
				(("banana",), "<b>yellow</b> fruit"),
				(("cherry",), "red fruit"),
				(("date",), "sweet fruit"),
				(("elderberry",), "dark berry"),
				(
					("pomme",),
					'<a href="fruit">see fruit</a> <img src=".img/icon.png"> <audio controls src="audio/hello.mp3"></audio>',
				),
			],
		)
		self.assertEqual(
			data,
			{
				"audio/hello.mp3": b"ID3fixture",
				"img/icon.png": b"\x89PNG\r\n\x1a\nfixture",
			},
		)
		self.assertEqual(glos.getInfo("name"), "PyGlossary MDict Test")
		self.assertEqual(
			glos.getInfo("description"),
			'Minimal fixture for PyGlossary tests <&>"',
		)

	def test_read_links_fixture(self):
		glos = self._read(LINKS_FIXTURE)
		rows, data = _entries(glos)

		self.assertEqual(len(rows) + len(data), 5)
		self.assertEqual(
			rows,
			[
				(
					("main", "alias1", "alias2"),
					(
						'<a href="bword://other">other</a> '
						"<a href='bword://def'>d</a> "
						'<a href="bword://thing">x</a> '
						'<img src=".img/icon.png"> '
						'<a href="sound://audio/hello.mp3">listen</a>'
					),
				),
				(("other", "linker"), "other definition"),
			],
		)
		self.assertEqual(
			data,
			{
				"audio/hello.mp3": b"ID3links",
				"img/icon.png": b"\x89PNG\r\n\x1a\nlinks",
				"nested/zero.bin": b"\x00",
			},
		)

	def test_read_audio(self):
		glos = self._read(LINKS_FIXTURE, audio=True)
		rows, _data = _entries(glos)

		self.assertIn(
			'<audio controls src="audio/hello.mp3"></audio>',
			rows[0][1],
		)
		self.assertNotIn("sound://", rows[0][1])

	def test_read_no_title(self):
		glos = self._read(NOTITLE_FIXTURE)
		rows, data = _entries(glos)

		self.assertEqual(rows, [(("alpha",), "first"), (("beta",), "second")])
		self.assertEqual(data, {})
		self.assertNotEqual(glos.getInfo("name"), "Title (No HTML code allowed)")

	def test_read_no_title_header(self):
		glos = self._read("2-en-en-no-title.mdx")
		rows, data = _entries(glos)

		self.assertEqual(rows, [(("alpha",), "first"), (("beta",), "second")])
		self.assertEqual(data, {})
		self.assertNotEqual(glos.getInfo("name"), "Title (No HTML code allowed)")

	def test_load_links_on_closed_reader(self):
		glos = self.glos = Glossary()
		reader = Reader(glos)
		reader.open(self.downloadFile(FIXTURE))
		reader.close()

		with self.assertRaises(ValueError):
			reader.loadLinks()

	def test_read_same_dir_data_files(self):
		srcMdx = self.downloadFile(FIXTURE)
		dirPath = join(self.tempDir, "same-dir")
		os.makedirs(dirPath)
		shutil.copyfile(srcMdx, join(dirPath, FIXTURE))
		shutil.copyfile(
			self.downloadFile("8-en-en.mdd"),
			join(dirPath, "8-en-en.mdd"),
		)
		with open(join(dirPath, "extra.txt"), "wb") as file:
			file.write(b"extra resource")
		os.makedirs(join(dirPath, "subdir"))

		glos = self.glos = Glossary()
		glos.directRead(
			join(dirPath, FIXTURE),
			formatName="OctopusMdict",
			same_dir_data_files=True,
		)
		_rows, data = _entries(glos)

		self.assertEqual(data["extra.txt"], b"extra resource")
		self.assertIn("audio/hello.mp3", data)
		self.assertIn("img/icon.png", data)
		self.assertNotIn("subdir", data)

	def test_read_broken_mdd(self):
		class BrokenMdd:
			filename = "broken.mdd"

			def __len__(self):
				return 0

			def items(self):
				raise RuntimeError("broken mdd")

		srcMdx = self.downloadFile(FIXTURE)
		dirPath = join(self.tempDir, "broken-mdd")
		os.makedirs(dirPath)
		shutil.copyfile(srcMdx, join(dirPath, FIXTURE))
		with open(join(dirPath, "8-en-en.mdd"), "wb") as file:
			file.write(b"broken")

		glos = self.glos = Glossary()
		with mock.patch.object(readmdict, "MDD", return_value=BrokenMdd()):
			glos.directRead(join(dirPath, FIXTURE), formatName="OctopusMdict")
			rows, data = _entries(glos)

		self.assertEqual(len(rows), 6)
		self.assertEqual(data, {})

	def test_read_multiple_mdd(self):
		srcMdx = self.downloadFile(FIXTURE)
		srcMdd = self.downloadFile("8-en-en.mdd")
		dirPath = join(self.tempDir, "multi-mdd")
		os.makedirs(dirPath)
		shutil.copyfile(srcMdx, join(dirPath, FIXTURE))
		for name in ("8-en-en.mdd", "8-en-en.1.mdd", "8-en-en.2.mdd"):
			shutil.copyfile(srcMdd, join(dirPath, name))

		glos = self.glos = Glossary()
		glos.directRead(join(dirPath, FIXTURE), formatName="OctopusMdict")
		rows, data = _entries(glos)

		self.assertEqual(len(rows), 6)
		self.assertEqual(
			sorted(data),
			["audio/hello.mp3", "img/icon.png"],
		)

	def test_reader_len_count_and_close(self):
		glos = self.glos = Glossary()
		reader = Reader(glos)
		filename = self.downloadFile(FIXTURE)
		reader.open(filename)

		self.assertEqual(len(reader), 8)
		self.assertEqual(reader.countResourceFiles(), 0)
		self.assertEqual(len(list(reader)), 8)
		self.assertEqual(len(list(reader)), 0)
		reader.close()

	def test_iterate_closed_reader(self):
		glos = self._read(FIXTURE)
		self.assertEqual(len(list(glos)), 8)
		self.assertEqual(list(glos), [])


if __name__ == "__main__":
	unittest.main()
