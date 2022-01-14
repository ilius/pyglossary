import sys
from os.path import dirname, abspath
import unittest

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from pyglossary.glossary_test import TestGlossaryBase
from pyglossary.glossary import Glossary


class TestGlossaryStarDict(TestGlossaryBase):
	def __init__(self, *args, **kwargs):
		TestGlossaryBase.__init__(self, *args, **kwargs)

		self.dataFileCRC32.update({
			"100-en-fa-res.slob": "0216d006",
			"100-en-fa-res-slob.epub": "30506767",
		})

	def convert_slob_epub(self, fname, fname2, **convertArgs):
		import re

		inputFilename = self.downloadFile(f"{fname}.slob")
		outputFilename = self.newTempFilePath(f"{fname}-2.epub")

		expectedFilename = self.downloadFile(f"{fname2}.epub")
		glos = Glossary()
		res = glos.convert(
			inputFilename=inputFilename,
			outputFilename=outputFilename,
			**convertArgs
		)
		self.assertEqual(outputFilename, res)

		def remove_toc_uid(data):
			return re.sub(
				b'<meta name="dtb:uid" content="[0-9a-f]{32}" />',
				b'<meta name="dtb:uid" content="" />',
				data,
			)

		def remove_content_extra(data):
			data = re.sub(
				b'<dc:identifier id="uid" opf:scheme="uuid">[0-9a-f]{32}</dc:identifier>',
				b'<dc:identifier id="uid" opf:scheme="uuid"></dc:identifier>',
				data,
			)
			data = re.sub(
				b'<dc:date opf:event="creation">[0-9-]{10}</dc:date>',
				b'<dc:date opf:event="creation"></dc:date>',
				data,
			)
			return data

		self.compareZipFiles(
			outputFilename,
			expectedFilename,
			{
				"OEBPS/toc.ncx": remove_toc_uid,
				"OEBPS/content.opf": remove_content_extra,
			},
		)

	def test_convert_slob_epub_1(self):
		self.convert_slob_epub(
			"100-en-fa-res",
			"100-en-fa-res-slob",
		)

	def test_convert_slob_epub_2(self):
		for sort in (True, False):
			self.convert_slob_epub(
				"100-en-fa-res",
				"100-en-fa-res-slob",
				sort=sort,
			)

	def test_convert_slob_epub_3(self):
		for sqlite in (True, False):
			self.convert_slob_epub(
				"100-en-fa-res",
				"100-en-fa-res-slob",
				sqlite=sqlite,
			)

	def test_convert_slob_epub_4(self):
		for direct in (True, False):
			self.convert_slob_epub(
				"100-en-fa-res",
				"100-en-fa-res-slob",
				direct=direct,
			)


if __name__ == "__main__":
	unittest.main()
