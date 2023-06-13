# -*- coding: utf-8 -*-
# dsl/__init__.py
# Read ABBYY Lingvo DSL dictionary format
#
# Copyright © 2013-2020 Saeed Rasooli <saeed.gnu@gmail.com>
# Copyright © 2016 Ratijas <ratijas.t@me.com>
# Copyright © 2013 Xiaoqiang Wang <xiaoqiangwang AT gmail DOT com>
#
# This program is a free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# You can get a copy of GNU General Public License along this program
# But you can always get it from http://www.gnu.org/licenses/gpl.txt
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

import html
import html.entities
import re
import typing
from typing import Iterator
from xml.sax.saxutils import escape, quoteattr

from pyglossary.compression import (
	compressionOpen,
	stdCompressions,
)
from pyglossary.core import log
from pyglossary.glossary_types import EntryType, GlossaryType
from pyglossary.option import (
	BoolOption,
	EncodingOption,
	Option,
	StrOption,
)
from pyglossary.text_reader import TextFilePosWrapper

from .main import (
	DSLParser,
)

enable = True
lname = "dsl"
format = "ABBYYLingvoDSL"
description = "ABBYY Lingvo DSL (.dsl)"
extensions = (".dsl",)
extensionCreate = ".dsl"
singleFile = True
kind = "text"
wiki = "https://ru.wikipedia.org/wiki/ABBYY_Lingvo"
website = (
	"https://www.lingvo.ru/",
	"www.lingvo.ru",
)
optionsProp: "dict[str, Option]" = {
	"encoding": EncodingOption(),
	"audio": BoolOption(
		comment="Enable audio objects",
	),
	"only_fix_markup": BoolOption(
		comment="Only fix markup, without tag conversion",
	),
	"example_color": StrOption(
		comment="Examples color",
	),
}

# ABBYY is a Russian company
# https://ru.wikipedia.org/wiki/ABBYY_Lingvo
# http://lingvo.helpmax.net/en/troubleshooting/dsl-compiler/compiling-a-dictionary/
# https://www.abbyy.com/news/abbyy-lingvo-80-dictionaries-to-suit-every-taste/


# {{{
# modified to work around codepoints that are not supported by `unichr`.
# http://effbot.org/zone/re-sub.htm#unescape-html
# January 15, 2003 | Fredrik Lundh


# Removes HTML or XML character references and entities from a text string.
#
# @param text The HTML (or XML) source text.
# @return The plain text, as a Unicode string, if necessary.

htmlEntityPattern = re.compile(r"&#?\w+;")


def unescape(text: str) -> str:
	def fixup(m: "re.Match") -> str:
		text = m.group(0)
		if text[:2] == "&#":
			# character reference
			try:
				if text[:3] == "&#x":
					i = int(text[3:-1], 16)
				else:
					i = int(text[2:-1])
			except ValueError:
				pass
			else:
				try:
					return chr(i)
				except ValueError:
					# f"\\U{i:08x}", but no fb"..."
					return (b"\\U%08x" % i).decode("unicode-escape")
		else:
			# named entity
			try:
				text = chr(html.entities.name2codepoint[text[1:-1]])
			except KeyError:
				pass
		return text  # leave as is
	return htmlEntityPattern.sub(fixup, text)
# }}}


def make_a_href(s: str) -> str:
	return f"<a href={quoteattr(s)}>{escape(s)}</a>"


def ref_sub(m: "re.Match") -> str:
	return make_a_href(unescape(m.group(1)))


# order matters, a lot.
shortcuts = [
	# canonical: m > * > ex > i > c
	(
		"[m1](?:-{2,})",
		"<hr/>",
	),
	(
		"[m(\\d)](?:-{2,})",
		"<hr style=\"padding-left:\\g<1>em\"/>",
	),
]

shortcuts = [
	(
		re.compile(repl.replace("[", "\\[").replace("*]", "\\*]")),
		sub,
	) for (repl, sub) in shortcuts
]


