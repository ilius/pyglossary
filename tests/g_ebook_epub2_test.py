import hashlib
import os
import re
import sys
import unittest
from os.path import abspath, dirname

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from glossary_v2_test import TestGlossaryBase

from pyglossary.glossary_v2 import ConvertArgs, Glossary


class TestGlossaryEPUB2(TestGlossaryBase):
	def __init__(self, *args, **kwargs):
		TestGlossaryBase.__init__(self, *args, **kwargs)

		self.dataFileCRC32.update(
			{
				"100-en-fa-res.slob": "0216d006",
				"100-en-fa-res-slob-v2.epub": "304d174d",
				"100-en-fa-prefix3-v2.epub": "1b7244ca",
				"300-rand-en-fa-prefix3-v2.epub": "b5dd9ec6",
			},
		)

	def setUp(self):
		TestGlossaryBase.setUp(self)

	def remove_toc_uid(self, data):
		return re.sub(
			b'<meta name="dtb:uid" content="[0-9a-f]{32}" />',
			b'<meta name="dtb:uid" content="" />',
			data,
		)

	def remove_content_extra(self, data):
		data = re.sub(
			b'<dc:identifier id="uid" opf:scheme="uuid">[0-9a-f]{32}</dc:identifier>',
			b'<dc:identifier id="uid" opf:scheme="uuid"></dc:identifier>',
			data,
		)
		return re.sub(
			b'<dc:date opf:event="creation">[0-9-]{10}</dc:date>',
			b'<dc:date opf:event="creation"></dc:date>',
			data,
		)

	def convert_to_epub(
		self,
		inputFname,
		outputFname,
		testId,
		checkZipContents=True,
		sha1sum="",
		**convertArgs,
	):
		inputFilename = self.downloadFile(f"{inputFname}")
		outputFilename = self.newTempFilePath(
			f"{inputFname.replace('.', '_')}-{testId}.epub",
		)

		if sha1sum:
			os.environ["EPUB_UUID"] = hashlib.sha1(
				inputFname.encode("ascii")
			).hexdigest()
			os.environ["EBOOK_CREATION_TIME"] = "1730579400"
			# print(f'{os.environ["EPUB_UUID"]=}')

		glos = self.glos = Glossary()
		res = glos.convert(
			ConvertArgs(
				inputFilename=inputFilename,
				outputFilename=outputFilename,
				**convertArgs,
			)
		)
		self.assertEqual(outputFilename, res)

		if checkZipContents:
			self.compareZipFiles(
				outputFilename,
				self.downloadFile(f"{outputFname}.epub"),
				{
					"OEBPS/toc.ncx": self.remove_toc_uid,
					"OEBPS/content.opf": self.remove_content_extra,
				},
			)
		if sha1sum:
			with open(outputFilename, mode="rb") as _file:
				actualSha1 = hashlib.sha1(_file.read()).hexdigest()
			self.assertEqual(sha1sum, actualSha1, f"{outputFilename=}")

	# def test_convert_txt_epub_1(self):
	# 	self.convert_to_epub(
	# 		"100-en-fa.txt",
	# 		"100-en-fa",
	# 		testId="a1",
	# 		checkZipContents=False,
	# 		sha1sum="86aaea126cc4c2a471c7b60ea35a32841bf4d4b7",
	# 	)

	def test_convert_to_epub_1(self):
		self.convert_to_epub(
			"100-en-fa-res.slob",
			"100-en-fa-res-slob-v2",
			testId="1",
		)

	def test_convert_to_epub_2(self):
		for sort in (True, False):
			self.convert_to_epub(
				"100-en-fa-res.slob",
				"100-en-fa-res-slob-v2",
				testId="2",
				sort=sort,
			)

	def test_convert_to_epub_3(self):
		for sqlite in (True, False):
			self.convert_to_epub(
				"100-en-fa-res.slob",
				"100-en-fa-res-slob-v2",
				testId="3",
				sqlite=sqlite,
			)

	def test_convert_to_epub_4(self):
		for direct in (True, False):
			self.convert_to_epub(
				"100-en-fa-res.slob",
				"100-en-fa-res-slob-v2",
				testId="4",
				direct=direct,
			)

	def test_convert_to_epub_5(self):
		for sqlite in (True, False):
			self.convert_to_epub(
				"100-en-fa.txt",
				"100-en-fa-prefix3-v2",
				testId="5",
				sqlite=sqlite,
				writeOptions={"group_by_prefix_length": 3},
			)

	def test_convert_to_epub_6(self):
		self.convert_to_epub(
			"300-rand-en-fa.txt",
			"300-rand-en-fa-prefix3-v2",
			testId="6",
			sqlite=True,
			writeOptions={"group_by_prefix_length": 3},
		)

	def test_convert_to_epub_7(self):
		self.convert_to_epub(
			"300-rand-en-fa.txt",
			"300-rand-en-fa-prefix3-v2",
			testId="7",
			sqlite=False,
			writeOptions={"group_by_prefix_length": 3},
		)


if __name__ == "__main__":
	unittest.main()
