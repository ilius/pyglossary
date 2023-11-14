import gzip
from functools import partial
from pathlib import Path
from typing import Callable

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


class TestDictzipBase(TestGlossaryErrorsBase):
	# FIXME Check warning
	def _run(self, func: partial, filename: str | Path) -> None:
		done = func(str(filename))
		if not done:
			func_name = func.func.__name__
			self.skipTest(f'Missing dependency for {func_name}')


class TestDictzip(TestDictzipBase):
	def make_dz(self, func: partial, path: str | Path) -> Path:
		"""Get path of dzipped file contains TEXT."""
		test_file_path = Path(path)/"test_file.txt"
		result_file_path = test_file_path.parent/(test_file_path.name + ".dz")
		with open(test_file_path, "a") as tmp_file:
			tmp_file.write(TEXT)
		self._run(func, test_file_path)
		return result_file_path

	def test_idzip_compressed_exists(self) -> None:
		result_file_path = self.make_dz(
			partial(runDictzip, method='idzip'), self.tempDir)
		self.assertTrue(result_file_path.exists())
		self.assertTrue(result_file_path.is_file())

	def test_idzip_compressed_matches(self) -> None:
		result_file_path = self.make_dz(
			partial(runDictzip, method='idzip'), self.tempDir)
		with gzip.open(result_file_path, 'r') as file:
			result = file.read().decode()
		self.assertEqual(result, TEXT)

	def test_dictzip_compressed_exists(self) -> None:
		result_file_path = self.make_dz(
			partial(runDictzip, method='dictzip'), self.tempDir)
		self.assertTrue(result_file_path.exists())
		self.assertTrue(result_file_path.is_file())

	def test_dictzip_compressed_matches(self) -> None:
		result_file_path = self.make_dz(
			partial(runDictzip, method='dictzip'), self.tempDir)
		with gzip.open(result_file_path, 'r') as file:
			result = file.read().decode()
		self.assertEqual(result, TEXT)


class TestDictzipErrors(TestDictzipBase):
	def tearDown(self):
		self.mockLog.clear()
		super().tearDown()

	def on_missing_target(self, func: Callable[[str], bool]) -> None:
		filename = '/NOT_EXISTED_PATH/file.txt'
		self._run(func, filename)
		err_num = self.mockLog.printRemainingErrors()
		self.assertEqual(err_num, 1)

	# FIXME
	#test_idzip_missing_target = partialmethod(on_missing_target, func=_idzip)
	#test_dictzip_missing_target = partialmethod(on_missing_target, func=_dictzip)