# precompiled regexs
re_brackets_blocks = re.compile(r"\{[^}]*\}")
re_double_brackets_blocks = re.compile(r"\{\{[^}]*\}\}")
re_lang_open = re.compile(r"(?<!\\)\[lang[^\]]*\]")
re_m_open = re.compile(r"(?<!\\)\[m\d?\]")
re_c_open_color = re.compile(r"\[c (\w+)\]")
re_sound = re.compile(r"\[s\]([^\[]*?)(wav|mp3)\s*\[/s\]")
re_img = re.compile(r"\[s\]([^\[]*?)(jpg|jpeg|gif|tif|tiff|png|bmp)\s*\[/s\]")
re_m = re.compile(r"\[m(\d)\](.*?)")
re_wrapped_in_quotes = re.compile("^(\\'|\")(.*)(\\1)$")
re_end = re.compile(r"\\$")
re_ref_tag = re.compile(r"\[ref(?: [^\[\]]*)?\]([^[]*)")
re_ref = re.compile("<<(.*?)>>")
# re_ref = re.compile("<<(?<!\\<<)(.*?)>>(?<!\\>>)")
# or maybe "[^\\]<<([^>]*?[^\\])>>"


# single instance of parser
# it is safe as long as this script is not going multithread.
_parse = DSLParser().parse


def apply_shortcuts(line: str) -> str:
	for pattern, sub in shortcuts:
		line = pattern.sub(sub, line)
	return line


def _clean_tags(
	line: str,
	audio: bool,
	example_color: str,
	current_key: str,
) -> str:
	r"""
	[m{}] => <p style="padding-left:{}em;margin:0">
	[*]   => <span class="sec">
	[ex]  => <span class="ex"><font color="{example_color}">
	[c]   => <font color="green">
	[p]   => <i class="p"><font color="green">

	[']   => <u>
	[b]   => <b>
	[i]   => <i>
	[u]   => <u>
	[sup] => <sup>
	[sub] => <sub>

	[ref]   \
	[url]    } => <a href={}>{}</a>
	<<...>> /

	[s] =>  <object type="audio/x-wav" data="{}" width="40" height="40">
				<param name="autoplay" value="false" />
			</object>
	[s] =>  <img align="top" src="{}" alt="{}" />

	[t] => <font face="Helvetica" class="dsl_t">

	{{...}}   \
	[trn]      |
	[!trn]     |
	[trs]      } => remove
	[!trs]     |
	[lang ...] |
	[com]     /
	"""

	# substitute ~ with main key of the article (except for escaped tilda \~)
	line = re.sub(r"(?<!\\)~", current_key, string=line)
	line = line.replace(r"\~", "~")

	# unescape escaped special characters
	line = line.replace(r"\@", "@")
	line = line.replace(r"\ ", "&nbsp;")

	# remove {{...}} blocks
	line = re_double_brackets_blocks.sub("", line)
	# remove trn tags
	# re_trn = re.compile("\[\/?!?tr[ns]\]")
	line = line \
		.replace("[trn]", "") \
		.replace("[/trn]", "") \
		.replace("[trs]", "") \
		.replace("[/trs]", "") \
		.replace("[!trn]", "") \
		.replace("[/!trn]", "") \
		.replace("[!trs]", "") \
		.replace("[/!trs]", "")

	# remove lang tags
	line = re_lang_open.sub("", line).replace("[/lang]", "")
	# remove com tags
	line = line.replace("[com]", "").replace("[/com]", "")

	# escape html special characters like '<' and '>'
	line = html.escape(html.unescape(line))

	# remove t tags
	line = line.replace(
		"[t]",
		"<font face=\"Helvetica\" class=\"dsl_t\">",
	)
	line = line.replace("[/t]", "</font>")

	line = _parse(line)

	# cross-reference
	line = re_ref_tag.sub(ref_sub, line).replace("[/ref]", "")
	line = line.replace("[url]", "<<").replace("[/url]", ">>")
	line = line.replace("&lt;&lt;", "<<").replace("&gt;&gt;", ">>")
	line = re_ref.sub(ref_sub, line)

	line = re_end.sub("<br/>", line)

	# paragraph, part one: before shortcuts.
	if not re_m_open.search(line):
		line = "[m0]" + line
	line = line.replace("[m]", "[m1]")
	line = line.replace("[m0]", '<p style="margin:0.3em">')
	# if line somewhere contains "[m_]" tag like
	# "[b]I[/b][m1] [c][i]conj.[/i][/c][/m][m1]1) ...[/m]"
	# then leave it alone.  only wrap in "[m1]" when no "m" tag found at all.

	line = apply_shortcuts(line)

	# paragraph, part two: if any not shourcuted [m] left?
	line = re_m.sub(
		r'<p style="padding-left:\g<1>em;margin:0">\g<2>',
		line,
	)
	line = line.replace("[/m]", "")

	# text formats

	line = line.replace("[&#x27;]", '<u class="accent">').replace("[/&#x27;]", "</u>")
	line = line.replace("[b]", "<b>").replace("[/b]", "</b>")
	line = line.replace("[i]", "<i>").replace("[/i]", "</i>")
	line = line.replace("[u]", "<u>").replace("[/u]", "</u>")
	line = line.replace("[sup]", "<sup>").replace("[/sup]", "</sup>")
	line = line.replace("[sub]", "<sub>").replace("[/sub]", "</sub>")

	# color
	line = line.replace("[c]", "<font color=\"green\">")
	line = re_c_open_color.sub("<font color=\"\\g<1>\">", line)
	line = line.replace("[/c]", "</font>")

	# example zone
	line = line.replace(
		"[ex]",
		f"<span class=\"ex\"><font color=\"{example_color}\">",
	)
	line = line.replace("[/ex]", "</font></span>")

	# secondary zone
	line = line.replace("[*]", "<span class=\"sec\">")\
		.replace("[/*]", "</span>")

	# abbrev. label
	line = line.replace("[p]", "<i class=\"p\"><font color=\"green\">")
	line = line.replace("[/p]", "</font></i>")

	# sound file
	if audio:
		sound_tag = (
			r'<object type="audio/x-wav" data="\g<1>\g<2>" '
			"width=\"40\" height=\"40\">"
			"<param name=\"autoplay\" value=\"false\" />"
			"</object>"
		)
	else:
		sound_tag = ""
	line = re_sound.sub(sound_tag, line)

	# image file
	line = re_img.sub(
		r'<img align="top" src="\g<1>\g<2>" alt="\g<1>\g<2>" />',
		line,
	)

	# \[...\]
	# \{...\}
	return line.replace("\\[", "[").replace("\\]", "]")\
		.replace("\\{", "{").replace("\\}", "}")


