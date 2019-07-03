# -*- coding: utf-8 -*-
# http://www.octopus-studio.com/download.en.htm

from formats_common import *
from collections import OrderedDict

enable = True
format = "OctopusMdictSource"
description = "Octopus MDict Source"
extensions = [".mtxt"]
optionsProp = {
	"encoding": EncodingOption(),
	"links": BoolOption(),
	"resources": BoolOption(),
}
depends = {}


def read(
	glos,
	filename,
	encoding="utf-8",
	links=False,
):
	with open(filename, encoding=encoding) as fp:
		text = fp.read()
	text = text.replace("\r\n", "\n")
	text = text.replace("entry://", "bword://")
	lastEntry = None
	linksDict = {}
	entryDict = OrderedDict()
	for section in text.split("</>"):
		lines = section.strip().split("\n")
		if len(lines) < 2:
			continue
		word = lines[0]
		defi = "\n".join(lines[1:])

		if defi.startswith("@@@LINK="):
			mainWord = defi.partition("=")[2]
			if links:
				linksDict[word] = mainWord
			elif lastEntry and lastEntry.getWords()[0] == mainWord:
				lastEntry.addAlt(word)
			else:
				log.error("alternate is not ride after word: %s", defi)
			continue

		entry = glos.newEntry(word, defi)
		if links:
			# do not call glos.addEntry or glos.addEntryObj
			# because we will need to modify entries at the end
			# and we need to keep a OrderedDict of entries (ordered list of entries, and dict of entries by word)
			entryDict[word] = entry
		else:
			if lastEntry:
				# now that we know there are no more alternate forms of lastEntry
				glos.addEntryObj(lastEntry)
			lastEntry = entry

	if links:
		for sourceWord, targetWord in linksDict.items():
			targetEntry = entryDict.get(targetWord)
			if targetEntry is None:
				log.error("Link to non-existing word %s" % targetWord)
				continue
			targetEntry.addAlt(sourceWord)
		for entry in entryDict.values():
			glos.addEntryObj(entry)
	else:
		if lastEntry:
			glos.addEntryObj(lastEntry)

def writeEntryGen(glos):
	for entry in glos:
		words = entry.getWords()
		defis = entry.getDefis()

		yield glos.newEntry(words[0], defis)

		for alt in words[1:]:
			yield glos.newEntry(
				alt,
				"@@@LINK=%s" % words[0],
			)


def write(
	glos,
	filename,
	resources=True,
):
	glos.writeTxt(
		"\n",
		"\n</>\n",
		filename=filename,
		writeInfo=False,
		rplList=[
			("bword://", "entry://"),
		],
		ext=".mtxt",
		head="",
		iterEntries=writeEntryGen(glos),
		newline="\r\n",
		resources=resources,
	)
