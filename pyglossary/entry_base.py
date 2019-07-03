# -*- coding: utf-8 -*-

class BaseEntry(object):
	def isData(self):
		raise NotImplementedError

	def getFileName(self):
		raise NotImplementedError

	def getData(self):
		raise NotImplementedError

	def save(self, directory):
		raise NotImplementedError

	def getWord(self):
		raise NotImplementedError

	def getWords(self):
		raise NotImplementedError

	def getDefi(self):
		raise NotImplementedError

	def getDefis(self):
		raise NotImplementedError

	def getDefiFormat(self):
		raise NotImplementedError

	def setDefiFormat(self, defiFormat):
		raise NotImplementedError

	def detectDefiFormat(self):
		raise NotImplementedError

	def addAlt(self, alt):
		raise NotImplementedError

	def editFuncWord(self, func):
		raise NotImplementedError

	def editFuncDefi(self, func):
		raise NotImplementedError

	def strip(self):
		raise NotImplementedError

	def replaceInWord(self, source, target):
		raise NotImplementedError

	def replaceInDefi(self, source, target):
		raise NotImplementedError

	def replace(self, source, target):
		raise NotImplementedError

	def getRaw(self):
		raise NotImplementedError

	def getEntrySortKey(key=None):
		raise NotImplementedError

	def getRawEntrySortKey(key=None):
		raise NotImplementedError

