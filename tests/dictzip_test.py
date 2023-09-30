import gzip
import tempfile
from functools import partialmethod
from pathlib import Path
from typing import Callable

from glossary_errors_test import TestGlossaryErrorsBase

from pyglossary.os_utils import _dictzip, _idzip

FUNC_TYPE = Callable[[str], bool]

TEXT = """
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor
incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis
nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu
fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in
culpa qui officia deserunt mollit anim id est laborum.
"""


class TestDictzipBase(TestGlossaryErrorsBase):
	def _run(self, func: FUNC_TYPE, filename: str | Path) -> None:
		done = func(str(filename))
		if not done:
			self.skipTest(f'Missing dependency for {func.__name__}')


class TestDictzip(TestDictzipBase):
	def make_dz(self, func: FUNC_TYPE, path: str | Path) -> Path:
		"""Get path of dzipped file contains TEXT."""
		test_file_path = Path(path)/"test_file.txt"
		result_file_path = test_file_path.parent/(test_file_path.name + ".dz")
		with open(test_file_path, "a") as tmp_file:
			tmp_file.write(TEXT)
		self._run(func, test_file_path)
		return result_file_path

	def is_compressed_exists(self, func: FUNC_TYPE) -> None:
		with tempfile.TemporaryDirectory() as tmp_dir:
			result_file_path = self.make_dz(func, tmp_dir)
			self.assertTrue(result_file_path.exists())
			self.assertTrue(result_file_path.is_file())

	def is_compressed_matches(self, func: FUNC_TYPE) -> None:
		with tempfile.TemporaryDirectory() as tmp_dir:
			result_file_path = self.make_dz(func, tmp_dir)
			with gzip.open(result_file_path, 'r') as file:
				result = file.read().decode()
		self.assertEqual(result, TEXT)

	test_idzip_compressed_exists = partialmethod(is_compressed_exists, _idzip)
	test_idzip_compressed_matches = partialmethod(is_compressed_matches, _idzip)

	test_dictzip_compressed_exists = partialmethod(is_compressed_exists, _dictzip)
	test_dictzip_compressed_matches = partialmethod(is_compressed_matches, _dictzip)


class TestDictzipErrors(TestDictzipBase):
	def tearDown(self):
		self.mockLog.clear()
		super().tearDown()

	def on_missing_target(self, func: FUNC_TYPE) -> None:
		filename = '/NOT_EXISTED_PATH/file.txt'
		self._run(func, filename)
		err_num = self.mockLog.printRemainingErrors()
		self.assertEqual(err_num, 1)

	test_idzip_missing_target = partialmethod(on_missing_target, func=_idzip)
	test_dictzip_missing_target = partialmethod(on_missing_target, func=_dictzip)
