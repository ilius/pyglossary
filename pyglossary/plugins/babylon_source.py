# -*- coding: utf-8 -*-

# Source Glossary for "Babylon Builder".
# A plain text file. Not binary like BGL files.

from formats_common import *

enable = True
format = "BabylonSource"
description = "Babylon Source (gls)"
extensions = [".gls", ".babylon"]
optionsProp = {
	"writeInfo": BoolOption(),
	"newline": NewlineOption(),
	"encoding": EncodingOption(),
	"resources": BoolOption(),
}
depends = {}


def entryCleanWinArabic(entry: BaseEntry) -> Optional[BaseEntry]:
	from pyglossary.arabic_utils import cleanWinArabicStr
	entry.editFuncWord(cleanWinArabicStr)
	entry.editFuncDefi(cleanWinArabicStr)
	return entry


def write(
	glos: GlossaryType,
	filename: str,
	writeInfo: bool = True,
	newline: str = "",
	encoding: str = "",
	resources: bool = True,
) -> None:
	g = glos
	entryFilterFunc = None
	if encoding.lower() in ("", "utf8", "utf-8"):
		encoding = "UTF-8"
	elif encoding.lower() in (
		"arabic",
		"windows-1256",
		"windows-arabic",
		"arabic-windows",
		"arabic windows",
		"windows arabic",
	):
		encoding = "windows-1256"
		entryFilterFunc = entryCleanWinArabic
		if not newline:
			newline = "\r\n"

	if not newline:
		newline = "\n"

	head = ""
	if writeInfo:
		head += "\n".join([
			"### Glossary title:%s" % g.getInfo("name"),
			"### Author:%s" % g.getInfo("author"),
			"### Description:%s" % g.getInfo("description"),
			"### Source language:%s" % g.getInfo("inputlang"),
			"### Source alphabet:%s" % encoding,
			"### Target language:%s" % g.getInfo("outputlang"),
			"### Target alphabet:%s" % encoding,
			"### Browsing enabled?Yes",
			"### Type of glossary:00000000",
			"### Case sensitive words?0"
			"",
			"### Glossary section:",
			"",
		])

	g.writeTxt(
		"\n",
		"\n\n",
		filename=filename,
		writeInfo=False,
		rplList=(
			("\n", "<BR>"),
		),
		ext=".gls",
		head=head,
		entryFilterFunc=entryFilterFunc,
		encoding=encoding,
		newline=newline,
		resources=resources,
	)
