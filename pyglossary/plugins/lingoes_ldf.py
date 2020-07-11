# -*- coding: utf-8 -*-

from formats_common import *
from pyglossary.text_reader import TextGlossaryReader
from pyglossary.file_utils import fileCountLines

enable = True
format = "LingoesLDF"
description = "Lingoes Source (LDF)"
extensions = (".ldf",)
singleFile = True
optionsProp = {
	"newline": NewlineOption(),
	"resources": BoolOption(),
	"encoding": EncodingOption(),
}
depends = {}

tools = [
	{
		"name": "Lingoes Dictionary Creator",
		"web": "http://www.lingoes.net/en/dictionary/dict_format.php",
		"platforms": [],
		"comment": """Lingoes Dictionary Creator is developing now.
Please send your finished dictionary source file to kevin-yau@msn.com
Lingoes will compile it into .ld2 for you.
You will can do it yourself after the creator release."""
	},
]

infoKeys = [
	"title",
	"description",
	"author",
	"email",
	"website",
	"copyright",
]


class Reader(TextGlossaryReader):
	def __len__(self):
		if self._wordCount is None:
			log.debug("Try not to use len(reader) as it takes extra time")
			self._wordCount = fileCountLines(
				self._filename,
				newline="\n\n",
			) - self._leadingLinesCount
		return self._wordCount

	def isInfoWord(self, word):
		if isinstance(word, str):
			return word.startswith("#")
		else:
			return False

	def fixInfoWord(self, word):
		if isinstance(word, str):
			return word.lstrip("#").lower()
		else:
			return word

	def nextPair(self):
		if not self._file:
			raise StopIteration
		entryLines = []
		while True:
			line = self._file.readline()
			if not line:
				raise StopIteration
			line = line.rstrip("\n\r")  # FIXME
			if line.startswith("###"):
				parts = line.split(":")
				key = parts[0].strip()
				value = ":".join(parts[1:]).strip()
				return key, value
			if line:
				entryLines.append(line)
				continue

			# now `line` is empty, process `entryLines`
			if not entryLines:
				return
			if len(entryLines) < 2:
				log.error(
					f"invalid block near line {fileObj.line}"
					f" in file {filename}"
				)
				return
			word = entryLines[0]
			defi = "\n".join(entryLines[1:])
			defi = defi.replace("<br/>", "\n")  # FIXME

			word = [p.strip() for p in word.split("|")]

			return word, defi


def write(
	glos: GlossaryType,
	filename: str,
	newline: str = "\n",
	resources: str = True,
):
	g = glos
	head = "\n".join([
		f"###{key.capitalize()}: {g.getInfo(key)}"
		for key in infoKeys
	])
	head += "\n"
	g.writeTxt(
		entryFmt="{word}\n{defi}\n\n",
		filename=filename,
		writeInfo=False,
		rplList=(
			("\n", "<br/>"),
		),
		ext=".ldf",
		head=head,
		newline=newline,
		resources=resources,
	)
