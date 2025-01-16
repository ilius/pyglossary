import datetime
import hashlib
import sys
import unittest
from os.path import abspath, dirname

from freezegun import freeze_time

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from glossary_v2_test import TestGlossaryBase

from pyglossary.glossary_v2 import ConvertArgs, Glossary

testTimeEpoch = 1730579400
testTime = datetime.datetime.fromtimestamp(testTimeEpoch, tz=datetime.timezone.utc)


class TestGlossaryEPUB2(TestGlossaryBase):
	def __init__(self, *args, **kwargs):
		TestGlossaryBase.__init__(self, *args, **kwargs)

		self.dataFileCRC32.update(
			{
				"050-JMdict-English-v3.txt": "6068b9a7",
			},
		)

	def convert_to_yomichan(
		self,
		inputFname,
		testId,
		sha1sum="",
		**convertArgs,
	):
		inputFilename = self.downloadFile(inputFname)
		outputFilename = self.newTempFilePath(
			f"{inputFname.replace('.', '_')}-{testId}.zip",
		)

		glos = self.glos = Glossary()
		res = glos.convert(
			ConvertArgs(
				inputFilename=inputFilename,
				outputFilename=outputFilename,
				outputFormat="Yomichan",
				**convertArgs,
			)
		)
		self.assertEqual(outputFilename, res)

		if sha1sum:
			with open(outputFilename, mode="rb") as _file:
				actualSha1 = hashlib.sha1(_file.read()).hexdigest()
			self.assertEqual(sha1sum, actualSha1, f"{outputFilename=}")

	@freeze_time(testTime)
	def test_convert_txt_yomichan_1(self):
		self.convert_to_yomichan(
			"050-JMdict-English-v3.txt",
			testId="1",
			sha1sum="e54bc12755924586c306831b54a44a3dfd45cf7b",
		)


if __name__ == "__main__":
	unittest.main()
