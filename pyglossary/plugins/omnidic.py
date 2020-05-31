# -*- coding: utf-8 -*-

from formats_common import *

enable = True
format = "Omnidic"
description = "Omnidic"
extensions = [".omni", ".omnidic"]
optionsProp = {
	"dicIndex": IntOption(),
}
depends = {}


def write(glos: GlossaryType, filename: str, dicIndex=16):
	if not isinstance(dicIndex, int):
		raise TypeError(f"invalid dicIndex={dicIndex!r}, must be integer")
	with indir(filename, create=True):
		indexFp = open(str(dicIndex), "w", encoding="utf8")

		for bucketIndex, bucket in enumerate(glos.iterEntryBuckets(100)):
			lastWordIndex = bucketIndex * 100 + len(bucket) - 1
			bucketFilename = f"{dicIndex}{lastWordIndex}"

			firstWord = bucket[0].getWord()
			lastWord = bucket[-1].getWord()
			indexFp.write(f"{firstWord}#{lastWord}#{bucketFilename}\n")

			bucketFileObj = open(bucketFilename, "w", encoding="utf8")
			for entry in bucket:
				word = entry.getWord()
				defi = entry.getDefi()
				defi = defi.replace("\n", "  ")  # FIXME
				bucketFileObj.write(f"{word}#{defi}\n")
			bucketFileObj.close()

		indexFp.close()
