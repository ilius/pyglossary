import gzip
import logging
from pathlib import Path

from glossary_v2_errors_test import TestGlossaryErrorsBase

from pyglossary.os_utils import runDictzip

TEXT = """
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor
incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis
nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu
fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in
culpa qui officia deserunt mollit anim id est laborum.
"""
MISSING_DEP_MARK = "Dictzip compression requires idzip module or dictzip utility,"


class TestDictzip(TestGlossaryErrorsBase):
	def setUp(self) -> None:
		super().setUp()
		self.test_file_path = Path(self.tempDir) / "test_file.txt"
		filename = self.test_file_path.name + ".dz"
		self.result_file_path = self.test_file_path.parent / filename
		with open(self.test_file_path, "a") as tmp_file:
			tmp_file.write(TEXT)

	def skip_on_dep(self, method: str) -> None:
		warn = self.mockLog.popLog(logging.WARNING, MISSING_DEP_MARK, partial=True)
		if warn:
			self.skipTest(f"Missing {method} dependency")

	def test_idzip_compressed_exists(self) -> None:
		method = "idzip"
		runDictzip(self.test_file_path, method)
		self.skip_on_dep(method)
		self.assertTrue(self.result_file_path.exists())
		self.assertTrue(self.result_file_path.is_file())

	def test_idzip_compressed_matches(self) -> None:
		method = "idzip"
		runDictzip(self.test_file_path, method)
		self.skip_on_dep(method)
		with gzip.open(self.result_file_path, "r") as file:
			result = file.read().decode()
		self.assertEqual(result, TEXT)

	def test_dictzip_compressed_exists(self) -> None:
		method = "dictzip"
		runDictzip(self.test_file_path, method)
		self.skip_on_dep(method)
		self.assertTrue(self.result_file_path.exists())
		self.assertTrue(self.result_file_path.is_file())

	def test_dictzip_compressed_matches(self) -> None:
		method = "dictzip"
		runDictzip(self.test_file_path, method)
		self.skip_on_dep(method)
		with gzip.open(self.result_file_path, "r") as file:
			result = file.read().decode()
		self.assertEqual(result, TEXT)

	def test_dictzip_missing_target(self) -> None:
		method = "idzip"
		filename = "/NOT_EXISTED_PATH/file.txt"
		expected = f"No such file or directory: '{filename}'"
		runDictzip(filename, method)
		self.skip_on_dep(method)
		err = self.mockLog.popLog(logging.ERROR, expected, partial=True)
		self.assertIsNotNone(err)

	def test_idzip_missing_target(self) -> None:
		method = "dictzip"
		filename = "/NOT_EXISTED_PATH/boilerplate.txt"
		expected = f'Cannot open "{filename}"'
		runDictzip(filename, method)
		self.skip_on_dep(method)
		err = self.mockLog.popLog(logging.ERROR, expected, partial=True)
		self.assertIsNotNone(err)
