import unittest

from glossary_v2_test import TestGlossaryBase


class TestGlossaryXDXF(TestGlossaryBase):
	def __init__(self, *args, **kwargs):
		TestGlossaryBase.__init__(self, *args, **kwargs)

		self.dataFile |= {
			"100-cyber_lexicon_en-es-v4.txt",
			"100-cyber_lexicon_en-es-v5.txt",
			"4-en-en-xdxf.xdxf",
			"4-en-en-xdxf.txt",
			"4-en-en-xdxf-raw.txt",
		}
		self.dataFileCRC32 |= {
			"100-cyber_lexicon_en-es.xdxf": "8d9ba394",
		}

	def convert_xdxf_txt(self, fname, fname2, **convertArgs):
		self.convert(
			f"{fname}.xdxf",
			f"{fname}-tmp.txt",
			compareText=f"{fname2}.txt",
			**convertArgs,
		)

	# def test_convert_xdxf_txt_1(self):
	# 	self.convert_xdxf_txt(
	# 		"100-cyber_lexicon_en-es",
	# 		"100-cyber_lexicon_en-es-v4",
	# 		readOptions={"xsl": False}
	# 	)

	def test_convert_xdxf_txt_1(self):
		self.convert_xdxf_txt(
			"100-cyber_lexicon_en-es",
			"100-cyber_lexicon_en-es-v4",
			readOptions={"xsl": True},
		)

	def test_convert_xdxf_txt_2(self):
		self.convert_xdxf_txt(
			"100-cyber_lexicon_en-es",
			"100-cyber_lexicon_en-es-v5",
			readOptions={"xsl": False},
		)

	def test_convert_xdxf_txt_3(self):
		self.convert_xdxf_txt(
			"4-en-en-xdxf",
			"4-en-en-xdxf",
		)

	def test_convert_xdxf_txt_4(self):
		self.convert_xdxf_txt(
			"4-en-en-xdxf",
			"4-en-en-xdxf-raw",
			readOptions={"html": False},
		)

	def test_reader_api(self):
		from pyglossary.glossary_v2 import Glossary
		from pyglossary.plugins.xdxf.reader import Reader

		glos = self.glos = Glossary()
		reader = Reader(glos)
		self.assertEqual(len(reader), 0)
		self.assertEqual(reader.countResourceFiles(), 0)

	def test_open_non_seekable(self):
		import io
		from unittest import mock

		from pyglossary.glossary_v2 import Glossary
		from pyglossary.plugins.xdxf import reader as xdxfReader

		with open(self.downloadFile("4-en-en-xdxf.xdxf"), "rb") as file:
			data = file.read()

		class NonSeekableFile(io.BytesIO):
			def seekable(self):
				return False

		glos = self.glos = Glossary()
		reader = xdxfReader.Reader(glos)
		with mock.patch.object(
			xdxfReader,
			"compressionOpen",
			side_effect=lambda *_args, **_kwargs: NonSeekableFile(data),
		):
			reader.open("4-en-en-xdxf.xdxf")
		reader.close()


if __name__ == "__main__":
	unittest.main()
