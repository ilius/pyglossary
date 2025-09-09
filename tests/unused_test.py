import sys
import unittest
from os.path import abspath, dirname

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from pyglossary import __version__
from pyglossary.logger import format_exception
from pyglossary.plugins.ebook_kobo import (
	description,
	enable,
	extensionCreate,
	extensions,
	kind,
	lname,
	name,
	optionsProp,
	singleFile,
	website,
	wiki,
)
from pyglossary.plugins.stardict import (
	Reader,
	description,
	enable,
	extensionCreate,
	extensions,
	kind,
	lname,
	name,
	optionsProp,
	singleFile,
	website,
	wiki,
)
from pyglossary.plugins.tabfile import (
	Writer,
	description,
	enable,
	extensionCreate,
	extensions,
	kind,
	lname,
	name,
	optionsProp,
	singleFile,
	website,
	wiki,
)
from pyglossary.sort_keys import LocaleNamedSortKey


class TestDummy(unittest.TestCase):
	def test_test(self):
		pass
