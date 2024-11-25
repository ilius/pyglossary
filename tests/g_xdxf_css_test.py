import unittest

from glossary_v2_test import TestGlossaryBase


class TestGlossaryXDXF(TestGlossaryBase):
	def __init__(self, *args, **kwargs):
		TestGlossaryBase.__init__(self, *args, **kwargs)

		self.dataFileCRC32.update(
			{
				"100-cyber_lexicon_en-es.xdxf": "8d9ba394",
				"100-cyber_lexicon_en-es-css.txt": "be892c84",
				# "100-cyber_lexicon_en-es-css.txt_res/css/xdxf.css": "206ae89d",
				# "100-cyber_lexicon_en-es-css.txt_res/js/xdxf.js": "938842f0",
			},
		)

	def convert_xdxf_txt(self, fname, fname2, **convertArgs):
		self.convert(
			f"{fname}.xdxf",
			f"{fname}-tmp.txt",
			compareText=f"{fname2}.txt",
			inputFormat="XdxfCss",
			**convertArgs,
		)

	def test_convert_xdxf_txt_1(self):
		self.convert_xdxf_txt(
			"100-cyber_lexicon_en-es",
			"100-cyber_lexicon_en-es-css",
		)


if __name__ == "__main__":
	unittest.main()
