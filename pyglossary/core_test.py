#!/usr/bin/python3

import logging
from typing import Optional


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

	def printRemainingLogs(self, level) -> int:
		if level not in self.recordsByLevel:
			return 0
		count = 0
		for record in self.recordsByLevel[level]:
			count += 1
			msg = self.format(record)
			print(f"unhandled log: {msg!r}")
		return count

	def printRemainingErrors(self) -> int:
		count = self.printRemainingLogs(logging.CRITICAL)
		count += self.printRemainingLogs(logging.ERROR)
		return count

	def printRemainingwWarnings(self) -> int:
		return self.printRemainingLogs(logging.WARNING)


mockLog = None


def getMockLogger():
	global mockLog

	if mockLog is not None:
		return mockLog

	log = logging.getLogger("pyglossary")

	for handler in log.handlers:
		log.removeHandler(handler)

	mockLog = MockLogHandler()
	mockLog.setLevel(logging.WARNING)
	log.addHandler(mockLog)
	return mockLog
