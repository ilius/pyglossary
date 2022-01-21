#!/usr/bin/python3

import sys
import os
from os.path import join, dirname, abspath, isdir, isfile
import unittest
import logging

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from tests.glossary_errors_test import TestGlossaryErrors
from tests.glossary_test import dataDir
from pyglossary.glossary import Glossary

class TestGlossarySecurity(TestGlossaryErrors):
	def __init__(self, *args, **kwargs):
		TestGlossaryErrors.__init__(self, *args, **kwargs)
		self.mockLog.setLevel(logging.INFO)

	def test_convert_1(self):
		glos = Glossary()
		res = glos.convert(
			inputFilename="os.system('abcd')",
			outputFilename="os.system('abcd -l')",
		)
		self.assertLogCritical("Unable to detect output format!")
		self.assertLogCritical(
			'Writing file "os.system(\'abcd -l\')" failed.'
		)

	def test_convert_2(self):
		glos = Glossary()
		res = glos.convert(
			inputFilename="os.system('abcd');test.txt",
			outputFilename="os.system('abcd -l')",
		)
		self.assertLogCritical("Unable to detect output format!")
		self.assertLogCritical(
			'Writing file "os.system(\'abcd -l\')" failed.'
		)

	def test_convert_3(self):
		glos = Glossary()
		res = glos.convert(
			inputFilename="os.system('abcd');test.txt",
			outputFilename="os.system('abcd -l');test.csv",
		)
		self.assertLogCritical(
			f'[Errno 2] No such file or directory: '
			f'"{dataDir}/os.system(\'abcd\');test.txt"'
		)
		self.assertLogCritical(
			'Reading file "os.system(\'abcd\');test.txt" failed.'
		)

	def test_convert_3(self):
		glos = Glossary()
		res = glos.convert(
			inputFilename="test.txt\nos.system('abcd')",
			outputFilename="test.csv\nos.system('abcd -l')",
		)
		self.assertLogCritical("Unable to detect output format!")
		self.assertLogCritical(
			'Writing file "test.csv\\nos.system(\'abcd -l\')" failed.'
		)
