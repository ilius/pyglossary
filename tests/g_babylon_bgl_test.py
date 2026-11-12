import gzip
import struct
import unittest
import zlib
from os.path import isfile, join

from glossary_v2_test import TestGlossaryBase

from pyglossary.glossary_v2 import Glossary


class TestGlossaryBGL(TestGlossaryBase):
	def __init__(self, *args, **kwargs):
		TestGlossaryBase.__init__(self, *args, **kwargs)

		self.dataFile |= {
			"004-bar.txt.bgl",
			"100-en-fa.txt.bgl",
			"1-en-en-enc-lang.bgl",
			"1-en-en-enc-lang.txt",
			"1-en-en-enc-utf8.bgl",
			"1-en-en-enc-utf8.txt",
			"2-en-en-gzip-flags.bgl",
			"2-en-en-gzip-flags.txt",
			"2-en-en-gzip-large.bgl",
			"57-en-en-blocks.bgl",
			"57-en-en-blocks.txt",
			"57-en-en-blocks.txt_res/abouthtml",
			"57-en-en-blocks.txt_res/icon1.ico",
			"57-en-en-blocks.txt_res/icon2.ico",
			"57-en-en-blocks.txt_res/res.txt",
		}
		self.dataFileCRC32 |= {
			"Flavours_of_Malaysia.bgl": "46ef154b",
			"Flavours_of_Malaysia.txt_res/icon1.ico": "76a3b4c3",
			"Currency_In_Each_Country.bgl": "309f1b3f",
			"Solar_Physics_Glossary.bgl": "cc8f5ca1",
			"Farsi_Aviation_Dictionary.bgl": "efa7bee4",
		}

	def convert_bgl_txt(
		self,
		fname,
		sha1sum=None,
		md5sum=None,
		resFiles=None,
		**convertArgs,
	):
		if resFiles is None:
			resFiles = {}
		resFilesPath = {
			resName: self.newTempFilePath(join(f"{fname}-2.txt_res", resName))
			for resName in resFiles
		}

		self.convert(
			f"{fname}.bgl",
			f"{fname}-2.txt",
			sha1sum=sha1sum,
			md5sum=md5sum,
			**convertArgs,
		)

		for resName in resFiles:
			resPathActual = resFilesPath[resName]
			resPathExpected = self.downloadFile(f"{fname}.txt_res/{resName}")
			self.compareBinaryFiles(resPathActual, resPathExpected)

	def test_convert_bgl_txt_1(self):
		self.convert_bgl_txt(
			"Flavours_of_Malaysia",
			sha1sum="2b1fae135df2aaaeac23fb1dde497a4b6a22fd95",
			resFiles=["icon1.ico"],
		)

	def test_convert_bgl_txt_2(self):
		self.convert_bgl_txt(
			"Currency_In_Each_Country",
			sha1sum="731147c72092d813dfe1ab35d420477478832443",
		)

	def test_convert_bgl_txt_3(self):
		self.convert_bgl_txt(
			"Solar_Physics_Glossary",
			sha1sum="f30b392c748c4c5bfa52bf7f9945c574617ff74a",
		)

	def test_convert_bgl_txt_4(self):
		self.convert_bgl_txt(
			"Farsi_Aviation_Dictionary",
			sha1sum="34729e2542085c6026090e9e3f49d10291393113",
			readOptions={
				"process_html_in_key": True,
			},
		)

	def test_convert_bgl_txt_5(self):
		self.convert_bgl_txt(
			"004-bar.txt",
			sha1sum="40525745c2f82241e72f2f39d073078459c30eb8",
		)

	def test_convert_bgl_txt_6(self):
		self.convert_bgl_txt(
			"100-en-fa.txt",
			sha1sum="3a479a6de968e25f8ba7ee717f8cfe94fdf0e3b0",
		)

	def test_convert_bgl_txt_blocks(self):
		fname = "57-en-en-blocks"
		self.convert(
			f"{fname}.bgl",
			f"{fname}-2.txt",
			compareText=f"{fname}.txt",
		)
		for resName in ("abouthtml", "icon1.ico", "icon2.ico", "res.txt"):
			resPath = join(self.tempDir, f"{fname}-2.txt_res", resName)
			self.assertTrue(isfile(resPath), resPath)
			self.compareBinaryFiles(
				resPath,
				self.downloadFile(f"{fname}.txt_res/{resName}"),
			)

	def test_convert_bgl_txt_blocks_options(self):
		src = "57-en-en-blocks"
		optionsList = [
			{"strict_string_conversion": True},
			{"no_control_sequence_in_defi": True},
			{"key_rstrip_chars": "/"},
			{"default_encoding_overwrite": "cp1251"},
			{
				"source_encoding_overwrite": "cp1251",
				"target_encoding_overwrite": "cp1251",
			},
			{"process_html_in_key": False},
		]
		for i, readOptions in enumerate(optionsList):
			with self.subTest(readOptions=readOptions):
				self.convert(
					f"{src}.bgl",
					f"{src}-{i}.txt",
					readOptions=readOptions,
				)

	def test_convert_bgl_txt_enc_lang(self):
		self.convert(
			"1-en-en-enc-lang.bgl",
			"1-en-en-enc-lang-2.txt",
			compareText="1-en-en-enc-lang.txt",
		)

	def test_convert_bgl_txt_enc_utf8(self):
		self.convert(
			"1-en-en-enc-utf8.bgl",
			"1-en-en-enc-utf8-2.txt",
			compareText="1-en-en-enc-utf8.txt",
		)

	def test_convert_bgl_txt_gzip_flags(self):
		self.convert(
			"2-en-en-gzip-flags.bgl",
			"2-en-en-gzip-flags-2.txt",
			compareText="2-en-en-gzip-flags.txt",
		)

	def test_convert_bgl_txt_gzip_large(self):
		outputName = "2-en-en-gzip-large-2.txt"
		self.convert("2-en-en-gzip-large.bgl", outputName)
		expected = (
			"##name\t2-en-en-gzip-large.bgl\n"
			"##bgl_defaultEncoding\tcp1252\n"
			"##bgl_sourceEncoding\tcp1252\n"
			"##bgl_targetEncoding\tcp1252\n"
			"##sourceCharset\tUTF-8\n"
			"##targetCharset\tUTF-8\n"
			"##sourceLang\tEnglish\n"
			"##targetLang\tEnglish\n"
			"small\tx\n"
			"big\t" + "A" * 9000 + "\n"
		)
		with open(join(self.tempDir, outputName), encoding="utf-8") as file:
			self.assertEqual(file.read().rstrip("\n"), expected.rstrip("\n"))

	def _write_bgl_bytes(self, data: bytes) -> str:
		path = self.newTempFilePath("custom.bgl")
		with open(path, "wb") as file:
			file.write(data)
		return path

	def _wrap_gzip(self, raw: bytes) -> bytes:
		return (
			b"\x12\x34\x00\x01"
			+ (64).to_bytes(2, "big")
			+ b"\x00" * 58
			+ gzip.compress(raw, mtime=0)
		)

	def test_convert_bgl_txt_debug(self):
		from pyglossary.core import log

		prevVerbosity = log.getVerbosity()
		log.setVerbosity(4)
		try:
			self.convert(
				"57-en-en-blocks.bgl",
				"57-en-en-blocks-debug.txt",
			)
		finally:
			log.setVerbosity(prevVerbosity)

	def test_reader_public_methods(self):
		from pyglossary.plugins.babylon_bgl.reader import Reader

		glos = Glossary()
		try:
			reader = Reader(glos)
			self.assertEqual(reader.countResourceFiles(), 0)
			self.assertEqual(len(reader), 0)
			self.assertRaises(RuntimeError, list, reader)
		finally:
			glos.clear()

	def test_file_offs_seek(self):
		from pyglossary.plugins.babylon_bgl.reader_io import FileOffS

		path = self.newTempFilePath("offs.bin")
		with open(path, "wb") as file:
			file.write(b"0123456789")
		fileObj = FileOffS(path, 2)
		try:
			self.assertEqual(fileObj.tell(), 0)
			self.assertEqual(fileObj.read(2), b"23")
			self.assertEqual(fileObj.tell(), 2)
			fileObj.seek(1, 1)
			self.assertEqual(fileObj.read(1), b"3")
			fileObj.seek(-100, 1)
			self.assertEqual(fileObj.tell(), 0)
			fileObj.seek(-2, 2)
			self.assertEqual(fileObj.read(1), b"8")
			self.assertRaises(ValueError, fileObj.seek, 0, 3)
			fileObj.seek(-10)
			self.assertEqual(fileObj.tell(), 0)
			self.assertEqual(fileObj.read(1), b"2")
		finally:
			fileObj.close()

	def test_read_invalid_header(self):
		path = self._write_bgl_bytes(b"ABCD\x00@")
		glos = Glossary()
		try:
			self.assertRaises(OSError, glos.directRead, path, formatName="BabylonBgl")
		finally:
			glos.clear()

	def test_read_invalid_gzip_offset(self):
		path = self._write_bgl_bytes(b"\x12\x34\x00\x01\x00\x00")
		glos = Glossary()
		try:
			self.assertRaises(OSError, glos.directRead, path, formatName="BabylonBgl")
		finally:
			glos.clear()

	def test_read_invalid_gzip_headers(self):
		base = gzip.compress(b"\x41\x00", mtime=0)
		cases = {
			"magic": b"XX" + base[2:],
			"method": base[:2] + b"\x07" + base[3:],
		}
		for name, data in cases.items():
			with self.subTest(name=name):
				path = self._write_bgl_bytes(
					b"\x12\x34\x00\x01" + (64).to_bytes(2, "big") + b"\x00" * 58 + data,
				)
				glos = Glossary()
				try:
					self.assertRaises(
						OSError,
						glos.directRead,
						path,
						formatName="BabylonBgl",
					)
				finally:
					glos.clear()

	def test_read_truncated_gzip(self):
		data = self._wrap_gzip(b"\x41\x00")[:-4]
		path = self._write_bgl_bytes(data)
		glos = Glossary()
		try:
			self.assertRaises(
				EOFError,
				glos.directRead,
				path,
				formatName="BabylonBgl",
			)
		finally:
			glos.clear()

	def test_read_incorrect_gzip_length(self):
		raw = b"\x41\x00"
		crc = zlib.crc32(raw)
		deflated = zlib.compressobj(9, zlib.DEFLATED, -zlib.MAX_WBITS)
		body = deflated.compress(raw) + deflated.flush()
		header = b"\x1f\x8b\x08\x00" + struct.pack("<I", 0) + b"\x00\xff"
		data = header + body + struct.pack("<II", crc, 1)
		path = self._write_bgl_bytes(
			b"\x12\x34\x00\x01" + (64).to_bytes(2, "big") + b"\x00" * 58 + data,
		)
		glos = Glossary()
		try:
			self.assertRaises(
				OSError,
				glos.directRead,
				path,
				formatName="BabylonBgl",
			)
		finally:
			glos.clear()

	def test_read_truncated_block_length(self):
		for raw in (b"\x25", b"\x25\x00"):
			with self.subTest(raw=raw):
				path = self._write_bgl_bytes(self._wrap_gzip(raw))
				glos = Glossary()
				try:
					glos.directRead(path, formatName="BabylonBgl")
					self.assertEqual(list(glos), [])
				finally:
					glos.clear()


if __name__ == "__main__":
	unittest.main()
