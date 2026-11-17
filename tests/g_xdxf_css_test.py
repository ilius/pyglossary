import unittest

from glossary_v2_test import TestGlossaryBase


class TestGlossaryXDXF(TestGlossaryBase):
	def __init__(self, *args, **kwargs):
		TestGlossaryBase.__init__(self, *args, **kwargs)

		self.dataFile |= {
			"4-en-en-xdxf-css.xdxf",
			"4-en-en-xdxf-css.txt",
		}
		self.dataFileCRC32 |= {
			"100-cyber_lexicon_en-es.xdxf": "8d9ba394",
			"100-cyber_lexicon_en-es-css.txt": "be892c84",
			# "100-cyber_lexicon_en-es-css.txt_res/css/xdxf.css": "206ae89d",
			# "100-cyber_lexicon_en-es-css.txt_res/js/xdxf.js": "938842f0",
		}

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

	def test_convert_xdxf_txt_2(self):
		self.convert_xdxf_txt(
			"4-en-en-xdxf-css",
			"4-en-en-xdxf-css",
		)

	def test_open_non_seekable(self):
		import io
		from unittest import mock

		from pyglossary.glossary_v2 import Glossary
		from pyglossary.plugins.xdxf_css import reader as xdxfCssReader

		with open(self.downloadFile("4-en-en-xdxf-css.xdxf"), "rb") as file:
			data = file.read()

		class NonSeekableFile(io.BytesIO):
			def seekable(self):
				return False

		glos = self.glos = Glossary()
		reader = xdxfCssReader.Reader(glos)
		with mock.patch.object(
			xdxfCssReader,
			"compressionOpen",
			side_effect=lambda *_args, **_kwargs: NonSeekableFile(data),
		):
			reader.open("4-en-en-xdxf-css.xdxf")
		reader.close()


if __name__ == "__main__":
	unittest.main()
