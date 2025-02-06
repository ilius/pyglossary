import unittest

import lxml
from glossary_v2_test import TestGlossaryBase

if not lxml.__version__.startswith("5.3."):
	raise OSError(f"Found lxml=={lxml.__version__}, must use lxml==5.3")


class TestGlossaryJMdict(TestGlossaryBase):
	def __init__(self, *args, **kwargs):
		TestGlossaryBase.__init__(self, *args, **kwargs)

		self.dataFileCRC32.update(
			{
				"050-JMdict-English": "aec9ad8c",
				"050-JMdict-English-v3.txt": "6068b9a7",
			},
		)
		# os.environ["CALC_FILE_SIZE"] = "1"

	def convert_jmdict_txt(self, fname, fname2, **convertArgs):
		self.convert(
			fname,
			f"{fname}-2.txt",
			compareText=f"{fname2}.txt",
			inputFormat="JMDict",
			**convertArgs,
		)

	# with lxml==5.3.0, for "bword://{word}", `word` is not unicode-escaped by lxml
	# while lxml < 5.3.0 does escape these unicode characters
	# that's why 050-JMdict-English-v2 was updated to 050-JMdict-English-v3
	def test_convert_jmdict_txt_1(self):
		self.convert_jmdict_txt(
			"050-JMdict-English",
			"050-JMdict-English-v3",
		)


if __name__ == "__main__":
	unittest.main()
