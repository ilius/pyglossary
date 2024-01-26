import unittest

from glossary_v2_test import TestGlossaryBase


class TestGlossaryJMdict(TestGlossaryBase):
	def __init__(self, *args, **kwargs):
		TestGlossaryBase.__init__(self, *args, **kwargs)

		self.dataFileCRC32.update(
			{
				"050-JMdict-English": "aec9ad8c",
				"050-JMdict-English-v2.txt": "cc87ff65",
			},
		)

	def convert_jmdict_txt(self, fname, fname2, **convertArgs):
		self.convert(
			fname,
			f"{fname}-2.txt",
			compareText=f"{fname2}.txt",
			inputFormat="JMDict",
			**convertArgs,
		)

	def test_convert_jmdict_txt_1(self):
		self.convert_jmdict_txt(
			"050-JMdict-English",
			"050-JMdict-English-v2",
		)


if __name__ == "__main__":
	unittest.main()
