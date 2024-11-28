
from __future__ import annotations
import logging
import re
from operator import itemgetter
from typing import TYPE_CHECKING, Iterable, Iterator

if TYPE_CHECKING:
	from .glossary_types import EntryType, GlossaryExtendedType

__all__ = ["reverseGlossary"]

log = logging.getLogger("pyglossary")


def reverseGlossary(
	glos: GlossaryExtendedType,
	savePath: str = "",
	words: list[str] | None = None,
	includeDefs: bool = False,
	reportStep: int = 300,
	saveStep: int = 1000,  # set this to zero to disable auto saving
	**kwargs,
) -> Iterator[int]:
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
			allowed values: None, "Percent", "Percent At First"
	"""
	if not savePath:
		savePath = glos.getInfo("name") + ".txt"

	if saveStep < 2:
		raise ValueError("saveStep must be more than 1")

	entries: list[EntryType] = list(glos)
	log.info(f"loaded {len(entries)} entries into memory")

	if words:
		words = list(words)
	else:
		words = takeOutputWords(glos, entries)

	wordCount = len(words)
	log.info(
		f"Reversing to file {savePath!r}"
		f", number of words: {wordCount}",
	)
	glos.progressInit("Reversing")
	wcThreshold = wordCount // 200 + 1

	with open(savePath, "w", encoding="utf-8") as saveFile:
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
				**kwargs,
			)
			if result:
				try:
					if includeDefs:
						defi = "\\n\\n".join(result)
					else:
						defi = ", ".join(result) + "."
				except Exception:
					log.exception("")
					log.debug(f"{result = }")
					return
				saveFile.write(f"{word}\t{defi}\n")
			yield wordI

	glos.progressEnd()
	yield wordCount


def takeOutputWords(
	glos: GlossaryExtendedType,
	entryIter: Iterable[EntryType],
	minWordLen: int = 3,
) -> list[str]:
	# fr"[\w]{{{minWordLen},}}"
	wordPattern = re.compile(r"[\w]{%d,}" % minWordLen, re.UNICODE)
	words = set()
	progressbar, glos.progressbar = glos.progressbar, False
	for entry in entryIter:
		words.update(wordPattern.findall(
			entry.defi,
		))
	glos.progressbar = progressbar
	return sorted(words)


def searchWordInDef(
	entryIter: Iterable[EntryType],
	st: str,
	matchWord: bool = True,
	sepChars: str = ".,،",
	maxNum: int = 100,
	minRel: float = 0.0,
	minWordLen: int = 3,
	includeDefs: bool = False,
	showRel: str = "Percent",  # "Percent" | "Percent At First" | ""
) -> list[str]:
	# searches word "st" in definitions of the glossary
	splitPattern = re.compile(
		"|".join(re.escape(x) for x in sepChars),
		re.UNICODE,
	)
	wordPattern = re.compile(r"[\w]{%d,}" % minWordLen, re.UNICODE)
	outRel: list[tuple[str, float] | tuple[str, float, str]] = []
	for entry in entryIter:
		words = entry.l_word
		defi = entry.defi
		if st not in defi:
			continue
		for word in words:
			rel = 0.0  # relation value of word (0 <= rel <= 1)
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
						partWords.count(st) / len(partWords),
					)
				else:
					rel = max(
						rel,
						part.count(st) * len(st) / len(part),
					)
			if rel <= minRel:
				continue
			if includeDefs:
				outRel.append((word, rel, defi))
			else:
				outRel.append((word, rel))
	outRel.sort(
		key=itemgetter(1),
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
			w, num, m = outRel[j]  # type: ignore
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
		w, num = outRel[j]  # type: ignore
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
