import os
import logging
from os.path import (
	isdir,
)

log = logging.getLogger("pyglossary")


def writeTxt(
	glos: "GlossaryType",
	entryFmt: str = "",  # contain {word} and {defi}
	filename: str = "",
	writeInfo: bool = True,
	wordEscapeFunc: "Optional[Callable]" = None,
	defiEscapeFunc: "Optional[Callable]" = None,
	ext: str = ".txt",
	head: str = "",
	tail: str = "",
	outInfoKeysAliasDict: "Optional[Dict[str, str]]" = None,
	encoding: str = "utf-8",
	newline: str = "\n",
	resources: bool = True,
) -> "Generator[None, BaseEntry, None]":
	# TODO: replace outInfoKeysAliasDict arg with a func?
	from .compression import compressionOpen as c_open
	if not entryFmt:
		raise ValueError("entryFmt argument is missing")
	if not filename:
		filename = glos.filename + ext

	if not outInfoKeysAliasDict:
		outInfoKeysAliasDict = {}

	fileObj = c_open(filename, mode="wt", encoding=encoding, newline=newline)

	fileObj.write(head)
	if writeInfo:
		for key, value in glos.iterInfo():
			# both key and value are supposed to be non-empty string
			if not (key and value):
				log.warning(f"skipping info key={key!r}, value={value!r}")
				continue
			key = outInfoKeysAliasDict.get(key, key)
			if not key:
				continue
			word = f"##{key}"
			if wordEscapeFunc is not None:
				word = wordEscapeFunc(word)
				if not word:
					continue
			if defiEscapeFunc is not None:
				value = defiEscapeFunc(value)
				if not value:
					continue
			fileObj.write(entryFmt.format(
				word=word,
				defi=value,
			))
	fileObj.flush()

	myResDir = f"{filename}_res"
	if not isdir(myResDir):
		os.mkdir(myResDir)

	while True:
		entry = yield
		if entry is None:
			break
		if entry.isData():
			if resources:
				entry.save(myResDir)
			continue

		word = entry.s_word
		defi = entry.defi
		if word.startswith("#"):  # FIXME
			continue
		# if glos.getConfig("enable_alts", True):  # FIXME

		if wordEscapeFunc is not None:
			word = wordEscapeFunc(word)
		if defiEscapeFunc is not None:
			defi = defiEscapeFunc(defi)
		fileObj.write(entryFmt.format(word=word, defi=defi))

	if tail:
		fileObj.write(tail)

	fileObj.close()
	if not os.listdir(myResDir):
		os.rmdir(myResDir)
