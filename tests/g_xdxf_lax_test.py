import unittest

from glossary_v2_test import TestGlossaryBase


class TestGlossaryXDXFLax(TestGlossaryBase):
	def __init__(self, *args, **kwargs):
		TestGlossaryBase.__init__(self, *args, **kwargs)

		self.dataFile |= {
			"100-cyber_lexicon_en-es-v4.txt",
			"100-cyber_lexicon_en-es-v5.txt",
			"2-en-en-xdxf.xdxf",
			"2-en-en-xdxf-lax.txt",
			"2-en-en-xdxf-lax-wordtitle.txt",
			"2-en-en-xdxf-lax-colors.txt",
			"2-en-en-xdxf-lax-colors-xsl.txt",
		}
		self.dataFileCRC32 |= {
			"100-cyber_lexicon_en-es.xdxf": "8d9ba394",
		}

	def convert_xdxf_txt(self, fname, fname2, **convertArgs):
		self.convert(
			f"{fname}.xdxf",
			f"{fname}-tmp.txt",
			compareText=f"{fname2}.txt",
			inputFormat="XdxfLax",
			**convertArgs,
		)

	def test_convert_xdxf_txt_1(self):
		self.convert_xdxf_txt(
			"100-cyber_lexicon_en-es",
			"100-cyber_lexicon_en-es-v4",
			readOptions={"xsl": True, "word_title": True},
		)

	def test_convert_xdxf_txt_2(self):
		self.convert_xdxf_txt(
			"100-cyber_lexicon_en-es",
			"100-cyber_lexicon_en-es-v5",
			readOptions={"xsl": False, "word_title": True},
		)

	def test_convert_xdxf_txt_options(self):
		self.convert_xdxf_txt(
			"2-en-en-xdxf",
			"2-en-en-xdxf-lax",
		)

	def test_convert_xdxf_txt_word_title(self):
		self.convert_xdxf_txt(
			"2-en-en-xdxf",
			"2-en-en-xdxf-lax-wordtitle",
			readOptions={"word_title": True},
		)

	def test_convert_xdxf_txt_colors(self):
		self.convert_xdxf_txt(
			"2-en-en-xdxf",
			"2-en-en-xdxf-lax-colors",
			readOptions={
				"pron_color": "blue",
				"gram_color": "red",
			},
		)

	def test_convert_xdxf_txt_colors_xsl(self):
		self.convert_xdxf_txt(
			"2-en-en-xdxf",
			"2-en-en-xdxf-lax-colors-xsl",
			readOptions={
				"xsl": True,
				"pron_color": "blue",
				"gram_color": "red",
			},
		)


if __name__ == "__main__":
	unittest.main()
