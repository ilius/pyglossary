#!/usr/bin/python3

import logging


class MockLogHandler(logging.Handler):
	def __init__(self) -> None:
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

	def popLog(self, level: int, msg: str) -> "logging.LogRecord | None":
		if level not in self.recordsByLevel:
			return None
		records = self.recordsByLevel[level]
		for index, record in enumerate(records):
			if record.getMessage() == msg:
				return records.pop(index)
		return None

	def printRemainingLogs(self, level, method: str = "") -> int:
		if level not in self.recordsByLevel:
			return 0
		count = 0
		for record in self.recordsByLevel[level]:
			count += 1
			msg = self.format(record)
			print(f"{method}: {msg!r}")
		return count

	def printRemainingErrors(self, method: str = "") -> int:
		count = self.printRemainingLogs(logging.CRITICAL, method)
		count += self.printRemainingLogs(logging.ERROR, method)
		return count

	def printRemainingwWarnings(self, method: str = "") -> int:
		return self.printRemainingLogs(logging.WARNING, method)


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
