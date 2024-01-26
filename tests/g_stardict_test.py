import sys
import unittest
from os.path import abspath, dirname, relpath

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from glossary_errors_test import TestGlossaryErrorsBase

from pyglossary.glossary import Glossary


class TestGlossaryStarDictBase(TestGlossaryErrorsBase):
	def convert_txt_stardict(
		self,
		fname,
		fname2="",
		syn=True,
		dictzip=False,
		config=None,
		rawEntryCompress=None,
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

		glos = self.glos = Glossary(info=info)

		if config is not None:
			glos.config = config

		if rawEntryCompress is not None:
			glos.setRawEntryCompress(rawEntryCompress)

		if writeOptions is None:
			writeOptions = {}
		writeOptions["dictzip"] = dictzip

		result = glos.convert(
			inputFilename=inputFilename,
			outputFilename=outputFilename,
			writeOptions=writeOptions,
			**convertArgs,
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

	def convert_txt_stardict_zip(
		self,
		fname,
		sha1sumDict,
		dictzip=False,
		config=None,
		rawEntryCompress=None,
		**convertArgs,
	):
		inputFilename = self.downloadFile(f"{fname}.txt")
		outputFilename = self.newTempFilePath(f"{fname}.zip")

		glos = self.glos = Glossary()

		if config is not None:
			glos.config = config

		if rawEntryCompress is not None:
			glos.setRawEntryCompress(rawEntryCompress)

		result = glos.convert(
			inputFilename=inputFilename,
			outputFilename=outputFilename,
			outputFormat="Stardict",
			writeOptions={
				"dictzip": dictzip,
			},
			**convertArgs,
		)
		self.assertEqual(outputFilename, result)

		self.checkZipFileSha1sum(
			outputFilename,
			sha1sumDict=sha1sumDict,
		)

	def convert_stardict_txt(
		self,
		inputFname: str,
		outputFname: str,
		testId: str,
		syn=True,
		**convertArgs,
	):
		binExtList = ["idx", "dict"]
		if syn:
			binExtList.append("syn")
		for ext in binExtList:
			self.downloadFile(f"{inputFname}.sd/{inputFname}.{ext}")

		inputFilename = self.downloadFile(f"{inputFname}.sd/{inputFname}.ifo")
		outputFilename = self.newTempFilePath(
			f"{inputFname}-{testId}.txt",
		)
		expectedFilename = self.downloadFile(f"{outputFname}.txt")
		glos = self.glos = Glossary()

		result = glos.convert(
			inputFilename=inputFilename,
			outputFilename=outputFilename,
			**convertArgs,
		)
		self.assertEqual(outputFilename, result)

		self.compareTextFiles(outputFilename, expectedFilename)


class TestGlossaryStarDict(TestGlossaryStarDictBase):
	def __init__(self, *args, **kwargs):
		TestGlossaryErrorsBase.__init__(self, *args, **kwargs)

		self.dataFileCRC32.update(
			{
				"004-bar.sd/004-bar.dict": "9ea397f8",
				"004-bar.sd/004-bar.idx": "cf9440cf",
				"004-bar.sd/004-bar.ifo": "ada870e4",
				"004-bar.sd/004-bar.syn": "286b17bf",
				"100-en-de-v4.sd/100-en-de-v4.dict": "5a97476f",
				"100-en-de-v4.sd/100-en-de-v4.idx": "a99f29d2",
				"100-en-de-v4.sd/100-en-de-v4.ifo": "6529871f",
				"100-en-fa.sd/100-en-fa.dict": "223a0d1d",
				"100-en-fa.sd/100-en-fa.idx": "6df43378",
				"100-en-fa.sd/100-en-fa.ifo": "3f2086cd",
				"100-en-fa.sd/100-en-fa.syn": "1160fa0b",
				"100-en-fa-sd.txt": "85f9d3fc",
				# FIXME: remove empty description line from 100-en-fa.ifo
				# stardict-mixed-types-1.ifo, "stardict-mixed-types-2.ifo
				"100-en-fa-merge-syns.sd/100-en-fa-merge-syns.dict": "223a0d1d",
				"100-en-fa-merge-syns.sd/100-en-fa-merge-syns.idx": "13f1c7af",
				"100-en-fa-merge-syns.sd/100-en-fa-merge-syns.ifo": "07338eed",
				"100-ja-en.sd/100-ja-en.dict": "39715f01",
				"100-ja-en.sd/100-ja-en.idx": "adf0e552",
				"100-ja-en.sd/100-ja-en.ifo": "b01e368c",
				"100-ja-en.sd/100-ja-en.syn": "76e6df95",
				"300-ru-en.txt": "77cfee2f",
				"300-ru-en.sd/300-ru-en.dict": "8be7fa4c",
				"300-ru-en.sd/300-ru-en.idx": "1cd30f1a",
				"300-ru-en.sd/300-ru-en.ifo": "0b135812",
				"300-ru-en.sd/300-ru-en.syn": "87ee3372",
				"stardict-mixed-types-2.sd/stardict-mixed-types-2.dict": "2e43237a",
				"stardict-mixed-types-2.sd/stardict-mixed-types-2.idx": "65a1f9fc",
				"stardict-mixed-types-2.sd/stardict-mixed-types-2.ifo": "e1063b84",
				"stardict-mixed-types-2.sd.txt": "94de4bc6",
				"002-plain-html.txt": "75484314",
				"002-plain-html.sd/002-plain-html.dict": "2e9d20d8",
				"002-plain-html.sd/002-plain-html.idx": "3956ad72",
				"002-plain-html.sd/002-plain-html.ifo": "1991f125",
				"004-plain-html-alts.txt": "505d4675",
				"004-plain-html-alts.sd/004-plain-html-alts.dict": "889f11f8",
				"004-plain-html-alts.sd/004-plain-html-alts.idx": "edbe368d",
				"004-plain-html-alts.sd/004-plain-html-alts.ifo": "b9b92fa3",
				"004-plain-html-alts.sd/004-plain-html-alts.syn": "c07f7111",
				"004-plain-html-alts-merge-syns.sd/"
				"004-plain-html-alts-merge-syns.dict": "889f11f8",
				"004-plain-html-alts-merge-syns.sd/"
				"004-plain-html-alts-merge-syns.idx": "092ba555",
				"004-plain-html-alts-merge-syns.sd/"
				"004-plain-html-alts-merge-syns.ifo": "628abe99",
			},
		)

	def test_convert_txt_stardict_0(self):
		self.convert_txt_stardict(
			"100-en-fa",
			config={"auto_sqlite": True},
			direct=True,
		)

	def test_convert_txt_stardict_1(self):
		for sqlite in (None, False, True):
			for rawEntryCompress in (None, True, False):
				self.convert_txt_stardict(
					"100-en-fa",
					rawEntryCompress=rawEntryCompress,
					sqlite=sqlite,
				)

	def test_convert_txt_stardict_1_merge_syns(self):
		self.convert_txt_stardict(
			"100-en-fa",
			fname2="100-en-fa-merge-syns",
			syn=False,
			writeOptions={"merge_syns": True},
		)

	def test_convert_txt_stardict_1_zip(self):
		sha1sumDict = {
			"100-en-fa.dict": "1e462e829f9e2bf854ceac2ef8bc55911460c79e",
			"100-en-fa.idx": "943005945b35abf3a3e7b80375c76daa87e810f0",
			"100-en-fa.ifo": "3e982a76f83eef66a8d4915e7a0018746f4180bc",
			"100-en-fa.syn": "fcefc76628fed18b84b9aa83cd7139721b488545",
		}
		for sqlite in (None, False, True):
			self.convert_txt_stardict_zip(
				"100-en-fa",
				sha1sumDict=sha1sumDict,
				sqlite=sqlite,
			)

	def test_convert_txt_stardict_2(self):
		for sqlite in (None, False, True):
			for rawEntryCompress in (None, True, False):
				self.convert_txt_stardict(
					"004-bar",
					rawEntryCompress=rawEntryCompress,
					sqlite=sqlite,
				)

	def test_convert_txt_stardict_3(self):
		for sqlite in (None, False, True):
			self.convert_txt_stardict(
				"100-en-de-v4",
				syn=False,
				sqlite=sqlite,
			)

	def test_convert_txt_stardict_3_merge_syns(self):
		self.convert_txt_stardict(
			"100-en-de-v4",
			syn=False,
			writeOptions={"merge_syns": True},
		)

	def test_convert_txt_stardict_4(self):
		for sqlite in (None, False, True):
			self.convert_txt_stardict(
				"100-ja-en",
				syn=True,
				sqlite=sqlite,
			)

	def test_convert_txt_stardict_5(self):
		for sqlite in (None, False, True):
			self.convert_txt_stardict(
				"300-ru-en",
				syn=True,
				sqlite=sqlite,
			)

	def test_convert_txt_stardict_sqlite_no_alts(self):
		self.convert_txt_stardict(
			"100-en-fa",
			config={"enable_alts": False},
			sqlite=True,
		)
		self.assertLogWarning(
			"SQLite mode only works with enable_alts=True, force-enabling it.",
		)

	def test_convert_stardict_txt_1(self):
		self.convert_stardict_txt(
			"100-en-fa",
			"100-en-fa-sd",
			"1",
		)

	def test_convert_stardict_txt_mixed_types_1(self):
		self.convert_stardict_txt(
			"stardict-mixed-types-2",
			"stardict-mixed-types-2.sd",
			"mixed-types-1",
			syn=False,
		)

	def test_convert_stardict_txt_mixed_types_2(self):
		self.convert_stardict_txt(
			"stardict-mixed-types-2",
			"stardict-mixed-types-2.sd",
			"mixed-types-1",
			syn=False,
			readOptions={"xdxf_to_html": False},
		)

	def test_convert_txt_stardict_general_1(self):
		self.convert_txt_stardict(
			"002-plain-html",
			syn=False,
		)

	def test_convert_txt_stardict_general_1_merge_syns(self):
		self.convert_txt_stardict(
			"002-plain-html",
			syn=False,
			writeOptions={"merge_syns": True},
		)

	def test_convert_txt_stardict_general_2(self):
		self.convert_txt_stardict(
			"004-plain-html-alts",
			syn=True,
		)

	def test_convert_txt_stardict_general_2_merge_syns(self):
		self.convert_txt_stardict(
			"004-plain-html-alts",
			fname2="004-plain-html-alts-merge-syns",
			syn=False,
			writeOptions={"merge_syns": True},
		)


class TestGlossaryErrorsStarDict(TestGlossaryErrorsBase):
	def __init__(self, *args, **kwargs):
		TestGlossaryErrorsBase.__init__(self, *args, **kwargs)

	def test_convert_from_stardict_invalid_sametypesequence(self):
		fname = "foobar"
		inputFilename = self.newTempFilePath(f"{fname}.ifo")
		outputFilename = self.newTempFilePath(f"{fname}.txt")

		with open(inputFilename, mode="w") as _file:
			_file.write(
				"""StarDict's dict ifo file
version=3.0.0
bookname=Test
wordcount=123
idxfilesize=1234
sametypesequence=abcd
""",
			)

		glos = self.glos = Glossary()

		result = glos.convert(
			inputFilename=inputFilename,
			outputFilename=outputFilename,
		)
		self.assertIsNone(result)
		self.assertLogCritical("Invalid sametypesequence = 'abcd'")
		self.assertLogCritical(f"Reading file {relpath(inputFilename)!r} failed.")


if __name__ == "__main__":
	unittest.main()
