from .glossary_type import GlossaryType
from .entry import Entry, BaseEntry

import re

import logging
log = logging.getLogger("pyglossary")


def reverseGlossary(
	glos: GlossaryType,
	savePath: str = "",
	words: "Optional[List[str]]" = None,
	includeDefs: bool = False,
	reportStep: int = 300,
	saveStep: int = 1000,  # set this to zero to disable auto saving
	**kwargs
) -> "Iterator[int]":
	"""
	This is a generator
	Usage:
		for wordIndex in glos.reverse(...):
			pass

	Inside the `for` loop, you can pause by waiting (for input or a flag)
		or stop by breaking

	Potential keyword arguments:
		words = None ## None, or list
		reportStep = 300
		saveStep = 1000
		savePath = ""
		matchWord = True
		sepChars = ".,،"
		maxNum = 100
		minRel = 0.0
		minWordLen = 3
		includeDefs = False
		showRel = "None"
			allowed values: "None", "Percent", "Percent At First"
	"""
	if not savePath:
		savePath = glos.getInfo("name") + ".txt"

	if saveStep < 2:
		raise ValueError("saveStep must be more than 1")

	ui = glos.ui

	entries = []
	for entry in glos:
		entries.append(entry)
	log.info(f"loaded {len(entries)} entries into memory")

	if words:
		words = list(words)
	else:
		words = takeOutputWords(glos, entries)

	wordCount = len(words)
	log.info(
		f"Reversing to file {savePath!r}"
		f", number of words: {wordCount}"
	)
	glos.progressInit("Reversing")
	wcThreshold = wordCount // 200 + 1

	with open(savePath, "w") as saveFile:
		for wordI in range(wordCount):
			word = words[wordI]
			if wordI % wcThreshold == 0:
				glos.progress(wordI, wordCount)

			if wordI % saveStep == 0 and wordI > 0:
				saveFile.flush()
			result = searchWordInDef(
				entries,
				word,
				includeDefs=includeDefs,
				**kwargs
			)
			if result:
				try:
					if includeDefs:
						defi = "\\n\\n".join(result)
					else:
						defi = ", ".join(result) + "."
				except Exception:
					log.exception("")
					log.debug(f"result = {result}")
					return
				saveFile.write(f"{word}\t{defi}\n")
			yield wordI

	glos.progressEnd()
	yield wordCount


def takeOutputWords(
	glos: GlossaryType,
	entryIter: "Iterator[BaseEntry]",
	minWordLen: int = 3,
) -> "List[str]":
	# fr"[\w]{{{minWordLen},}}"
	wordPattern = re.compile(r"[\w]{%d,}" % minWordLen, re.U)
	words = set()
	progressbar, glos._progressbar = glos._progressbar, False
	for entry in entryIter:
		words.update(wordPattern.findall(
			entry.defi,
		))
	glos._progressbar = progressbar
	return sorted(words)


def searchWordInDef(
	entryIter: "Iterator[BaseEntry]",
	st: str,
	matchWord: bool = True,
	sepChars: str = ".,،",
	maxNum: int = 100,
	minRel: float = 0.0,
	minWordLen: int = 3,
	includeDefs: bool = False,
	showRel: str = "Percent",  # "Percent" | "Percent At First" | ""
) -> "List[str]":
	# searches word "st" in definitions of the glossary
	splitPattern = re.compile(
		"|".join([re.escape(x) for x in sepChars]),
		re.U,
	)
	wordPattern = re.compile(r"[\w]{%d,}" % minWordLen, re.U)
	outRel = []
	for entry in entryIter:
		words = entry.l_word
		defi = entry.defi
		if st not in defi:
			continue
		for word in words:
			rel = 0  # relation value of word (0 <= rel <= 1)
			for part in splitPattern.split(defi):
				if not part:
					continue
				if matchWord:
					partWords = wordPattern.findall(
						part,
					)
					if not partWords:
						continue
					rel = max(
						rel,
						partWords.count(st) / len(partWords)
					)
				else:
					rel = max(
						rel,
						part.count(st) * len(st) / len(part)
					)
			if rel <= minRel:
				continue
			if includeDefs:
				outRel.append((word, rel, defi))
			else:
				outRel.append((word, rel))
	outRel.sort(
		key=lambda x: x[1],
		reverse=True,
	)
	n = len(outRel)
	if n > maxNum > 0:
		outRel = outRel[:maxNum]
		n = maxNum
	num = 0
	out = []
	if includeDefs:
		for j in range(n):
			numP = num
			w, num, m = outRel[j]
			m = m.replace("\n", "\\n").replace("\t", "\\t")
			onePer = int(1.0 / num)
			if onePer == 1.0:
				out.append(f"{w}\\n{m}")
			elif showRel == "Percent":
				out.append(f"{w}(%{100*num})\\n{m}")
			elif showRel == "Percent At First":
				if num == numP:
					out.append(f"{w}\\n{m}")
				else:
					out.append(f"{w}(%{100*num})\\n{m}")
			else:
				out.append(f"{w}\\n{m}")
		return out
	for j in range(n):
		numP = num
		w, num = outRel[j]
		onePer = int(1.0 / num)
		if onePer == 1.0:
			out.append(w)
		elif showRel == "Percent":
			out.append(f"{w}(%{100*num})")
		elif showRel == "Percent At First":
			if num == numP:
				out.append(w)
			else:
				out.append(f"{w}(%{100*num})")
		else:
			out.append(w)
	return out
