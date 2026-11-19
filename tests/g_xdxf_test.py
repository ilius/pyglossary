import unittest

from glossary_v2_test import TestGlossaryBase


class TestGlossaryXDXF(TestGlossaryBase):
	def __init__(self, *args, **kwargs):
		TestGlossaryBase.__init__(self, *args, **kwargs)

		self.dataFile |= {
			"100-cyber_lexicon_en-es-v4.txt",
			"100-cyber_lexicon_en-es-v5.txt",
			"1-en-en-xdxf.xdxf",
			"4-en-en-xdxf.xdxf",
			"4-en-en-xdxf.txt",
			"4-en-en-xdxf-raw.txt",
			"2-en-en-xdxf.xdxf",
			"2-en-en-xdxf.txt",
			"2-en-en-xdxf-colors.txt",
			"2-en-en-xdxf-colors-xsl.txt",
			"2-en-en-xdxf-wordtitle.txt",
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
			readOptions={"xsl": True, "word_title": True},
		)

	def test_convert_xdxf_txt_2(self):
		self.convert_xdxf_txt(
			"100-cyber_lexicon_en-es",
			"100-cyber_lexicon_en-es-v5",
			readOptions={"xsl": False, "word_title": True},
		)

	def test_convert_xdxf_txt_3(self):
		self.convert_xdxf_txt(
			"4-en-en-xdxf",
			"4-en-en-xdxf",
			readOptions={"word_title": True},
		)

	def test_convert_xdxf_txt_4(self):
		self.convert_xdxf_txt(
			"4-en-en-xdxf",
			"4-en-en-xdxf-raw",
			readOptions={"html": False},
		)

	def test_convert_xdxf_txt(self):
		self.convert_xdxf_txt(
			"2-en-en-xdxf",
			"2-en-en-xdxf",
		)

	def test_convert_xdxf_txt_wordtitle(self):
		self.convert_xdxf_txt(
			"2-en-en-xdxf",
			"2-en-en-xdxf-wordtitle",
			readOptions={"word_title": True},
		)

	def test_convert_xdxf_txt_colors(self):
		self.convert_xdxf_txt(
			"2-en-en-xdxf",
			"2-en-en-xdxf-colors",
			readOptions={
				"pron_color": "blue",
				"gram_color": "red",
			},
		)

	def test_convert_xdxf_txt_colors_xsl(self):
		self.convert_xdxf_txt(
			"2-en-en-xdxf",
			"2-en-en-xdxf-colors-xsl",
			readOptions={
				"xsl": True,
				"pron_color": "blue",
				"gram_color": "red",
			},
		)

	def _write_xdxf(self, fname):
		from pyglossary.glossary_v2 import ConvertArgs, Glossary

		inputFilename = self.downloadFile(f"{fname}.xdxf")
		outputFilename = self.newTempFilePath(f"{fname}-tmp.xdxf")
		glos = self.glos = Glossary()
		glos.convert(
			ConvertArgs(
				inputFilename=inputFilename,
				outputFilename=outputFilename,
				readOptions={"html": False},
			),
		)
		return outputFilename

	def _assertTextFilesEqualIgnoringInputFileSize(self, fpath1, fpath2):
		def readLines(path):
			with open(path, encoding="utf-8") as file:
				return [
					line for line in file if not line.startswith("##input_file_size\t")
				]

		self.assertEqual(readLines(fpath1), readLines(fpath2))

	def _normalizedXdxfArticles(self, filename):
		from lxml import etree as ET

		parser = ET.XMLParser(remove_blank_text=True)
		tree = ET.parse(filename, parser)
		articles = []
		for article in tree.iter("ar"):
			if not any("".join(key.itertext()).strip() for key in article.findall("k")):
				continue
			articles.append(ET.tostring(article, method="c14n"))
		return articles

	def test_convert_xdxf_xdxf(self):
		for fname in ("1-en-en-xdxf", "4-en-en-xdxf"):
			with self.subTest(fname=fname):
				inputFilename = self.downloadFile(f"{fname}.xdxf")
				outputFilename = self._write_xdxf(fname)
				self.assertEqual(
					self._normalizedXdxfArticles(inputFilename),
					self._normalizedXdxfArticles(outputFilename),
				)

	def test_convert_xdxf_xdxf_txt(self):
		from pyglossary.glossary_v2 import ConvertArgs, Glossary

		outputXdxf = self._write_xdxf("4-en-en-xdxf")
		outputTxt = self.newTempFilePath("4-en-en-xdxf-tmp.txt")
		glos = self.glos = Glossary()
		glos.convert(
			ConvertArgs(
				inputFilename=outputXdxf,
				outputFilename=outputTxt,
				readOptions={"html": False},
			),
		)
		self._assertTextFilesEqualIgnoringInputFileSize(
			outputTxt,
			self.downloadFile("4-en-en-xdxf-raw.txt"),
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