def unwrap_quotes(s: str) -> str:
	return re_wrapped_in_quotes.sub("\\2", s)


class Reader(object):
	compressions = stdCompressions + ("dz",)

	_encoding: str = ""
	_audio: bool = False
	_only_fix_markup: bool = False
	_example_color: str = "steelblue"

	re_tags_open = re.compile(r"(?<!\\)\[(c |[cuib]\])")
	re_tags_close = re.compile(r"\[/[cuib]\]")

	def __init__(self: "typing.Self", glos: GlossaryType) -> None:
		self._glos = glos
		self.clean_tags = _clean_tags
		self._file = None
		self._fileSize = 0
		self._bufferLine = ""

	def close(self: "typing.Self") -> None:
		if self._file:
			self._file.close()
		self._file = None

	def __len__(self: "typing.Self") -> int:
		# FIXME
		return 0

	def _clean_tags_only_markup(self: "typing.Self", line: str, audio: bool) -> str:
		return _parse(line)

	def open(
		self: "typing.Self",
		filename: str,
	) -> None:
		self._filename = filename
		if self._only_fix_markup:
			self.clean_tags = self._clean_tags_only_markup
		else:
			self.clean_tags = _clean_tags

		encoding = self._encoding
		if not encoding:
			encoding = self.detectEncoding()
		cfile = compressionOpen(
			filename,
			dz=True,
			mode="rt",
			encoding=encoding,
		)

		if cfile.seekable():
			cfile.seek(0, 2)
			self._fileSize = cfile.tell()
			cfile.seek(0)
			# self._glos.setInfo("input_file_size", f"{self._fileSize}")
		else:
			log.warning("DSL Reader: file is not seekable")

		self._file = TextFilePosWrapper(cfile, encoding)

		# read header
		for line in self._file:
			line = line.rstrip().lstrip('\ufeff')  # noqa: B005
			# \ufeff -> https://github.com/ilius/pyglossary/issues/306
			if not line:
				continue
			if not line.startswith("#"):
				self._bufferLine = line
				break
			self.processHeaderLine(line)

	def detectEncoding(self: "typing.Self") -> str:
		for testEncoding in ("utf-8", "utf-16"):
			with compressionOpen(
				self._filename,
				dz=True,
				mode="rt",
				encoding=testEncoding,
			) as fileObj:
				try:
					for _ in range(10):
						fileObj.readline()
				except UnicodeDecodeError:
					log.info(f"Encoding of DSL file is not {testEncoding}")
					continue
				else:
					log.info(f"Encoding of DSL file detected: {testEncoding}")
					return testEncoding
		raise ValueError(
			"Could not detect encoding of DSL file"
			", specify it by: --read-options encoding=ENCODING",
		)

	def setInfo(self: "typing.Self", key: str, value: str) -> None:
		self._glos.setInfo(key, unwrap_quotes(value))

	def processHeaderLine(self: "typing.Self", line: str) -> None:
		if line.startswith("#NAME"):
			self.setInfo("name", unwrap_quotes(line[6:].strip()))
		elif line.startswith("#INDEX_LANGUAGE"):
			self._glos.sourceLangName = unwrap_quotes(line[16:].strip())
		elif line.startswith("#CONTENTS_LANGUAGE"):
			self._glos.targetLangName = unwrap_quotes(line[19:].strip())

	def _iterLines(self: "typing.Self") -> "Iterator[str]":
		if self._bufferLine:
			line = self._bufferLine
			self._bufferLine = ""
			yield line
		for line in self._file:
			yield line

	def sub_title_line(self, m) -> str:
		line = m.group(0)[1:-1]
		line = line.replace("[']", "") # FIXME
		line = line.replace("[/']", "")
		return line  # noqa: RET504

	def fix_title_line(self, line: str) -> str:
		# find {...} and apply acute accents
		return re_brackets_blocks.sub(self.sub_title_line, line)

	def __iter__(self: "typing.Self") -> "Iterator[EntryType]":
		current_key = ""
		current_key_alters = []
		current_text = []
		line_type = "header"
		unfinished_line = ""
		re_tags_open = self.re_tags_open
		re_tags_close = self.re_tags_close

		for line in self._iterLines():
			line = line.rstrip()
			if not line:
				continue

			# texts
			if line.startswith((" ", "\t")):
				line_type = "text"
				line = unfinished_line + line.lstrip()

				# some ill formatted source may have tags spanned into
				# multiple lines
				# try to match opening and closing tags
				tags_open = re_tags_open.findall(line)
				tags_close = re_tags_close.findall(line)
				if len(tags_open) != len(tags_close):
					unfinished_line = line
					continue

				unfinished_line = ""
				# convert DSL tags to HTML tags
				line = self.clean_tags(
					line=line,
					audio=self._audio,
					example_color=self._example_color,
					current_key=current_key,
				)
				current_text.append(line)
				continue

			# title word(s)
			# alternative titles
			if line_type == "title":
				line = self.fix_title_line(line)
				current_key_alters.append(line)
				continue

			# previous line type is text -> start new title
			# append previous entry
			if line_type == "text":
				if unfinished_line:
					# line may be skipped if ill formatted
					current_text.append(self.clean_tags(
						line=unfinished_line,
						audio=self._audio,
						example_color=self._example_color,
					))
				yield self._glos.newEntry(
					[current_key] + current_key_alters,
					"\n".join(current_text),
					byteProgress=(
						(self._file.tell(), self._fileSize)
						if self._fileSize
						else None
					),
				)

			line = self.fix_title_line(line)
			current_key_alters.append(line)

			# start new entry
			current_key = line
			current_key_alters = []
			current_text = []
			unfinished_line = ""
			line_type = "title"

		# last entry
		if line_type == "text":
			yield self._glos.newEntry(
				[current_key] + current_key_alters,
				"\n".join(current_text),
			)
