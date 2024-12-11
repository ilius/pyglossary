import sys
import unittest
from os.path import abspath, dirname

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from glossary_v2_errors_test import TestGlossaryErrorsBase

from pyglossary.glossary_v2 import ConvertArgs, Glossary

__all__ = ["TestGlossaryStarDictMergeSyns"]


class TestGlossaryStarDictMergeSynsBase(TestGlossaryErrorsBase):
	def convert_txt_stardict(  # noqa: PLR0913
		self,
		fname,
		fname2="",
		syn=True,
		dictzip=False,
		config=None,
		writeOptions=None,
		info=None,
		**convertArgs,
	):
		if not fname2:
			fname2 = fname

		binExtList = ["idx", "dict"]
		if syn:
			binExtList.append("syn")

		inputFilename = self.downloadFile(f"{fname}.txt")
		outputFilename = self.newTempFilePath(f"{fname}.ifo")
		otherFiles = {ext: self.newTempFilePath(f"{fname}.{ext}") for ext in binExtList}

		glos = self.glos = Glossary()
		if info:
			for key, value in info.items():
				glos.setInfo(key, value)

		if config is not None:
			glos.config = config

		if writeOptions is None:
			writeOptions = {}
		writeOptions["dictzip"] = dictzip

		result = glos.convert(
			ConvertArgs(
				inputFilename=inputFilename,
				outputFilename=outputFilename,
				writeOptions=writeOptions,
				outputFormat="StardictMergeSyns",
				**convertArgs,
			)
		)
		self.assertEqual(outputFilename, result)

		self.compareTextFiles(
			outputFilename,
			self.downloadFile(f"{fname2}.sd/{fname2}.ifo"),
		)

		for ext in binExtList:
			self.compareBinaryFiles(
				otherFiles[ext],
				self.downloadFile(f"{fname2}.sd/{fname2}.{ext}"),
			)

	def convert_txt_stardict_zip(  # noqa: PLR0913
		self,
		fname,
		sha1sumDict,
		dictzip=False,
		config=None,
		**convertArgs,
	):
		inputFilename = self.downloadFile(f"{fname}.txt")
		outputFilename = self.newTempFilePath(f"{fname}.zip")

		glos = self.glos = Glossary()

		if config is not None:
			glos.config = config

		result = glos.convert(
			ConvertArgs(
				inputFilename=inputFilename,
				outputFilename=outputFilename,
				outputFormat="StardictMergeSyns",
				writeOptions={
					"dictzip": dictzip,
				},
				**convertArgs,
			)
		)
		self.assertEqual(outputFilename, result)

		self.checkZipFileSha1sum(
			outputFilename,
			sha1sumDict=sha1sumDict,
		)


class TestGlossaryStarDictMergeSyns(TestGlossaryStarDictMergeSynsBase):
	def __init__(self, *args, **kwargs):
		TestGlossaryErrorsBase.__init__(self, *args, **kwargs)

		self.dataFileCRC32.update(
			{
				"100-en-de-v4.sd/100-en-de-v4.dict": "5a97476f",
				"100-en-de-v4.sd/100-en-de-v4.idx": "a99f29d2",
				"100-en-de-v4.sd/100-en-de-v4.ifo": "6529871f",
				"100-en-fa-merge-syns.sd/100-en-fa-merge-syns.dict": "223a0d1d",
				"100-en-fa-merge-syns.sd/100-en-fa-merge-syns.idx": "13f1c7af",
				"100-en-fa-merge-syns.sd/100-en-fa-merge-syns.ifo": "07338eed",
				"002-plain-html.txt": "75484314",
				"002-plain-html.sd/002-plain-html.dict": "2e9d20d8",
				"002-plain-html.sd/002-plain-html.idx": "3956ad72",
				"002-plain-html.sd/002-plain-html.ifo": "1991f125",
				"004-plain-html-alts.txt": "505d4675",
				"004-plain-html-alts-merge-syns.sd/"
				"004-plain-html-alts-merge-syns.dict": "889f11f8",
				"004-plain-html-alts-merge-syns.sd/"
				"004-plain-html-alts-merge-syns.idx": "092ba555",
				"004-plain-html-alts-merge-syns.sd/"
				"004-plain-html-alts-merge-syns.ifo": "628abe99",
			},
		)

	def test_convert_txt_stardict_1_merge_syns(self):
		self.convert_txt_stardict(
			"100-en-fa",
			fname2="100-en-fa-merge-syns",
			syn=False,
		)

	def test_convert_txt_stardict_3_merge_syns(self):
		self.convert_txt_stardict(
			"100-en-de-v4",
			syn=False,
		)

	def test_convert_txt_stardict_general_1_merge_syns(self):
		self.convert_txt_stardict(
			"002-plain-html",
			syn=False,
		)

	def test_convert_txt_stardict_general_2_merge_syns(self):
		self.convert_txt_stardict(
			"004-plain-html-alts",
			fname2="004-plain-html-alts-merge-syns",
			syn=False,
		)


if __name__ == "__main__":
	unittest.main()
