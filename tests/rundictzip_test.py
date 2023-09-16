import gzip
import tempfile
from pathlib import Path

from glossary_errors_test import TestGlossaryErrorsBase

from pyglossary.os_utils import runDictzip

TEXT = """
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor
incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis
nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu
fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in
culpa qui officia deserunt mollit anim id est laborum.
"""


class AsciiLowerUpperTest(TestGlossaryErrorsBase):
	def make_dz(self, path: Path) -> Path:
		"""Get path of dzipped file contains TEXT."""
		test_file_path = Path(path)/"test_file.txt"
		result_file_path = test_file_path.parent/(test_file_path.name + ".dz")
		with open(test_file_path, "a") as tmp_file:
			tmp_file.write(TEXT)
		runDictzip(str(test_file_path))
		return result_file_path

	def test_compressed_exists(self):
		with tempfile.TemporaryDirectory() as tmp_dir:
			result_file_path = self.make_dz(tmp_dir)
			self.assertTrue(result_file_path.exists())
			self.assertTrue(result_file_path.is_file())

	def test_compressed_matches(self):
		with tempfile.TemporaryDirectory() as tmp_dir:
			result_file_path = self.make_dz(tmp_dir)
			with gzip.open(result_file_path, 'r') as file:
				result = file.read().decode()
		self.assertEqual(result, TEXT)

	def test_missing_target(self):
		filename = 'NOT_EXISTED_PATH/file.txt'
		expected_msg = f"{filename} is not a regular file"
		runDictzip(filename)
		self.assertLogError(expected_msg)
