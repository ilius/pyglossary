import sys
from os.path import dirname, abspath
import unittest

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from tests.glossary_test import TestGlossaryBase
from pyglossary.glossary import Glossary
from pyglossary.plugins.appledict_bin import Reader


class TestGlossaryAppleDictBin(TestGlossaryBase):
	def __init__(self, *args, **kwargs):
		TestGlossaryBase.__init__(self, *args, **kwargs)

		self.dataFileCRC32.update({
			"appledict-bin/002-appledict-bin-no-morphology.dictionary/Contents/Body.data": "3c073986",
			"appledict-bin/002-appledict-bin-no-morphology.dictionary/Contents/DefaultStyle.css": "a83210cb",
			"appledict-bin/002-appledict-bin-no-morphology.dictionary/Contents/EntryID.data": "37305249",
			"appledict-bin/002-appledict-bin-no-morphology.dictionary/Contents/EntryID.index": "8c30a3fa",
			"appledict-bin/002-appledict-bin-no-morphology.dictionary/Contents/Info.plist": "fa73dd65",
			"appledict-bin/002-appledict-bin-no-morphology.dictionary/Contents/KeyText.data": "aefe15e0",
			"appledict-bin/002-appledict-bin-no-morphology.dictionary/Contents/KeyText.index": "b723c5b2",
			"appledict-bin/002-appledict-bin-no-morphology.dictionary/Contents/MyDictionary.xsl": "023de1ea",
			"appledict-bin/002-appledict-bin-no-morphology.dictionary/Contents/MyDictionary_prefs.html": "09a9f6e9",
			"appledict-bin/002-appledict-bin-no-morphology.dictionary/appledict-source_expected.xml": "9c30ae49",
			"appledict-bin/002-appledict-bin-no-morphology.dictionary/stardict_expected.xml": "bf521bfc",
		})

	def test_fix_links(self):
		glos = Glossary()
		reader = Reader(glos)
		f = reader.fixLinksInDefi
		self.assertEqual(
			f('foo <a id="123" href="hello">test</a> bar'),
			'foo <a id="123" href="bword://hello">test</a> bar',
		)
		self.assertEqual(
			f('foo <a href="http://github.com" id="123">test</a> bar'),
			'foo <a href="http://github.com" id="123">test</a> bar',
		)
		self.assertEqual(
			f('foo <a href="https://github.com" id="123">test</a> bar'),
			'foo <a href="https://github.com" id="123">test</a> bar',
		)
		self.assertEqual(
			f('foo <a id="123" href="hello">test</a> bar'),
			'foo <a id="123" href="bword://hello">test</a> bar',
		)
		self.assertEqual(
			f('foo <a id="123" href="x-dictionary:d:hello">test</a> bar'),
			'foo <a id="123" href="bword://hello">test</a> bar',
		)
		self.assertEqual(
			f(
				'<a href="x-dictionary:r:123:com.apple.dictionary.no.oup'
				'#xpointer(//*[@id=\'234\'])" title="test">'
			),
			'<a href="bword://test" title="test">',
		)

	def test_binary_to_source(self):
		self.glos = Glossary()

		folder_input = 'appledict-bin/002-appledict-bin-no-morphology.dictionary'
		folder_output = 'no-morphology.source'

		result = self.glos.convert(
			inputFilename=f'./{folder_input}',
			outputFilename=f'./{folder_output}',
			inputFormat="AppleDictBin",
			outputFormat="AppleDict",
		)

		self.compareTextFiles(
			f'./{folder_output}/no-morphology_source.xml',
			self.downloadFile('appledict-bin/002-appledict-bin-no-morphology.dictionary/appledict-source_expected.xml'),
		)

	def test_binary_to_stardict(self):
		self.glos = Glossary()

		folder_input = 'appledict-bin/002-appledict-bin-no-morphology.dictionary'
		folder_output = 'no-morphology.source'

		result = self.glos.convert(
			inputFilename=f'./{folder_input}',
			outputFilename=f'./{folder_output}/stardict.xml',
			inputFormat="AppleDictBin",
			outputFormat="StardictTextual",
		)

		self.compareTextFiles(
			f'./{folder_output}/stardict.xml',
			self.downloadFile('appledict-bin/002-appledict-bin-no-morphology.dictionary/stardict_expected.xml'),
		)

