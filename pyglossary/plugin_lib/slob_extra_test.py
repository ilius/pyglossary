#!/usr/bin/env python3
import sys
import os
from os.path import dirname, abspath
import unittest
import logging
import tempfile

rootDir = dirname(dirname(dirname(abspath(__file__))))
sys.path.insert(0, rootDir)

from pyglossary.plugin_lib.slob_extra import *
from pyglossary.plugin_lib.slob_test import BaseTest


class TestBestMatch(BaseTest):

	def setUp(self):
		self.tmpdir = tempfile.TemporaryDirectory(prefix='test')
		self.path1 = os.path.join(self.tmpdir.name, 'test1.slob')
		self.path2 = os.path.join(self.tmpdir.name, 'test2.slob')

		data1 = ['aa', 'Aa', 'a-a', 'aabc', 'Äā', 'bb', 'aa']
		data2 = ['aa', 'aA', 'āā', 'a,a', 'a-a', 'aade', 'Äā', 'cc']

		with self.create(self.path1) as w:
			for key in data1:
				w.add(b'', key)

		with self.create(self.path2) as w:
			for key in data2:
				w.add(b'', key)

	def test_best_match(self):
		self.maxDiff = None
		with open(self.path1) as s1, open(self.path2) as s2:
			result = find('aa', [s1, s2], match_prefix=True)
			actual = list((s.id, item.key) for s, item in result)
			expected = [
				(s1.id, 'aa'),
				(s1.id, 'aa'),
				(s2.id, 'aa'),
				(s1.id, 'a-a'),
				(s2.id, 'a-a'),
				(s2.id, 'a,a'),
				(s1.id, 'Aa'),
				(s2.id, 'aA'),
				(s1.id, 'Äā'),
				(s2.id, 'Äā'),
				(s2.id, 'āā'),
				(s1.id, 'aabc'),
				(s2.id, 'aade'),
			]
			self.assertEqual(expected, actual)

	def tearDown(self):
		self.tmpdir.cleanup()


if __name__ == '__main__':
	unittest.main()
