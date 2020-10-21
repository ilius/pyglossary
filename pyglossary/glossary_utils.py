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


def zipOutDir(filename: str):
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
	with indir(dirn):
		output, error = subprocess.Popen(
			["zip", f"{filename}.zip", name, "-m"],
			stdout=subprocess.PIPE,
		).communicate()
		return error


def compressOutDir(filename: str, compression: str) -> str:
	"""
	filename is the existing file path
	compression is the archive extension (without dot): "gz", "bz2", "zip"
	"""
	try:
		os.remove(f"{filename}.{compression}")
	except OSError:
		pass
	if compression == "gz":
		output, error = subprocess.Popen(
			["gzip", filename],
			stdout=subprocess.PIPE,
		).communicate()
		if error:
			log.error(
				error + "\n" +
				f"Failed to compress file \"{filename}\""
			)
	elif compression == "bz2":
		output, error = subprocess.Popen(
			["bzip2", filename],
			stdout=subprocess.PIPE,
		).communicate()
		if error:
			log.error(
				error + "\n" +
				f"Failed to compress file \"{filename}\""
			)
	elif compression == "zip":
		error = zipOutDir(filename)
		if error:
			log.error(
				error + "\n" +
				f"Failed to compress file \"{filename}\""
			)

	compressedFilename = f"{filename}.{compression}"
	if isfile(compressedFilename):
		return compressedFilename
	else:
		return filename
