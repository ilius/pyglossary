# slob format exceptions (pyglossary)
"""
Exception types raised while parsing SLOB archives.

Covers unknown compression/encoding, malformed headers, and file-size mismatches
during SLOB read and write.
"""

from __future__ import annotations

__all__ = [
	"FileFormatException",
	"IncorrectFileSize",
	"UnknownCompression",
	"UnknownEncoding",
	"UnknownFileFormat",
]


class FileFormatException(Exception):
	"""File Format Exception."""


class UnknownFileFormat(FileFormatException):
	"""Unknown File Format."""


class UnknownCompression(FileFormatException):
	"""Unknown Compression."""


class UnknownEncoding(FileFormatException):
	"""Unknown Encoding."""


class IncorrectFileSize(FileFormatException):
	"""Incorrect File Size."""
