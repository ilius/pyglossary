from pyglossary.file_utils import fileCountLines
from pyglossary.entry import Entry

import logging
log = logging.getLogger('root')


class TextGlossaryReader(object):
	def __init__(self, glos, hasInfo=True):
		self._glos = glos
		self._filename = ''
		self._file = None
		self._hasInfo = True
		self._leadingLinesCount = 0
		self._pendingEntries = []
		self._wordCount = None
		self._pos = -1

	def open(self, filename, encoding='utf-8'):
		self._filename = filename
		self._file = open(filename, 'r', encoding=encoding)
		if self._hasInfo:
			self.loadInfo()

	def close(self):
		if not self._file:
			return
		try:
			self._file.close()
		except:
			log.exception('error while closing file "%s"' % self._filename)
		self._file = None

	def loadInfo(self):
		self._pendingEntries = []
		self._leadingLinesCount = 0
		try:
			while True:
				wordDefi = self.nextPair()
				if not wordDefi:
					continue
				word, defi = wordDefi
				if not self.isInfoWord(word):
					self._pendingEntries.append(Entry(word, defi))
					break
				self._leadingLinesCount += 1
				word = self.fixInfoWord(word)
				if not word:
					continue
				self._glos.setInfo(word, defi)
		except StopIteration:
			pass

	def __next__(self):
		self._pos += 1
		try:
			return self._pendingEntries.pop(0)
		except IndexError:
			pass
		###
		try:
			wordDefi = self.nextPair()
		except StopIteration as e:
			self._wordCount = self._pos
			raise e
		if not wordDefi:
			return
		word, defi = wordDefi
		###
		return Entry(word, defi)

	def __len__(self):
		if self._wordCount is None:
			log.debug('Try not to use len(reader) as it takes extra time')
			self._wordCount = fileCountLines(self._filename) - \
				self._leadingLinesCount
		return self._wordCount

	def __iter__(self):
		return self

	def isInfoWord(self, word):
		raise NotImplementedError

	def fixInfoWord(self, word):
		raise NotImplementedError

	def nextPair(self):
		raise NotImplementedError
