import unittest

from glossary_v2_test import TestGlossaryBase


class TestGlossaryDictOrg(TestGlossaryBase):
	def __init__(self, *args, **kwargs):
		TestGlossaryBase.__init__(self, *args, **kwargs)

		self.dataFileCRC32.update(
			{
				"100-en-fa.txt.dict": "02abe5dc",
				"100-en-fa.txt.index": "b10efcb4",
				"100-en-fa.txt.index.txt": "6c9d527c",
			},
		)

	def convert_txt_dict_org(self, fname, fname2, **convertArgs):
		self.convert(
			f"{fname}.txt",
			f"{fname}-2.index",
			compareText=f"{fname2}.index",
			**convertArgs,
		)

	def convert_dict_org_txt(self, fname, fname2, **convertArgs):
		self.downloadFile(f"{fname}.dict")
		self.convert(
			f"{fname}.index",
			f"{fname}-2.txt",
			compareText=f"{fname2}.txt",
			**convertArgs,
		)

	def test_convert_txt_dict_org_1(self):
		self.convert_txt_dict_org(
			"100-en-fa",
			"100-en-fa.txt",
			writeOptions={"install": False},
		)

	def test_convert_dict_org_txt_1(self):
		self.convert_dict_org_txt(
			"100-en-fa.txt",
			"100-en-fa.txt.index",
			infoOverride={"input_file_size": None},
		)


if __name__ == "__main__":
	unittest.main()
