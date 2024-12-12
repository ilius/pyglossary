# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
import os
from os.path import join
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	import io
	from collections.abc import Callable

	from .glossary_types import GlossaryType


stdCompressions = ("gz", "bz2", "lzma")

log = logging.getLogger("pyglossary")

__all__ = [
	"compress",
	"compressionOpen",
	"compressionOpenFunc",
	"stdCompressions",
	"uncompress",
	"zipFileOrDir",
]


def compressionOpenFunc(c: str) -> Callable | None:
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


def compressionOpen(
	filename: str,
	dz: bool = False,
	**kwargs,  # noqa: ANN003
) -> io.IOBase:
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
		openFunc = compressionOpenFunc(ext)
		if not openFunc:
			raise RuntimeError(f"no compression found for {ext=}")
		file = openFunc(filename, **kwargs)
		file.compression = ext
		return file
	return open(filename, **kwargs)  # noqa: SIM115


def zipFileOrDir(filename: str) -> None:
	import shutil
	import zipfile
	from os.path import (
		isdir,
		isfile,
		split,
	)

	from .os_utils import indir

	def _zipFileAdd(zf: zipfile.ZipFile, filename: str) -> None:
		if isfile(filename):
			zf.write(filename)
			return
		if not isdir(filename):
			raise OSError(f"Not a file or directory: {filename}")
		for subFname in os.listdir(filename):
			_zipFileAdd(zf, join(filename, subFname))

	with zipfile.ZipFile(f"{filename}.zip", mode="w") as zf:
		if isdir(filename):
			dirn, name = split(filename)
			with indir(filename):
				for subFname in os.listdir(filename):
					_zipFileAdd(zf, subFname)

			shutil.rmtree(filename)
			return

		dirn, name = split(filename)
		files = [name]

		if isdir(f"{filename}_res"):
			files.append(f"{name}_res")

		with indir(dirn):
			for fname in files:
				_zipFileAdd(zf, fname)


def compress(_glos: GlossaryType, filename: str, compression: str) -> str:
	"""
	Filename is the existing file path.

	supported compressions: "gz", "bz2", "lzma", "zip".
	"""
	import shutil
	from os.path import isfile

	log.info(f"Compressing {filename!r} with {compression!r}")

	compFilename = f"{filename}.{compression}"
	if compression in stdCompressions:
		openFunc = compressionOpenFunc(compression)
		if not openFunc:
			raise RuntimeError(f"invalid {compression=}")
		with openFunc(compFilename, mode="wb") as dest:
			with open(filename, mode="rb") as source:
				shutil.copyfileobj(source, dest)
		return compFilename

	if compression == "zip":
		try:
			os.remove(compFilename)
		except OSError:
			pass
		try:
			zipFileOrDir(filename)
		except Exception as e:
			log.error(
				f'{e}\nFailed to compress file "{filename}"',
			)
	else:
		raise ValueError(f"unexpected {compression=}")

	if isfile(compFilename):
		return compFilename

	return filename


def uncompress(srcFilename: str, dstFilename: str, compression: str) -> None:
	"""
	Filename is the existing file path.

	supported compressions: "gz", "bz2", "lzma".
	"""
	import shutil

	log.info(f"Uncompressing {srcFilename!r} to {dstFilename!r}")

	if compression in stdCompressions:
		openFunc = compressionOpenFunc(compression)
		if not openFunc:
			raise RuntimeError(f"invalid {compression=}")
		with openFunc(srcFilename, mode="rb") as source:
			with open(dstFilename, mode="wb") as dest:
				shutil.copyfileobj(source, dest)
		return

	# TODO: if compression == "zip":
	raise ValueError(f"unsupported compression {compression!r}")
