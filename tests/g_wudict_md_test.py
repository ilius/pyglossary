import gzip
import os
import tempfile
import unittest
import zipfile
from unittest import mock

from glossary_v2_test import ConvertArgs, Glossary, TestGlossaryBase

from pyglossary.plugins.wudict_md import Reader, Writer, wumd
from pyglossary.plugins.wudict_md import reader as reader_mod
from pyglossary.plugins.wudict_md import writer as writer_mod


class TestGlossaryWudictMd(TestGlossaryBase):
	def __init__(self, *args, **kwargs):
		TestGlossaryBase.__init__(self, *args, **kwargs)

		self.dataFile |= {
			"4-bar.wudict.md",
			"4-bar-clean.wudict.md",
			"5-en-en.wudict.md",
			"5-en-en.txt",
			"5-en-en-html.wudict.md",
			"13-en-en.wudict.md",
			"13-en-en.txt",
			"13-en-en-html.wudict.md",
			"13-en-en-clean.wudict.md",
			"13-en-en-repair.wudict.md",
			"13-en-en-repair.txt",
			"13-en-en-invalid.wudict.md",
			"13-en-en-invalid.txt",
			"13-en-en-truncated.wudict.md",
			"13-en-en-truncated.txt",
			"24-en-en-markdown.wudict.md",
			"24-en-en-markdown.txt",
			"92-en-en-html.txt",
			"92-en-en-html.wudict.md",
			"92-en-en-html-clean.wudict.md",
		}

	def convert_wudict_txt(self, fname, fname2, **convertArgs):
		self.convert(
			f"{fname}.wudict.md",
			f"{fname}-2.txt",
			compareText=f"{fname2}.txt",
			**convertArgs,
		)

	def convert_txt_wudict(self, fname, fname2, **convertArgs):
		self.convert(
			f"{fname}.txt",
			f"{fname}-2.wudict.md",
			compareText=f"{fname2}.wudict.md",
			**convertArgs,
		)

	def convert_txt_wudict_html_defi(self, fname, fname2, **convertArgs):
		inputFilename = self.downloadFile(f"{fname}.txt")
		outputFilename = self.newTempFilePath(f"{fname2}-2.wudict.md")
		glos = self.glos = Glossary()
		glos.setDefaultDefiFormat("h")
		glos.convert(
			ConvertArgs(
				inputFilename=inputFilename,
				outputFilename=outputFilename,
				**convertArgs,
			),
		)
		self.compareTextFiles(
			outputFilename,
			self.downloadFile(f"{fname2}.wudict.md"),
		)

	def test_convert_txt_wudict_clean(self):
		self.convert_txt_wudict(
			"004-bar",
			"4-bar-clean",
			writeOptions={"mode": "clean"},
		)

	def test_convert_txt_wudict_html(self):
		self.convert_txt_wudict(
			"004-bar",
			"4-bar",
		)

	def test_convert_txt_wudict_html_metadata(self):
		self.convert_txt_wudict(
			"5-en-en",
			"5-en-en-html",
		)

	def test_convert_wudict_txt_1(self):
		self.convert_wudict_txt("5-en-en", "5-en-en")

	def test_convert_wudict_txt_dz(self):
		with open(self.downloadFile("5-en-en.wudict.md"), "rb") as f:
			data = f.read()
		inputFilename = self.newTempFilePath("5-en-en.wudict.md.dz")
		with gzip.open(inputFilename, "wb") as f:
			f.write(data)
		outputFilename = self.newTempFilePath("5-en-en-dz.txt")
		glos = self.glos = Glossary()
		glos.convert(
			ConvertArgs(
				inputFilename=inputFilename,
				outputFilename=outputFilename,
			),
		)
		self.compareTextFiles(outputFilename, self.downloadFile("5-en-en.txt"))

	def test_convert_wudict_txt_gzip(self):
		with open(self.downloadFile("5-en-en.wudict.md"), "rb") as f:
			data = f.read()
		inputFilename = self.newTempFilePath("5-en-en.wudict.md.gz")
		with gzip.open(inputFilename, "wb") as f:
			f.write(data)
		outputFilename = self.newTempFilePath("5-en-en-gz.txt")
		glos = self.glos = Glossary()
		glos.convert(
			ConvertArgs(
				inputFilename=inputFilename,
				outputFilename=outputFilename,
			),
		)
		self.compareTextFiles(outputFilename, self.downloadFile("5-en-en.txt"))

	def test_read_resources_dir(self):
		src = self.downloadFile("5-en-en.wudict.md")
		base = self.newTempFilePath("5-en-en.wudict")
		with open(src, "rb") as f:
			data = f.read()
		with open(base + ".md", "wb") as f:
			f.write(data)
		resDir = base + ".files"
		os.makedirs(os.path.join(resDir, "images"), exist_ok=True)
		with open(os.path.join(resDir, "images", "icon.bin"), "wb") as f:
			f.write(b"PNG")
		glos = self.glos = Glossary()
		glos.directRead(base + ".md")
		dataFiles = {entry.getFileName(): entry.data for entry in glos if entry.isData()}
		self.assertEqual(dataFiles, {"images/icon.bin": b"PNG"})

	def test_convert_wudict_txt_chunked(self):
		with mock.patch.object(wumd, "CHUNK_SIZE", 1):
			self.convert_wudict_txt("13-en-en", "13-en-en")

	def test_convert_wudict_txt_invalid(self):
		self.convert_wudict_txt("13-en-en-invalid", "13-en-en-invalid")

	def test_convert_wudict_txt_repair(self):
		self.convert_wudict_txt("13-en-en-repair", "13-en-en-repair")

	def test_convert_wudict_txt_rich(self):
		self.convert_wudict_txt("13-en-en", "13-en-en")

	def test_convert_wudict_txt_truncated(self):
		self.convert_wudict_txt("13-en-en-truncated", "13-en-en-truncated")

	def test_convert_wudict_wudict_rich_clean(self):
		self.convert(
			"13-en-en.wudict.md",
			"13-en-en-2.wudict.md",
			compareText="13-en-en-clean.wudict.md",
			writeOptions={"mode": "clean"},
		)

	def test_convert_wudict_wudict_rich_html(self):
		self.convert(
			"13-en-en.wudict.md",
			"13-en-en-2.wudict.md",
			compareText="13-en-en-html.wudict.md",
		)

	def test_convert_wudict_txt_markdown_edges(self):
		self.convert_wudict_txt("24-en-en-markdown", "24-en-en-markdown")

	def test_convert_txt_wudict_clean_coverage(self):
		self.convert_txt_wudict_html_defi(
			"92-en-en-html",
			"92-en-en-html-clean",
			writeOptions={"mode": "clean"},
		)

	def test_convert_txt_wudict_html_coverage(self):
		self.convert_txt_wudict_html_defi(
			"92-en-en-html",
			"92-en-en-html",
		)


