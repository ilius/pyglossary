import unittest

from glossary_v2_test import TestGlossaryBase


class TestGlossaryStarDictTextual(TestGlossaryBase):
	def __init__(self, *args, **kwargs):
		TestGlossaryBase.__init__(self, *args, **kwargs)

		self.dataFileCRC32.update(
			{
				"100-en-fa-sdt.xml": "48cb3336",
				"100-en-fa-sdt.xml.txt": "0c9b4025",
				"stardict-xdxf-2.xml": "b3285d5c",
				"stardict-xdxf-2.xml-h.txt": "97b3a22b",
				"stardict-xdxf-2.xml-x.txt": "de63f937",
				"stardict-mixed-types-2.xml": "51d9ceb2",
				"stardict-mixed-types-2.xml.txt": "c896cf68",
			},
		)

	def convert_txt_sdxml(self, fname, fname2, **convertArgs):
		self.convert(
			f"{fname}.txt",
			f"{fname}-2.xml",
			compareText=f"{fname2}.xml",
			outputFormat="StardictTextual",
			**convertArgs,
		)

	def convert_sdxml_txt(self, fname, fname2, **convertArgs):
		self.convert(
			f"{fname}.xml",
			f"{fname}-2.txt",
			compareText=f"{fname2}.txt",
			inputFormat="StardictTextual",
			**convertArgs,
		)

	def test_convert_txt_sdxml_1(self):
		self.convert_txt_sdxml(
			"100-en-fa",
			"100-en-fa-sdt",
		)

	def test_convert_sdxml_txt_1(self):
		self.convert_sdxml_txt(
			"100-en-fa-sdt",
			"100-en-fa-sdt.xml",
		)

	def test_convert_sdxml_txt_2(self):
		self.convert_sdxml_txt(
			"stardict-mixed-types-2",
			"stardict-mixed-types-2.xml",
		)

	def test_convert_sdxml_txt_3(self):
		self.convert_sdxml_txt(
			"stardict-xdxf-2",
			"stardict-xdxf-2.xml-h",
			readOptions={"xdxf_to_html": True},
		)

	def test_convert_sdxml_txt_4(self):
		self.convert_sdxml_txt(
			"stardict-xdxf-2",
			"stardict-xdxf-2.xml-x",
			readOptions={"xdxf_to_html": False},
		)


if __name__ == "__main__":
	unittest.main()
