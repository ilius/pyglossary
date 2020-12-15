# -*- coding: utf-8 -*-

stdCompressions = ("gz", "bz2", "lzma")


def compressionOpenFunc(c: str):
	if not c:
		return open
	if c == "gz":
		import gzip
		return gzip.open
	if c == "bz2":
		import bz2
		return bz2.open
	if c == "lzma":
		import lzma
		return lzma.open
	if c == "dz":
		import gzip
		return gzip.open
	return None


def compressionOpen(filename, dz=False, **kwargs):
	from os.path import splitext
	filenameNoExt, ext = splitext(filename)
	ext = ext.lower().lstrip(".")
	try:
		int(ext)
	except ValueError:
		pass
	else:
		_, ext = splitext(filenameNoExt)
		ext = ext.lower().lstrip(".")
	if ext in stdCompressions or (dz and ext == "dz"):
		_file = compressionOpenFunc(ext)(filename, **kwargs)
		_file.compression = ext
		return _file
	return open(filename, **kwargs)
