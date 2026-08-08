import os
import sqlite3
import sys
import unittest
import zipfile
from os.path import abspath, dirname, join

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)
sys.path.insert(0, dirname(abspath(__file__)))

from glossary_v2_test import TestGlossaryBase

from pyglossary.glossary_v2 import ConvertArgs, Glossary
from pyglossary.text_utils import escapeNTB


class TestAnkiApkg(TestGlossaryBase):
	@staticmethod
	def _make_apkg(path: str, flds: str, tags: str = "") -> None:
		import tempfile

		fd, tmp_sqlite = tempfile.mkstemp(suffix=".sqlite")
		os.close(fd)
		try:
			con = sqlite3.connect(tmp_sqlite)
			con.execute(
				"""CREATE TABLE notes (
				id integer primary key,
				guid text not null,
				mid integer not null,
				mod integer not null,
				usn integer not null,
				tags text not null,
				flds text not null,
				sfld text not null,
				csum integer not null,
				flags integer not null,
				data text not null
			);""",
			)
			first_f = flds.split("\x1f", 1)[0]
			con.execute(
				"INSERT INTO notes VALUES (1, 'g', 1, 0, 0, ?, ?, ?, 0, 0, '');",
				(tags, flds, first_f),
			)
			con.commit()
			con.close()
			with zipfile.ZipFile(path, "w") as zf:
				zf.write(tmp_sqlite, "collection.anki21")
		finally:
			os.unlink(tmp_sqlite)

	def test_convert_apkg_tabfile_basic(self) -> None:
		apkg = join(self.tempDir, "one.apkg")
		self._make_apkg(apkg, "hello\x1f<b>Back side</b>")
		out_f = join(self.tempDir, "out.txt")
		expected_f = join(self.tempDir, "expected.txt")
		with open(expected_f, "w", encoding="utf-8") as fp:
			fp.write(f"hello\t{escapeNTB('<b>Back side</b>')}\n")
		glos = self.glos = Glossary()
		glos.convert(
			ConvertArgs(
				inputFilename=apkg,
				outputFilename=out_f,
				writeOptions={"enable_info": False},
			),
		)
		self.compareTextFiles(out_f, expected_f)

	def test_convert_apkg_word_field(self) -> None:
		apkg = join(self.tempDir, "wf.apkg")
		self._make_apkg(apkg, "front\x1fmiddle\x1fback")
		out_f = join(self.tempDir, "out-wf.txt")
		expected_f = join(self.tempDir, "expected-wf.txt")
		defi_raw = "front<br>\nback"
		with open(expected_f, "w", encoding="utf-8") as fp:
			fp.write(f"middle\t{escapeNTB(defi_raw)}\n")
		glos = self.glos = Glossary()
		glos.convert(
			ConvertArgs(
				inputFilename=apkg,
				outputFilename=out_f,
				readOptions={"word_field": 1},
				writeOptions={"enable_info": False},
			),
		)
		self.compareTextFiles(out_f, expected_f)

	def test_convert_apkg_include_tags(self) -> None:
		apkg = join(self.tempDir, "tags.apkg")
		self._make_apkg(apkg, "w\x1fd", tags="t1 t2")
		out_f = join(self.tempDir, "out-tags.txt")
		expected_f = join(self.tempDir, "expected-tags.txt")
		defi_raw = '<div class="anki-tags">t1 t2</div>\nd'
		with open(expected_f, "w", encoding="utf-8") as fp:
			fp.write(f"w\t{escapeNTB(defi_raw)}\n")
		glos = self.glos = Glossary()
		glos.convert(
			ConvertArgs(
				inputFilename=apkg,
				outputFilename=out_f,
				readOptions={"include_tags": True},
				writeOptions={"enable_info": False},
			),
		)
		self.compareTextFiles(out_f, expected_f)


if __name__ == "__main__":
	unittest.main()