class TestWudictMdUnit(unittest.TestCase):
	def test_decode(self):
		self.assertEqual(
			wumd.decode(b"\xef\xbb\xbf# Title\r\nwudict: 1\rBody\xff"),
			"# Title\nwudict: 1\nBody\ufffd",
		)

	def test_read_text(self):
		doc = wumd.read_text(
			"# Sample\n"
			"wudict: 1\n"
			"from: en-US\n"
			"to: fa\n"
			"author: Someone\n"
			"\n"
			"A **description**.\n"
			"\n"
			"## one\n"
			"## two\n"
			"Body with *emphasis*.\n"
			"\n"
			"## alias\n"
			"see: One\n",
		)
		try:
			self.assertEqual(
				doc.meta,
				{
					"name": "Sample",
					"from": "en-US",
					"to": "fa",
					"fields": [("author", "Someone")],
					"description": "<p>A <strong>description</strong>.</p>\n",
				},
			)
			self.assertEqual(doc.warnings, [])
			self.assertEqual(len(doc), 1)
			self.assertEqual(
				list(doc),
				[
					(
						["one", "two", "alias"],
						"<p>Body with <em>emphasis</em>.</p>\n",
					),
				],
			)
		finally:
			doc.close()

	def test_read_text_redirect_missing(self):
		doc = wumd.read_text(
			"# Sample\nwudict: 1\n\n## source\nsee: missing\n",
		)
		try:
			self.assertEqual(
				list(doc),
				[
					(
						["source"],
						'<p><a href="entry://missing">missing</a></p>\n',
					),
				],
			)
		finally:
			doc.close()

	def test_read_text_warnings(self):
		doc = wumd.read_text(
			"# Sample\n"
			"wudict: 1\n"
			"not a field\n"
			"\n"
			"## html\n"
			"<div>\n"
			"## swallowed\n"
			"</div>\n"
			"\n"
			"## empty-tag\n"
			"\n",
		)
		try:
			self.assertEqual(
				doc.warnings,
				[
					(
						"W-entry: 3: header line 3 is not `key: value`;"
						" it and the rest of the header are ignored"
					),
					(
						'W-entry: 7: "## swallowed" is inside the HTML block'
						" that starts on line 6, so it is not an entry;"
						" end that block before it (a blank line, or its closing tag)"
					),
					"W-entry: 10: heading group without a body; skipped",
				],
			)
			self.assertEqual(len(doc), 1)
			self.assertEqual(
				list(doc),
				[(["html"], "<div>\n## swallowed\n</div>\n")],
			)
		finally:
			doc.close()

	def test_read_text_errors(self):
		cases = [
			("# \nwudict: 1\n", "E-format"),
			("# Title\nx: 1\n", "E-format"),
			("# Title\nwudict: 2\n", "E-version"),
			("# Title\nwudict: x\n", "E-version"),
			("# Title\nwudict: 1\n---\n\n## a\nbody\n", "E-format"),
		]
		for text, code in cases:
			with self.subTest(text=text):
				with self.assertRaises(wumd.FormatError) as ctx:
					wumd.read_text(text)
				self.assertEqual(ctx.exception.code, code)

	def test_clean_body(self):
		cases = [
			(
				(
					"<p>Hello <strong>world</strong> &amp;"
					' <a href="https://x.test/a b">link</a></p>'
				),
				"Hello **world** \\& [link](https://x.test/a%20b)",
			),
			("<ul><li>one</li><li>two</li></ul>", "- one\n- two"),
			(
				(
					"<table><tr><th>a</th><th>b</th></tr>"
					"<tr><td>1</td><td>2</td></tr></table>"
				),
				"| a | b |\n| --- | --- |\n| 1 | 2 |",
			),
			("<script>alert(1)</script><p>x</p>", "x"),
		]
		for src, expected in cases:
			with self.subTest(src=src):
				self.assertEqual(wumd.clean_body(src), expected)

	def test_clean_body_rejects_deep_nesting(self):
		with self.assertRaises(wumd.CleanError):
			wumd.clean_body("<div>" * 600 + "x" + "</div>" * 600)

	def test_html_body(self):
		self.assertEqual(wumd.html_body(""), "")
		self.assertEqual(wumd.html_body("   \n"), "")
		self.assertEqual(wumd.html_body("<div>a</div>"), "<div>a</div>")
		self.assertEqual(
			wumd.html_body("<p>a</p><p>b</p>"),
			"<div>\n<p>a</p><p>b</p>\n</div>",
		)

	def test_repair_name(self):
		self.assertEqual(wumd.repair_name("  a\tb  "), "a b")
		self.assertEqual(wumd.repair_name("x\r\ny"), "x  y")
		self.assertEqual(wumd.repair_name("a\x00b"), "ab")

	def test_field_key(self):
		cases = [
			("Foo", "foo"),
			("# a", "a"),
			("a#b", "a-b"),
			("x: y", "x-y"),
			("1a", "x-1a"),
			("Meta", "x-meta"),
			("wudict", "x-wudict"),
			("", ""),
			(" ", ""),
		]
		for name, expected in cases:
			with self.subTest(name=name):
				self.assertEqual(wumd.field_key(name), expected)

	def test_heading_esc(self):
		self.assertEqual(wumd.heading_esc("a#"), "a#")
		self.assertEqual(wumd.heading_esc("#"), "\\#")
		self.assertEqual(wumd.heading_esc("a #"), "a \\#")
		self.assertEqual(wumd.heading_esc("a \\#"), "a \\\\#")


