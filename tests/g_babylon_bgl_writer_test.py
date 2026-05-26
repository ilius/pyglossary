# -*- coding: utf-8 -*-

import gzip
import unittest
from collections import Counter
from glob import glob
from os.path import basename, join

from glossary_v2_test import TestGlossaryBase, testLocalDataDir

from pyglossary.glossary_v2 import ConvertArgs, Glossary


class TestBabylonBglWriter(TestGlossaryBase):
	def _terms_signature(self, glos: Glossary) -> Counter[tuple[str, frozenset[str]]]:
		c: Counter[tuple[str, frozenset[str]]] = Counter()
		for entry in glos:
			if entry.isData():
				continue
			terms = entry.l_term
			head = terms[0]
			alts = frozenset(terms[1:])
			c[head, alts] += 1
		return c

	def _full_rows(self, glos: Glossary) -> list[tuple[tuple[str, ...], str]]:
		rows: list[tuple[tuple[str, ...], str]] = []
		for entry in glos:
			if entry.isData():
				continue
			rows.append((tuple(entry.l_term), entry.defi))
		return sorted(rows)

	def test_tabfile_to_bgl_readable_and_terms_preserved(self):
		for txt_path in sorted(glob(join(testLocalDataDir, "*.txt"))):
			with self.subTest(file=basename(txt_path)):
				gl0 = Glossary()
				gl0.directRead(txt_path, formatName="Tabfile")
				n0 = sum(1 for e in gl0 if not e.isData())
				sig0 = self._terms_signature(gl0)

				out_bgl = self.newTempFilePath(f"{basename(txt_path)}-out.bgl")
				gl1 = Glossary()
				gl1.convert(
					ConvertArgs(
						inputFilename=txt_path,
						outputFilename=out_bgl,
						inputFormat="Tabfile",
						outputFormat="BabylonBgl",
					),
				)

				gl2 = Glossary()
				gl2.directRead(out_bgl, formatName="BabylonBgl")
				n2 = sum(1 for e in gl2 if not e.isData())
				sig2 = self._terms_signature(gl2)

				self.assertEqual(n0, n2, msg=f"entry count mismatch for {txt_path!r}")
				self.assertEqual(
					sig0,
					sig2,
					msg=f"headword / alternate multiset mismatch for {txt_path!r}",
				)

				if basename(txt_path) != "100-ja-en.txt":
					self.assertEqual(
						self._full_rows(gl0),
						self._full_rows(gl2),
						msg=f"full entry mismatch for {txt_path!r}",
					)

	def test_bgl_writer_wraps_resource_links(self):
		import os
		import tempfile

		tmpdir = tempfile.mkdtemp()
		txt_path = join(tmpdir, "media.txt")
		res_dir = txt_path + "_res"
		os.makedirs(res_dir)
		png = (
			b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
			b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0c"
			b"IDAT\x08\x99\x01\x01\x00\x00\xff\xff\x00\x00\x00\x02\x00\x01"
			b"\x00\x00\x00\x00IEND\xaeB`\x82"
		)
		with open(join(res_dir, "test.png"), "wb") as png_file:
			png_file.write(png)
		with open(txt_path, "w", encoding="utf-8") as txt_file:
			txt_file.write("hello\t<img src='test.png'>\n")

		out_bgl = self.newTempFilePath("media-out.bgl")
		gl = Glossary()
		gl.convert(
			ConvertArgs(
				inputFilename=txt_path,
				outputFilename=out_bgl,
				inputFormat="Tabfile",
				outputFormat="BabylonBgl",
			),
		)

		with open(out_bgl, "rb") as bgl_file:
			bgl_file.seek(64)
			payload = gzip.GzipFile(fileobj=bgl_file).read()
		self.assertIn(b"\x1etest.png\x1f", payload)


if __name__ == "__main__":
	unittest.main()
