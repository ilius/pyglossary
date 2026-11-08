import contextlib
import io
import os
import shutil
import unittest
from os.path import join

from glossary_v2_test import Glossary, TestGlossaryBase, testLocalDataDir

from pyglossary.glossary_v2 import ConvertArgs
from pyglossary.plugins.wordnet.reader import Pointer, Reader, SynSet, WordNet


class TestGlossaryWordNet(TestGlossaryBase):
	def convert_wordnet_txt(self, fname, fname2, **convertArgs):
		inputFilename = join(testLocalDataDir, fname)
		outputFilename = self.newTempFilePath(f"{fname}-tmp.txt")
		self.glos = Glossary()
		result = self.glos.convert(
			ConvertArgs(
				inputFilename=inputFilename,
				outputFilename=outputFilename,
				inputFormat="Wordnet",
				outputFormat="Tabfile",
				**convertArgs,
			),
		)
		self.assertEqual(result, outputFilename)
		self.compareTextFiles(
			outputFilename,
			join(testLocalDataDir, f"{fname2}.txt"),
		)

	def test_convert_wordnet_txt(self):
		self.convert_wordnet_txt("11-en-en-wordnet", "11-en-en-wordnet")

	def test_gram_color(self):
		self.glos = Glossary()
		outputFilename = self.newTempFilePath("11-en-en-wordnet-gram_color.txt")
		result = self.glos.convert(
			ConvertArgs(
				inputFilename=join(testLocalDataDir, "11-en-en-wordnet"),
				outputFilename=outputFilename,
				inputFormat="Wordnet",
				outputFormat="Tabfile",
				readOptions={"gram_color": "red"},
			),
		)
		self.assertEqual(result, outputFilename)
		with open(outputFilename, encoding="utf-8") as file:
			text = file.read()
		self.assertIn('color="red"', text)
		self.assertNotIn('color="green"', text)

	def test_word_title(self):
		self.glos = Glossary()
		outputFilename = self.newTempFilePath("11-en-en-wordnet-word_title.txt")
		result = self.glos.convert(
			ConvertArgs(
				inputFilename=join(testLocalDataDir, "11-en-en-wordnet"),
				outputFilename=outputFilename,
				inputFormat="Wordnet",
				outputFormat="Tabfile",
				readOptions={"word_title": True},
			),
		)
		self.assertEqual(result, outputFilename)
		with open(outputFilename, encoding="utf-8") as file:
			text = file.read()
		self.assertIn("<h1>", text)

	def test_reader_api(self):
		reader = Reader(Glossary())
		self.assertEqual(reader.countResourceFiles(), 0)
		self.assertEqual(len(reader), 0)
		with self.assertRaises(ValueError):
			next(iter(reader))

	def test_process_skips_empty_articles(self):
		wordnet = WordNet(join(testLocalDataDir, "11-en-en-wordnet"), "green")
		wordnet.collector["empty"] = []
		self.assertEqual(list(wordnet.process()), [])

	def test_synset_and_pointer_helpers(self):
		synset = SynSet(b"00001740 03 n 01 entity 0 000 | a thing")
		self.assertEqual(synset.offset, 1740)
		self.assertIn("SynSet", repr(synset))
		pointer = Pointer("~", "00001740", "n", "0101")
		self.assertIn("Pointer", repr(pointer))

	def test_prepare_progress_output(self):
		inputDir = join(self.tempDir, "many-synsets")
		os.makedirs(inputDir)
		header = "  header\n"
		lines = [header]
		offset = len(header)
		for index in range(101):
			line = f"{offset:08d} 03 n 01 word{index} 0 000 | gloss\n"
			lines.append(line)
			offset += len(line)
		with open(join(inputDir, "data.noun"), "w", encoding="utf-8") as file:
			file.writelines(lines)
		wordnet = WordNet(inputDir, "green")
		with contextlib.redirect_stdout(io.StringIO()):
			wordnet.prepare()
		self.assertEqual(len(wordnet.collector), 101)

	def _copy_fixture(self, name):
		return shutil.copytree(
			join(testLocalDataDir, "11-en-en-wordnet"),
			join(self.tempDir, name),
		)

	def test_open_without_copyright(self):
		inputDir = self._copy_fixture("no-copyright")
		indexPath = join(inputDir, "index.noun")
		with open(indexPath, "w", encoding="utf-8") as file:
			file.writelines(f"line {index}\n" for index in range(40))
		reader = Reader(Glossary())
		reader.open(inputDir)
		self.assertEqual(reader._glos.getInfo("creationTime"), "")
		reader.close()

		with open(indexPath, "w", encoding="utf-8") as file:
			file.writelines(f"line {index}\n" for index in range(5))
		reader = Reader(Glossary())
		reader.open(inputDir)
		self.assertEqual(reader._glos.getInfo("creationTime"), "")
		reader.close()

	def test_open_with_non_numeric_copyright_year(self):
		inputDir = self._copy_fixture("bad-copyright")
		indexPath = join(inputDir, "index.noun")
		with open(indexPath, encoding="utf-8") as file:
			text = file.read()
		with open(indexPath, "w", encoding="utf-8") as file:
			file.write(text.replace("Copyright 2011", "Copyright unknown"))
		reader = Reader(Glossary())
		reader.open(inputDir)
		self.assertIn("Princeton University", reader._glos.getInfo("copyright"))
		self.assertEqual(reader._glos.getInfo("creationTime"), "")
		reader.close()


if __name__ == "__main__":
	unittest.main()
