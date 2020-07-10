# -*- coding: utf-8 -*-
# The MIT License (MIT)

# Copyright © 2020 Saeed Rasooli <saeed.gnu@gmail.com>

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

enable = True
format = "Dictfile"
description = "Kobo E-Reader Dictfile"
extensions = (".df",)
# https://github.com/geek1011/dictutil
tools = [
	{
		"name": "dictgen",
		"web": "https://pgaskin.net/dictutil/dictgen/",
		"platforms": ["Linux", "Windows", "Mac"],
		"license": "MIT",
	},
]


def fixWord(word: str) -> str:
	return word.replace("\n", " ")


def write(
	glos,
	filename,
):
	fp = open(filename, "w", encoding="utf-8")
	# dictgen's ParseDictFile does not seem to support glossary info / metedata
	for entry in glos:
		if entry.isData():
			continue
		words = entry.words
		defi = entry.defi
		fp.write(f"@ {fixWord(words[0])}\n")
		for alt in words[1:]:
			fp.write(f"& {fixWord(alt)}\n")
		fp.write(f"{defi}\n\n")
	fp.close()