class TestWudictPluginEdges(unittest.TestCase):
	def test_reader_not_open(self):
		r = Reader(Glossary())
		self.assertEqual(len(r), 0)
		with self.assertRaises(RuntimeError):
			next(iter(r))
		r.close()

	def test_reader_invalid_file(self):
		with tempfile.NamedTemporaryFile(suffix=".wudict.md", delete=False) as f:
			f.write(b"not a wudict dictionary\n")
			path = f.name
		try:
			r = Reader(Glossary())
			with self.assertRaises(ValueError):
				r.open(path)
			r.close()
		finally:
			os.remove(path)

	def test_reader_many_warnings(self):
		text = (
			"# T\nwudict: 1\n\n## a\nbody\n\n<div>\n"
			+ "\n".join(f"## x{i}" for i in range(101))
			+ "\n</div>\n"
		)
		with tempfile.NamedTemporaryFile(suffix=".wudict.md", delete=False) as f:
			f.write(text.encode())
			path = f.name
		try:
			r = Reader(Glossary())
			with mock.patch.object(reader_mod.log, "warning") as warning:
				r.open(path)
			self.assertEqual(warning.call_count, 101)
			r.close()
		finally:
			os.remove(path)

	def test_reader_zip_resources(self):
		with tempfile.TemporaryDirectory() as d:
			base = os.path.join(d, "foo.wudict")
			with open(base + ".md", "wb") as f:
				f.write(b"# T\nwudict: 1\n\n## a\nbody\n")
			with zipfile.ZipFile(base + ".files.zip", "w") as z:
				z.writestr("images/", b"")
				z.writestr("../escape.txt", b"a")
				z.writestr("x/y.txt", b"b")
				z.writestr("big.bin", b"x" * 20)
			r = Reader(Glossary())
			r.open(base + ".md")
			with mock.patch.object(wumd, "MAX_MARKDOWN", 10):
				entries = list(r)
			r.close()
			data = {e.getFileName(): e.data for e in entries if e.isData()}
			self.assertEqual(data, {"escape.txt": b"a", "x/y.txt": b"b"})

	def test_reader_skips_symlink_resources(self):
		with tempfile.TemporaryDirectory() as d:
			base = os.path.join(d, "foo.wudict")
			with open(base + ".md", "wb") as f:
				f.write(b"# T\nwudict: 1\n\n## a\nbody\n")
			res = base + ".files"
			os.makedirs(res)
			with open(os.path.join(res, "ok.bin"), "wb") as f:
				f.write(b"ok")
			os.symlink("/etc/hosts", os.path.join(res, "link.bin"))
			r = Reader(Glossary())
			r.open(base + ".md")
			with mock.patch.object(reader_mod.log, "warning") as warning:
				entries = list(r)
			r.close()
			data = {e.getFileName(): e.data for e in entries if e.isData()}
			self.assertEqual(data, {"ok.bin": b"ok"})
			self.assertTrue(warning.called)

	def test_writer_header_fields(self):
		with tempfile.TemporaryDirectory() as d:
			out = os.path.join(d, "out.wudict.md")
			glos = Glossary()
			for key, value in (
				("!!!", "v"),
				("a b", "v2"),
				("meta", "m"),
				("", "ignored"),
			):
				glos.setInfo(key, value)
			w = Writer(glos)
			w.open(out)
			gen = w.write()
			next(gen)
			gen.send(glos.newEntry(["x"], "<p>body</p>", defiFormat="h"))
			try:
				gen.send(None)
			except StopIteration:
				pass
			w.finish()
			with open(out, encoding="utf-8") as f:
				text = f.read()
			self.assertTrue(text.startswith("# out.wudict\nwudict: 1\n"))
			self.assertIn("meta: !!!: v\n", text)
			self.assertIn("a-b: v2\n", text)
			self.assertIn("meta: m\n", text)

	def test_writer_description_error(self):
		glos = Glossary()
		glos.setInfo("description", "<div>" * 600 + "x" + "</div>" * 600)
		w = Writer(glos)
		w._mode = "clean"
		with tempfile.TemporaryDirectory() as d, self.assertRaises(ValueError):
			w.open(os.path.join(d, "out.wudict.md"))

	def test_writer_invalid_mode(self):
		stub = mock.Mock()
		stub.getInfo.return_value = "T"
		w = Writer(stub)
		w._mode = "bad"
		with tempfile.TemporaryDirectory() as d, self.assertRaises(ValueError):
			w.open(os.path.join(d, "out.wudict.md"))

	def test_writer_empty_and_nameless(self):
		with tempfile.TemporaryDirectory() as d:
			out = os.path.join(d, "out.wudict.md")
			glos = Glossary()
			glos.setInfo("name", "T")
			dataEntry = glos.newDataEntry("a.bin", b"x")
			entries = [
				dataEntry,
				glos.newEntry([], "body", defiFormat="h"),
				glos.newEntry(["a"], "", defiFormat="h"),
				glos.newEntry(["b"], "<p>ok</p>", defiFormat="h"),
			]
			w = Writer(glos)
			w._mode = "clean"
			w.open(out)
			gen = w.write()
			next(gen)
			for entry in entries:
				gen.send(entry)
			try:
				gen.send(None)
			except StopIteration:
				pass
			resDir = out.removesuffix(".md") + ".files"
			with mock.patch.object(writer_mod.log, "info") as info:
				os.remove(os.path.join(resDir, "a.bin"))
				w.finish()
			self.assertEqual(info.call_count, 2)
			self.assertFalse(os.path.isdir(resDir))
			with open(out, encoding="utf-8") as f:
				text = f.read()
			self.assertIn("## b", text)
			self.assertNotIn("## a", text)
			self.assertFalse(os.path.exists(os.path.join(d, "out.wudict.files", "a.bin")))

	def test_writer_clean_error(self):
		with tempfile.TemporaryDirectory() as d:
			out = os.path.join(d, "out.wudict.md")
			glos = Glossary()
			glos.setInfo("name", "T")
			w = Writer(glos)
			w._mode = "clean"
			w.open(out)
			gen = w.write()
			next(gen)
			with self.assertRaises(ValueError):
				gen.send(
					glos.newEntry(
						["a"],
						"<div>" * 600 + "x" + "</div>" * 600,
						defiFormat="h",
					),
				)
			w.finish()
			self.assertFalse(os.path.exists(out))

	def test_writer_finish_twice_and_unfinished(self):
		with tempfile.TemporaryDirectory() as d:
			out = os.path.join(d, "out.wudict.md")
			glos = Glossary()
			glos.setInfo("name", "T")
			w = Writer(glos)
			w.open(out)
			w.finish()
			w.finish()
			self.assertFalse(os.path.exists(out))
			self.assertFalse(os.path.exists(out + ".tmp"))


if __name__ == "__main__":
	unittest.main()
