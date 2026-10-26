import datetime
import hashlib
import os
import re
import sys
import unittest
import zipfile
from os.path import abspath, dirname
from xml.etree import ElementTree

from freezegun import freeze_time

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from glossary_v2_test import TestGlossaryBase

from pyglossary.glossary_v2 import ConvertArgs, Glossary

testTimeEpoch = 1730579400
testTime = datetime.datetime.fromtimestamp(testTimeEpoch, tz=datetime.UTC)


class TestGlossaryEPUB2(TestGlossaryBase):
	def __init__(self, *args, **kwargs):
		TestGlossaryBase.__init__(self, *args, **kwargs)

		self.dataFileCRC32 |= {
			"100-en-fa-res.slob": "0216d006",
			"100-en-fa-res-slob-v2.epub": "304d174d",
			"100-en-fa-prefix3-v2.epub": "1b7244ca",
			"300-rand-en-fa-prefix3-v2.epub": "b5dd9ec6",
		}

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
			os.environ["EPUB_UUID"] = hashlib.sha1(inputFname.encode("ascii")).hexdigest()
			os.environ["EBOOK_CREATION_TIME"] = str(testTimeEpoch)
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
			with open(outputFilename, mode="rb") as file:
				actualSha1 = hashlib.sha1(file.read()).hexdigest()
			self.assertEqual(sha1sum, actualSha1, f"{outputFilename=}")

	# sha1sum still depends on current date (but not time)
	# despite using ReproducibleZipFile and EBOOK_CREATION_TIME env var. not sure why.
	@freeze_time(testTime)
	def test_convert_txt_epub_1(self):
		self.convert_to_epub(
			"100-en-fa.txt",
			"100-en-fa",
			testId="a1",
			checkZipContents=False,
			sha1sum="f52af4681a38df88c2e2916938735499cd700521",
		)

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

	def test_write_epub_ncx_links(self):
		glos = self.glos = Glossary()
		for term in ("apple", "banana", "cherry"):
			glos.addEntry(glos.newEntry([term], f"{term} definition"))
		outputFilename = self.newTempFilePath("ncx-links.epub")
		glos.write(outputFilename, formatName="Epub2")

		ns = {
			"ncx": "http://www.daisy.org/z3986/2005/ncx/",
			"x": "http://www.w3.org/1999/xhtml",
		}
		with zipfile.ZipFile(outputFilename) as zf:
			ncx = ElementTree.fromstring(zf.read("OEBPS/toc.ncx"))
			links = [
				(
					point.find("ncx:navLabel/ncx:text", ns).text,
					point.find("ncx:content", ns).get("src"),
				)
				for point in ncx.iterfind("ncx:navMap/ncx:navPoint", ns)
			]
			self.assertEqual(
				links,
				[
					("apple\u2013apple", "g000002.xhtml"),
					("banana\u2013banana", "g000003.xhtml"),
					("cherry\u2013cherry", "g000004.xhtml"),
				],
			)
			for label, src in links:
				page = ElementTree.fromstring(zf.read(f"OEBPS/{src}"))
				self.assertEqual(page.find(".//x:h1", ns).text, label)

	def test_write_epub_escape(self):
		glos = self.glos = Glossary()
		glos.addEntry(glos.newEntry(["AT&T"], "a company & a <brand>", defiFormat="m"))
		glos.addEntry(glos.newEntry(["a<b"], "<b>bold</b>", defiFormat="h"))
		outputFilename = self.newTempFilePath("escape.epub")
		glos.write(outputFilename, formatName="Epub2")

		with zipfile.ZipFile(outputFilename) as zf:
			ncx = ElementTree.fromstring(zf.read("OEBPS/toc.ncx"))
			pages = [
				ElementTree.fromstring(zf.read(name))
				for name in zf.namelist()
				if name.endswith(".xhtml")
			]

		ns = {
			"ncx": "http://www.daisy.org/z3986/2005/ncx/",
			"x": "http://www.w3.org/1999/xhtml",
		}
		labels = [
			text.text
			for text in ncx.iterfind("ncx:navMap/ncx:navPoint/ncx:navLabel/ncx:text", ns)
		]
		self.assertEqual(sorted(labels), ["AT&T\u2013AT&T", "a<b\u2013a<b"])
		entries = {
			"".join(entry.find("x:h2", ns).itertext()): "".join(
				entry.find("x:p", ns).itertext(),
			)
			for page in pages
			for entry in page.iterfind(".//x:div[@class='groupEntry']", ns)
		}
		self.assertEqual(entries, {"AT&T": "a company & a <brand>", "a<b": "bold"})


if __name__ == "__main__":
	unittest.main()
