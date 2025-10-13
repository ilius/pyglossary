from __future__ import annotations

import sys
from os.path import abspath, dirname
from typing import TYPE_CHECKING

from glossary_v2_test import TestGlossaryBase

if TYPE_CHECKING:
	pass

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)


class TestGlossaryDictfile(TestGlossaryBase):
	def __init__(self, *args, **kwargs):
		TestGlossaryBase.__init__(self, *args, **kwargs)

		self.dataFileCRC32.update(
			{
				"edict2/024-cedict.u8": "de30cdd3",
				"edict2/024-cedict.txt": "34e2dc56",
			},
		)

	def convert_edict_txt(self, fname, fname2):
		self.convert(
			f"edict2/{fname}.u8",
			f"{fname}-2.txt",
			compareText=f"edict2/{fname2}.txt",
			name=f"{fname}.u8",
		)

	def test_convert_edict_txt_1(self):
		self.convert_edict_txt(
			"024-cedict",
			"024-cedict",
		)
