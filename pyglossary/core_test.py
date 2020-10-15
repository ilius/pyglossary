#!/usr/bin/python3

import logging


class MockLogHandler(logging.Handler):
	def __init__(self):
		logging.Handler.__init__(self)
		self.clear()

	def clear(self):
		self.recordsByLevel = {}

	def emit(self, record):
		level = record.levelno
		if level in self.recordsByLevel:
			self.recordsByLevel[level].append(record)
		else:
			self.recordsByLevel[level] = [record]

	def popLog(self, level: int, msg: str) -> "Optional[logging.Record]":
		if level not in self.recordsByLevel:
			return None
		records = self.recordsByLevel[level]
		for index, record in enumerate(records):
			if record.getMessage() == msg:
				return records.pop(index)
		return None

	def printRemainingErrors(self) -> int:
		count = 0
		for level in (
			logging.CRITICAL,
			logging.ERROR,
			logging.WARNING,
		):
			if level not in self.recordsByLevel:
				continue
			for record in self.recordsByLevel[level]:
				count += 1
				print(self.format(record))
		return count
