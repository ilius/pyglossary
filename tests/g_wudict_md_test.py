import gzip
import os
import unittest

from glossary_v2_test import ConvertArgs, Glossary, TestGlossaryBase

from pyglossary.plugins.wudict_md import wumd


class TestGlossaryWudictMd(TestGlossaryBase):
	def __init__(self, *args, **kwargs):
		TestGlossaryBase.__init__(self, *args, **kwargs)

		self.dataFile |= {
			"4-bar.wudict.md",
			"4-bar-clean.wudict.md",
			"5-en-en.wudict.md",
			"5-en-en.txt",
			"5-en-en-html.wudict.md",
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

	def test_convert_wudict_txt_1(self):
		self.convert_wudict_txt("5-en-en", "5-en-en")

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

	def test_convert_txt_wudict_html(self):
		self.convert_txt_wudict(
			"004-bar",
			"4-bar",
		)

	def test_convert_txt_wudict_clean(self):
		self.convert_txt_wudict(
			"004-bar",
			"4-bar-clean",
			writeOptions={"mode": "clean"},
		)

	def test_convert_txt_wudict_html_metadata(self):
		self.convert_txt_wudict(
			"5-en-en",
			"5-en-en-html",
		)

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


if __name__ == "__main__":
	unittest.main()
