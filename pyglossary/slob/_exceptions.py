# slob format exceptions (pyglossary)
from __future__ import annotations


class FileFormatException(Exception):
	pass


class UnknownFileFormat(FileFormatException):
	pass


class UnknownCompression(FileFormatException):
	pass


class UnknownEncoding(FileFormatException):
	pass


class IncorrectFileSize(FileFormatException):
	pass
