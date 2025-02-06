import os
import unittest

from glossary_v2_test import TestGlossaryBase


class TestGlossaryDictOrg(TestGlossaryBase):
	def __init__(self, *args, **kwargs):
		TestGlossaryBase.__init__(self, *args, **kwargs)

		self.dataFileCRC32.update(
			{
				"100-en-fa.dtxt": "05d6e939",
			},
		)
		os.environ["CALC_FILE_SIZE"] = "1"

	def convert_txt_dict_org_source(self, fname, fname2, **convertArgs):
		self.convert(
			f"{fname}.txt",
			f"{fname}-2.dtxt",
			compareText=f"{fname2}.dtxt",
			**convertArgs,
		)

	def test_convert_txt_dict_org_source_1(self):
		self.convert_txt_dict_org_source(
			"100-en-fa",
			"100-en-fa",
		)


if __name__ == "__main__":
	unittest.main()
