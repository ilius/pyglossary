import os
import plistlib
import runpy
import shutil
import sys
import unittest
from os.path import abspath, basename, dirname, isdir, isfile, join
from unittest import mock

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from glossary_v2_test import TestGlossaryBase, testLocalDataDir

from pyglossary.glossary_v2 import ConvertArgs, Glossary


class TestGlossaryAppleDict(TestGlossaryBase):
	def __init__(self, *args, **kwargs):
		"""Register remote fixture checksums so reader/writer tests can validate downloaded files."""
		TestGlossaryBase.__init__(self, *args, **kwargs)

		hashDict = {
			"appledict-src/002-no-morphology-v3.txt": "d8086fe8",
			"appledict-src/002-no-morphology-v3a/002-no-morphology-v3a.css": "6818c1e5",
			"appledict-src/002-no-morphology-v3a/002-no-morphology-v3a.plist": "706d1d9c",
			"appledict-src/002-no-morphology-v3a/002-no-morphology-v3a.xml": "707994d6",
			"appledict-src/002-no-morphology-v3a/Makefile": "ecd42350",
		}
		self.dataFileCRC32 |= hashDict

	def test_convert_appledict_txt(self):
		"""Test that reading an AppleDict bundle yields the expected Tabfile output."""
		inputDirPath = join(testLocalDataDir, "6-en-en-appledict")
		outputFilePath = self.newTempFilePath("6-en-en-appledict-tmp.txt")
		self.glos = Glossary()

		result = self.glos.convert(
			ConvertArgs(
				inputFilename=inputDirPath,
				outputFilename=outputFilePath,
				inputFormat="AppleDict",
				outputFormat="Tabfile",
			)
		)
		self.assertEqual(result, outputFilePath)

		self.compareTextFiles(
			outputFilePath,
			join(testLocalDataDir, "6-en-en-appledict.txt"),
		)
		for relPath in ("note.txt", join("audio", "beep.mp3")):
			self.compareBinaryFiles(
				join(outputFilePath + "_res", relPath),
				join(inputDirPath, "OtherResources", relPath),
			)

	def _copyAppledictFixture(self, name):
		"""Copy the fixture into the temp directory so mutating tests cannot alter checked-in files."""
		return shutil.copytree(
			join(testLocalDataDir, "6-en-en-appledict"),
			join(self.tempDir, name),
		)

	def _readAppledictOutput(self, outputDirPath):
		"""Read generated XML and plist files to simplify writer-output assertions."""
		baseName = basename(outputDirPath).replace(".", "_")
		with open(join(outputDirPath, f"{baseName}.xml"), encoding="utf-8") as file:
			xml = file.read()
		with open(join(outputDirPath, f"{baseName}.plist"), encoding="utf-8") as file:
			plist = file.read()
		return baseName, xml, plist

	def test_reader_api(self):
		"""Test the reader's public length, resource-count, open, and close API."""
		from pyglossary.plugins.appledict.reader import Reader

		reader = Reader(Glossary(ui=object()))
		self.assertEqual(len(reader), 0)
		self.assertEqual(reader.countResourceFiles(), 0)

		reader.open(join(testLocalDataDir, "6-en-en-appledict"))
		self.assertEqual(len(reader), 6)
		self.assertEqual(reader.countResourceFiles(), 2)
		reader.close()
		self.assertEqual(len(reader), 0)

		with self.assertRaises(TypeError):
			reader.open(__file__)

	def test_reader_without_resources_or_plist(self):
		"""Test that bundles without a plist or OtherResources are read correctly."""
		inputDirPath = self._copyAppledictFixture("appledict-no-res-plist")
		os.remove(join(inputDirPath, "6-en-en-appledict.plist"))
		shutil.rmtree(join(inputDirPath, "OtherResources"))

		outputFilePath = self.newTempFilePath("appledict-no-res-plist.txt")
		self.glos = Glossary()
		self.glos.convert(
			ConvertArgs(
				inputFilename=inputDirPath,
				outputFilename=outputFilePath,
				inputFormat="AppleDict",
				outputFormat="Tabfile",
			)
		)
		with open(outputFilePath, encoding="utf-8") as file:
			text = file.read()
		self.assertNotIn("##copyright", text)
		self.assertNotIn("##author", text)
		self.assertFalse(isdir(outputFilePath + "_res"))

	def test_reader_plist_errors(self):
		"""Test that invalid or non-dictionary plists are ignored without losing entries."""
		for name, data in (
			("invalid", b"not a plist"),
			("non-dict", plistlib.dumps(["not", "a", "dict"])),
		):
			inputDirPath = self._copyAppledictFixture(f"appledict-plist-{name}")
			with open(
				join(inputDirPath, "6-en-en-appledict.plist"),
				mode="wb",
			) as file:
				file.write(data)

			glos = Glossary()
			self.assertTrue(glos.directRead(inputDirPath, formatName="AppleDict"))
			self.assertEqual(glos.getInfo("copyright"), "")
			glos.cleanup()
			glos.clear()

	def test_reader_xml_resolution_errors(self):
		"""Test single-XML fallback resolution and errors for ambiguous or missing XML."""
		from pyglossary.plugins.appledict.reader import Reader

		inputDirPath = self._copyAppledictFixture("appledict-xml-resolution")
		reader = Reader(Glossary())
		reader.open(inputDirPath)
		reader.close()

		with open(join(inputDirPath, "second.xml"), mode="w", encoding="utf-8") as file:
			file.write("<d:dictionary/>")
		with self.assertRaises(LookupError):
			reader.open(inputDirPath)

		for fname in os.listdir(inputDirPath):
			if fname.endswith(".xml"):
				os.remove(join(inputDirPath, fname))
		with self.assertRaises(LookupError):
			reader.open(inputDirPath)

	def test_convert_appledict_to_appledict_resources(self):
		"""Test round-tripping to ensure resource files survive the writer."""
		inputDirPath = join(testLocalDataDir, "6-en-en-appledict")
		outputDirPath = self.newTempFilePath("6-en-en-appledict-roundtrip.apple")
		self.glos = Glossary()
		result = self.glos.convert(
			ConvertArgs(
				inputFilename=inputDirPath,
				outputFilename=outputDirPath,
				inputFormat="AppleDict",
				outputFormat="AppleDict",
			)
		)
		self.assertEqual(result, outputDirPath)

		_, xml, _ = self._readAppledictOutput(outputDirPath)
		self.assertIn('d:title="alpha"', xml)
		for relPath in ("note.txt", join("audio", "beep.mp3")):
			self.compareBinaryFiles(
				join(outputDirPath, "OtherResources", relPath),
				join(inputDirPath, "OtherResources", relPath),
			)

	def test_convert_tabfile_to_appledict_clean_html(self):
		"""Test all HTML-cleaning writer options produce the expected transformed content."""
		inputFilePath = join(testLocalDataDir, "21-en-en-appledict-src.txt")
		outputDirPath = self.newTempFilePath("21-en-en-appledict-clean-html.apple")
		self.glos = Glossary()
		self.glos.setInfo("copyright", "<b>Copyright fixture</b>")
		self.glos.setInfo("CFBundleIdentifier", "com.example.fixture")

		result = self.glos.convert(
			ConvertArgs(
				inputFilename=inputFilePath,
				outputFilename=outputDirPath,
				inputFormat="Tabfile",
				outputFormat="AppleDict",
				writeOptions={
					"clean_html": True,
					"css": join(testLocalDataDir, "res", "appledict_test.css"),
					"xsl": join(testLocalDataDir, "res", "appledict_test.xsl"),
					"prefs_html": join(
						testLocalDataDir,
						"res",
						"appledict_test_prefs.html",
					),
					"front_back_matter": join(
						testLocalDataDir,
						"res",
						"appledict_test_front_back.xml",
					),
					"default_prefs": {"version": "1", "key": "value"},
					"indexes": "zh",
				},
			)
		)
		self.assertEqual(result, outputDirPath)

		baseName, xml, plist = self._readAppledictOutput(outputDirPath)
		self.assertIn("Front matter.", xml)
		self.assertIn('d:title="plain"', xml)
		self.assertIn("\xa0", xml)
		self.assertIn('<span class="ex" d:priority="2">sec</span>', xml)
		self.assertIn('<div class="m2">two</div>', xml)
		self.assertIn('<div class="ex m3">three</div>', xml)
		self.assertIn("plain xhtml", xml)
		self.assertIn('<span class="u">under</span>', xml)
		self.assertIn("<del>strike</del>", xml)
		self.assertIn("font-weight:bold", xml)
		self.assertIn('href="x-dictionary:d:entry"', xml)
		self.assertIn("javascript:new Audio", xml)
		self.assertIn('src="sound_1.mp3"', xml)
		self.assertIn('src="img/pic.png"', xml)
		self.assertIn('onmousedown="this.lastChild.play(); return false;"', xml)
		self.assertIn("nextElementSibling", xml)
		self.assertIn("previousElementSibling", xml)
		self.assertIn("this.className.match", xml)
		self.assertNotIn("empty title", xml)
		self.assertIn('d:value="ci2."', xml)

		self.assertIn("com.example.fixture", plist)
		self.assertIn("appledict_test.xsl", plist)
		self.assertIn("appledict_test_prefs.html", plist)
		self.assertIn("front_back_matter", plist)
		self.assertIn("<key>key</key>", plist)
		self.assertIn("Copyright fixture", plist)
		self.assertNotIn("&lt;b&gt;", plist)

		resDirPath = join(outputDirPath, "OtherResources")
		self.assertTrue(isfile(join(resDirPath, "appledict_test.xsl")))
		self.assertTrue(isfile(join(resDirPath, "appledict_test_prefs.html")))
		with open(join(outputDirPath, f"{baseName}.css"), encoding="utf-8") as file:
			self.assertIn("color: #333", file.read())
		with open(join(outputDirPath, "Makefile"), encoding="utf-8") as file:
			self.assertIn(baseName, file.read())

	def test_convert_tabfile_to_appledict_without_clean_html(self):
		"""Test the no-BeautifulSoup path so raw HTML transformations stay covered."""
		inputFilePath = join(testLocalDataDir, "21-en-en-appledict-src.txt")
		outputDirPath = self.newTempFilePath("21-en-en-appledict-no-soup.apple")
		self.glos = Glossary()

		result = self.glos.convert(
			ConvertArgs(
				inputFilename=inputFilePath,
				outputFilename=outputDirPath,
				inputFormat="Tabfile",
				outputFormat="AppleDict",
				writeOptions={
					"clean_html": False,
					"indexes": "ru",
				},
			)
		)
		self.assertEqual(result, outputDirPath)

		_, xml, _ = self._readAppledictOutput(outputDirPath)
		self.assertIn("&#160;", xml)
		self.assertIn("<xhtml:p>", xml)
		self.assertIn('<a href="x-dictionary:d:sound://audio.mp3">', xml)
		self.assertIn('<img src="/img/pic.png"//>', xml)
		self.assertIn("<br />", xml)
		self.assertIn("<hr />", xml)
		self.assertIn('d:value="кот-кот."', xml)
		self.assertIn('d:value="кот большой."', xml)
		self.assertIn('d:value="русский."', xml)
		self.assertNotIn('d:value="КОТ."', xml)

	def test_convert_tabfile_to_appledict_invalid_indexes(self):
		"""Test that unsupported index languages raise instead of generating bad indexes."""
		self.glos = Glossary()
		with self.assertRaises(ValueError):
			self.glos.convert(
				ConvertArgs(
					inputFilename=join(
						testLocalDataDir,
						"21-en-en-appledict-src.txt",
					),
					outputFilename=self.newTempFilePath("invalid-indexes.apple"),
					inputFormat="Tabfile",
					outputFormat="AppleDict",
					writeOptions={"indexes": "xx"},
				)
			)

	def test_convert_tabfile_to_appledict_default_prefs(self):
		"""Test invalid prefs version handling and rejection of non-dictionary prefs."""
		inputFilePath = join(testLocalDataDir, "21-en-en-appledict-src.txt")
		outputDirPath = self.newTempFilePath("appledict-default-prefs.apple")
		self.glos = Glossary()
		result = self.glos.convert(
			ConvertArgs(
				inputFilename=inputFilePath,
				outputFilename=outputDirPath,
				inputFormat="Tabfile",
				outputFormat="AppleDict",
				writeOptions={"default_prefs": {"version": "2"}},
			)
		)
		self.assertEqual(result, outputDirPath)

		self.glos = Glossary()
		with self.assertRaises(TypeError):
			self.glos.convert(
				ConvertArgs(
					inputFilename=inputFilePath,
					outputFilename=self.newTempFilePath("bad-prefs.apple"),
					inputFormat="Tabfile",
					outputFormat="AppleDict",
					writeOptions={"default_prefs": ["not", "a", "dict"]},
				)
			)

	def test_convert_tabfile_to_appledict_jing(self):
		"""Test that the Jing writer option invokes schema validation."""
		outputDirPath = self.newTempFilePath("appledict-jing.apple")
		self.glos = Glossary()
		with mock.patch("pyglossary.plugins.appledict.jing.run") as jing_run:
			result = self.glos.convert(
				ConvertArgs(
					inputFilename=join(
						testLocalDataDir,
						"21-en-en-appledict-src.txt",
					),
					outputFilename=outputDirPath,
					inputFormat="Tabfile",
					outputFormat="AppleDict",
					writeOptions={"jing": True},
				)
			)
		self.assertEqual(result, outputDirPath)
		jing_run.assert_called_once()

	def test_convert_xdxf_to_appledict_defi_format_x(self):
		"""Test the XDXF definition path to ensure non-HTML entries are transformed."""
		outputDirPath = self.newTempFilePath("1-en-en-xdxf.apple")
		self.glos = Glossary()
		result = self.glos.convert(
			ConvertArgs(
				inputFilename=join(testLocalDataDir, "1-en-en-xdxf.xdxf"),
				outputFilename=outputDirPath,
				inputFormat="Xdxf",
				outputFormat="AppleDict",
				readOptions={"html": False},
				writeOptions={"clean_html": True},
			)
		)
		self.assertEqual(result, outputDirPath)
		_, xml, _ = self._readAppledictOutput(outputDirPath)
		self.assertIn('d:title="xdxf"', xml)
		self.assertNotIn("<h1>", xml)

	def test_jing_run(self):
		"""Test Jing success and schema-failure results so validation errors propagate."""
		from pyglossary.plugins.appledict.jing import main as jing_main

		with mock.patch(
			"pyglossary.plugins.appledict.jing.main.subprocess.Popen",
		) as popen:
			proc = popen.return_value
			proc.wait.return_value = 0
			proc.communicate.return_value = (b"", None)
			jing_main.run(__file__)

		with mock.patch(
			"pyglossary.plugins.appledict.jing.main.subprocess.Popen",
		) as popen:
			proc = popen.return_value
			proc.wait.return_value = 1
			proc.communicate.return_value = (b"schema error", None)
			with self.assertRaises(jing_main.JingTestError):
				jing_main.run(__file__)

	def test_jing_main(self):
		"""Test Jing CLI exit codes for usage, success, and failure paths."""
		from pyglossary.plugins.appledict.jing import main as jing_main

		with mock.patch.object(sys, "argv", ["jing"]):
			self.assertEqual(jing_main.main(), 1)

		with (
			mock.patch.object(sys, "argv", ["jing", __file__]),
			mock.patch.object(jing_main, "run"),
		):
			self.assertEqual(jing_main.main(), 0)

		with (
			mock.patch.object(sys, "argv", ["jing", __file__]),
			mock.patch.object(
				jing_main,
				"run",
				side_effect=jing_main.JingTestError(1, ["jing"], "failure"),
			),
		):
			self.assertEqual(jing_main.main(), 1)

	def test_jing_module_entry_point(self):
		"""Test the module entry point so `python -m` usage stays working."""
		with (
			mock.patch.object(sys, "argv", ["jing"]),
			self.assertRaises(SystemExit) as cm,
		):
			runpy.run_module(
				"pyglossary.plugins.appledict.jing",
				run_name="__main__",
			)
		self.assertEqual(cm.exception.code, 1)

	def comparePlist(self, fpath1, fpath2):
		"""Compare parsed plist contents for semantic equality rather than raw text."""
		with open(fpath1, "rb") as file:
			data1 = plistlib.loads(file.read())
		with open(fpath2, "rb") as file:
			data2 = plistlib.loads(file.read())
		self.assertEqual(data1, data2)

	def test_tabfile_without_morpho_to_appledict_source(self):
		"""Test remote Tabfile-to-AppleDict conversion against expected source files."""
		self.glos = Glossary()

		inputName = "002-no-morphology-v3"
		outputName = "002-no-morphology-v3a"
		inputFilepath = self.downloadFile(f"appledict-src/{inputName}.txt")
		outputDirPath = self.newTempFilePath(f"{outputName}")

		expectedFiles = {
			name: self.downloadFile(f"appledict-src/{outputName}/{name}")
			for name in [
				f"{outputName}.xml",
				f"{outputName}.css",
				"Makefile",
			]
		}

		result = self.glos.convert(
			ConvertArgs(
				inputFilename=inputFilepath,
				outputFilename=outputDirPath,
				inputFormat="Tabfile",
				outputFormat="AppleDict",
			)
		)
		self.assertIsNotNone(result)
		self.assertEqual(result, outputDirPath)

		for fname, fpath in expectedFiles.items():
			self.compareTextFiles(
				join(outputDirPath, fname),
				fpath,
			)

		self.comparePlist(
			join(outputDirPath, f"{outputName}.plist"),
			self.downloadFile(f"appledict-src/{outputName}/{outputName}.plist"),
		)

	def test_appledict_source_read_entry_count_matches_tabfile(self):
		"""Test round-trip entry counts to ensure no entries are lost."""
		inputName = "002-no-morphology-v3"
		inputFilepath = self.downloadFile(f"appledict-src/{inputName}.txt")

		gl_tab = Glossary()
		gl_tab.directRead(inputFilepath, formatName="Tabfile")
		n_tab = sum(1 for e in gl_tab if not e.isData())
		gl_tab.cleanup()

		outputDirPath = self.newTempFilePath("appledict_roundtrip.apple")
		self.glos = Glossary()
		self.glos.convert(
			ConvertArgs(
				inputFilename=inputFilepath,
				outputFilename=outputDirPath,
				inputFormat="Tabfile",
				outputFormat="AppleDict",
			)
		)

		gl_rd = Glossary()
		self.glos = gl_rd
		gl_rd.directRead(outputDirPath)
		n_rd = sum(1 for e in gl_rd if not e.isData())
		self.assertEqual(n_rd, n_tab)


if __name__ == "__main__":
	unittest.main()
