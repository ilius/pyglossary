from __future__ import annotations

import os
import shutil
import sys
import unittest
from os.path import abspath, dirname, join
from pathlib import Path

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from glossary_v2_test import TestGlossaryBase, testLocalDataDir

from pyglossary.glossary_v2 import ConvertArgs, Glossary

FIXTURE_NAME = "225-ja-ja-epwing"


class TestGlossaryEpwing(TestGlossaryBase):
	def convert_epwing(self, inputFilename: str, outputName: str):
		outputFilePath = self.newTempFilePath(outputName)
		self.glos = Glossary()
		return self.glos.convert(
			ConvertArgs(
				inputFilename=inputFilename,
				outputFilename=outputFilePath,
				inputFormat="EPWING",
				outputFormat="Tabfile",
			)
		)

	def assert_convert_fails(self, inputFilename: str, outputName: str) -> None:
		with self.assertRaises(RuntimeError):
			self.convert_epwing(inputFilename, outputName)

	def copy_fixture(self, name: str) -> str:
		return shutil.copytree(
			join(testLocalDataDir, FIXTURE_NAME),
			join(self.tempDir, name),
		)

	def patch(self, path: str, offset: int, data: bytes) -> None:
		file_path = Path(path)
		if offset < 0:
			content = file_path.read_bytes()
			start = len(content) + offset
			end = start + len(data)
			file_path.write_bytes(content[:start] + data + content[end:])
			return
		with open(path, "r+b") as file:
			file.seek(offset)
			file.write(data)

	def test_convert_epwing_txt(self):
		inputDirPath = join(testLocalDataDir, FIXTURE_NAME)
		outputFilePath = self.newTempFilePath(f"{FIXTURE_NAME}.txt")

		result = self.convert_epwing(inputDirPath, f"{FIXTURE_NAME}.txt")
		self.assertEqual(result, outputFilePath)

		self.compareTextFiles(
			outputFilePath,
			join(testLocalDataDir, f"{FIXTURE_NAME}.txt"),
		)

	def test_convert_catalogs_file(self):
		inputPath = join(testLocalDataDir, FIXTURE_NAME, "CATALOGS")
		self.convert_epwing(inputPath, "from-catalogs-file.txt")
		self.compareTextFiles(
			join(self.tempDir, "from-catalogs-file.txt"),
			join(testLocalDataDir, f"{FIXTURE_NAME}.txt"),
		)

	def test_convert_lowercase_catalogs(self):
		inputDirPath = self.copy_fixture("lowercase-catalogs")
		shutil.move(
			join(inputDirPath, "CATALOGS"),
			join(inputDirPath, "catalogs"),
		)
		self.convert_epwing(inputDirPath, "lowercase-catalogs.txt")
		self.compareTextFiles(
			join(self.tempDir, "lowercase-catalogs.txt"),
			join(testLocalDataDir, f"{FIXTURE_NAME}.txt"),
		)

	def test_convert_invalid_input(self):
		with self.assertRaises(ValueError):
			self.convert_epwing(
				join(testLocalDataDir, f"{FIXTURE_NAME}.txt"),
				"invalid-input.txt",
			)

	def test_convert_missing_catalogs(self):
		inputDirPath = self.copy_fixture("missing-catalogs")
		os.remove(join(inputDirPath, "CATALOGS"))
		with self.assertRaises(ValueError):
			self.convert_epwing(inputDirPath, "missing-catalogs.txt")

	def test_convert_corrupt_books(self):
		def shared_honmon(path: str) -> Path:
			return Path(path, "SHARED", "DATA", "HONMON")

		def patch_shared(offset: int, data: bytes):
			return lambda path: self.patch(str(shared_honmon(path)), offset, data)

		def set_overflowing_leaf(path: str):
			honmon_path = shared_honmon(path)
			content = bytearray(honmon_path.read_bytes())
			page = bytearray(2048)
			page[0] = 0xA0
			page[1] = 0xFF
			page[2:4] = (8).to_bytes(2, "big")
			position = (8).to_bytes(4, "big") + bytes(2)
			for index in range(7):
				offset = 4 + index * (0xFF + 12)
				page[offset + 0xFF : offset + 0xFF + 6] = position
				page[offset + 0xFF + 6 : offset + 0xFF + 12] = position
			content[6 * 2048 : 7 * 2048] = page
			honmon_path.write_bytes(content)

		def set_compression(path: str):
			with open(join(path, "CATALOGS"), "rb") as file:
				count = int.from_bytes(file.read(2), "big")
			extra_offset = 16 + count * 164
			self.patch(
				join(path, "CATALOGS"),
				extra_offset + 55,
				b"\x01",
			)

		def set_invalid_character(path: str):
			honmon_path = shared_honmon(path)
			content = bytearray(honmon_path.read_bytes())
			marker = b"\x1f\x02AB\x1f\x03"
			offset = content.index(marker)
			content[offset + 3] = 0x20
			honmon_path.write_bytes(content)

		cases = [
			(
				"missing-subbook",
				lambda path: shutil.rmtree(join(path, "SHARED")),
			),
			(
				"short-catalogs",
				lambda path: Path(path, "CATALOGS").write_bytes(b"\0" * 15),
			),
			(
				"bad-catalog-count",
				lambda path: Path(path, "CATALOGS").write_bytes(
					(1).to_bytes(2, "big") + bytes(14),
				),
			),
			("compressed-honmon", set_compression),
			(
				"empty-honmon",
				lambda path: shared_honmon(path).write_bytes(b""),
			),
			("invalid-index-count", patch_shared(1, b"\x80")),
			(
				"empty-index-page",
				patch_shared(2048 + 2, b"\0\0"),
			),
			(
				"index-too-deep",
				patch_shared(2048 + 5, (2).to_bytes(4, "big")),
			),
			("expected-leaf", patch_shared(6 * 2048, b"\x00")),
			("invalid-group-id", patch_shared(5 * 2048 + 10, b"\x42")),
			("overflowing-leaf", set_overflowing_leaf),
			(
				"invalid-page-number",
				patch_shared(18, (999).to_bytes(4, "big")),
			),
			(
				"truncated-control",
				lambda path: self.patch(
					str(shared_honmon(path)),
					-3,
					b"\x1f\x1f\x1f",
				),
			),
			("invalid-character", set_invalid_character),
		]

		for name, mutate in cases:
			with self.subTest(name):
				inputDirPath = self.copy_fixture(name)
				mutate(inputDirPath)
				self.assert_convert_fails(inputDirPath, f"{name}.txt")


if __name__ == "__main__":
	unittest.main()
