# -*- coding: utf-8 -*-
# glossary_utils.py
#
# Copyright © 2008-2020 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
# This file is part of PyGlossary project, https://github.com/ilius/pyglossary
#
# This program is a free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. Or on Debian systems, from /usr/share/common-licenses/GPL
# If not, see <http://www.gnu.org/licenses/gpl.txt>.

import os
from os.path import split, isdir, isfile
import subprocess
import logging

from .compression import (
	compressionOpenFunc,
	stdCompressions,
)

log = logging.getLogger("pyglossary")


def zipFileOrDir(glos: "GlossaryType", filename: str):
	from .os_utils import indir
	if isdir(filename):
		dirn, name = split(filename)
		with indir(filename):
			output, error = subprocess.Popen(
				["zip", "-r", f"../{name}.zip", ".", "-m"],
				stdout=subprocess.PIPE,
			).communicate()
			return error

	dirn, name = split(filename)
	files = [name]

	if isdir(f"{filename}_res"):
		files.append(f"{name}_res")

	with indir(dirn):
		output, error = subprocess.Popen(
			["zip", "-mr", f"{filename}.zip"] + files,
			stdout=subprocess.PIPE,
		).communicate()
		return error


def compress(glos: "GlossaryType", filename: str, compression: str) -> str:
	"""
	filename is the existing file path
	supported compressions: "gz", "bz2", "lzma", "zip"
	"""
	import shutil
	log.info(f"Compressing {filename!r} with {compression!r}")

	compFilename = f"{filename}.{compression}"
	if compression in stdCompressions:
		with compressionOpenFunc(compression)(compFilename, mode="wb") as dest:
			with open(filename, mode="rb") as source:
				shutil.copyfileobj(source, dest)
		return compFilename

	if compression == "zip":
		try:
			os.remove(compFilename)
		except OSError:
			pass
		error = zipFileOrDir(glos, filename)
		if error:
			log.error(
				error + "\n" +
				f"Failed to compress file \"{filename}\""
			)
	else:
		raise ValueError(f"unexpected compression={compression!r}")

	if isfile(compFilename):
		return compFilename
	else:
		return filename


def uncompress(srcFilename: str, dstFilename: str, compression: str) -> None:
	"""
	filename is the existing file path
	supported compressions: "gz", "bz2", "lzma"
	"""
	import shutil
	log.info(f"Uncompressing {srcFilename!r} to {dstFilename!r}")

	if compression in stdCompressions:
		with compressionOpenFunc(compression)(srcFilename, mode="rb") as source:
			with open(dstFilename, mode="wb") as dest:
				shutil.copyfileobj(source, dest)
		return

	# TODO: if compression == "zip":
	raise ValueError(f"unexpected compression={compression!r}")
