import os
import sys
import tempfile
import unittest
from os.path import abspath, dirname, join

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from pyglossary.utils.os_utils import (
	countFilesRecursive,
	listFilesRecursiveRelPath,
	rmtree,
)


class TestOsUtils(unittest.TestCase):
	def setUp(self):
		self.tempDir = tempfile.mkdtemp()

	def tearDown(self):
		rmtree(self.tempDir)

	def makeResFiles(self, direc):
		os.makedirs(join(direc, "img"))
		os.makedirs(join(direc, "audio", "en"))
		open(join(direc, "icon.png"), "wb").close()
		open(join(direc, "img", "pic.png"), "wb").close()
		open(join(direc, "audio", "en", "hello.mp3"), "wb").close()

	def test_listFilesRecursiveRelPath(self):
		direc = join(self.tempDir, "res")
		self.makeResFiles(direc)
		self.assertEqual(
			sorted(listFilesRecursiveRelPath(direc)),
			sorted(
				[
					"icon.png",
					join("img", "pic.png"),
					join("audio", "en", "hello.mp3"),
				]
			),
		)

	def test_listFilesRecursiveRelPath_trailing_slash(self):
		direc = join(self.tempDir, "res")
		self.makeResFiles(direc)
		self.assertEqual(
			sorted(listFilesRecursiveRelPath(direc + os.sep)),
			sorted(listFilesRecursiveRelPath(direc)),
		)

	def test_listFilesRecursiveRelPath_empty(self):
		self.assertEqual(list(listFilesRecursiveRelPath("")), [])

	def test_listFilesRecursiveRelPath_no_files(self):
		direc = join(self.tempDir, "empty")
		os.makedirs(join(direc, "sub"))
		self.assertEqual(list(listFilesRecursiveRelPath(direc)), [])

	def test_countFilesRecursive(self):
		direc = join(self.tempDir, "res")
		self.makeResFiles(direc)
		self.assertEqual(countFilesRecursive(direc), 3)
		self.assertEqual(countFilesRecursive(""), 0)


if __name__ == "__main__":
	unittest.main()
