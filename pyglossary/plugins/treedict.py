# -*- coding: utf-8 -*-

from formats_common import *
import subprocess

enable = True
format = "Treedict"
description = "TreeDict"
extensions = (".tree", ".treedict")
optionsProp = {
	"encoding": EncodingOption(),
	"archive": StrOption(
		customValue=False,
		values=[
			"tar.bz2",
			"tar.gz",
			"zip",
		],
	),
	"sep": StrOption(
		customValue=True,
		values=[
			"/",
			"\\",
		],
	),
}
depends = {}


def write(
	glos: GlossaryType,
	filename: str,
	encoding: str = "utf-8",
	sep: str = os.sep,
) -> None:
	if os.path.exists(filename):
		if os.path.isdir(filename):
			if os.listdir(filename):
				log.warning(f"Warning: directory {filename!r} is not empty.")
		else:
			raise IOError(f"{filename!r} is not a directory")
	for entry in glos:
		defi = entry.defi
		for word in entry.l_word:
			if not word:
				log.error("empty word")
				continue
			chars = list(word)
			try:
				os.makedirs(filename + os.sep + sep.join(chars[:-1]))
			except:
				pass
			entryFname = join(filename, sep.join(chars)) + ".m"
			try:
				with open(entryFname, "a", encoding=encoding) as entryFp:
					entryFp.write(defi)
			except:
				log.exception("")
