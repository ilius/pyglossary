import gzip
import os
import unittest

from glossary_v2_test import TestGlossaryBase


class TestGlossaryKobo(TestGlossaryBase):
	def setUp(self):
		if os.getenv("SKIP_TEST_MISSING_DEP"):
			try:
				import marisa_trie  # noqa: F401
			except ImportError:
				self.skipTest("skipping module due to missing dependency: marisa_trie")
		TestGlossaryBase.setUp(self)

	def __init__(self, *args, **kwargs):
		TestGlossaryBase.__init__(self, *args, **kwargs)
		# self.dataFileCRC32 |= {{})

	def convert_txt_kobo(self, fname, sha1sumDict, **convertArgs):
		outputFname = f"{fname}-2.kobo.zip"
		outputFpath = self.newTempFilePath(outputFname)
		# expectedFpath = self.downloadFile(f"{fname}.kobo.zip")
		self.convert(
			f"{fname}.txt",
			outputFname,
			**convertArgs,
		)
		dataReplaceFuncs = {
			zfname: gzip.decompress for zfname in sha1sumDict if zfname != "words"
		}
		self.checkZipFileSha1sum(
			outputFpath,
			sha1sumDict=sha1sumDict,
			dataReplaceFuncs=dataReplaceFuncs,
		)

	def test_convert_txt_kobo_1(self):
		sha1sumDict = {
			"11.html": "39f0f46560da7398ab0d3b19cc1c2387ecd201dd",
			"aa.html": "df9460450e8b46e913c57bf39dcc799ffdc2fb33",
			"ab.html": "be4271a8508dbb499bafd439810af621a7b3474f",
			"words": "d0f74e854f090fbaa8211bcfd162ad99ec4da0a3",
		}
		self.convert_txt_kobo("100-en-fa", sha1sumDict)

	def test_convert_txt_kobo_2(self):
		sha1sumDict = {
			"words": "1a5debdd530c4ed78214368db931d2767f425cd2",
			"々a.html": "a2258a374f078af361a40c0fba18e13c00462a72",
			"ｔシ.html": "fbaa17f71a8fa39bb552ef0f7eaf5ce6c87b7bc0",
			"アサ.html": "abeff96987c8844db68e55241f8fbb8fcc6d96b3",
			"アホ.html": "c38f00fdabbf8de4b8bb442caf6649f0a734b352",
			"イケ.html": "448c771a3b4834c9aac449f7985324751a3b7743",
			"ウソ.html": "58eda550c5a2c3c8ca7d8ff1a766c33888cccf3e",
			"ウネ.html": "56a56ab66d6a9a70dfbb964f4c5a6d300ae29048",
			"オー.html": "d6099a83b970dfb9bc6b6aae76ffcf91cc559dec",
			"シー.html": "3c2a244a3e7641d812ea7cc7bf0c825147ea0583",
			"否.html": "be52862d983588fa5ca9ee5fdf8aff822e7c404c",
			"斉.html": "cfeb02bfa36726cb952eabca695288d2926a1f7e",
			"論.html": "79f5ab44f6e4e0918526cb6613bdbb456a522689",
			"鱝.html": "538c73d1e664988af8a70175c3159ea53328dd77",
		}
		self.convert_txt_kobo("100-ja-en", sha1sumDict)


if __name__ == "__main__":
	unittest.main()
