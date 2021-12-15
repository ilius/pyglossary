# -*- coding: utf-8 -*-
# The MIT License (MIT)

# Copyright © 2012-2016 Alberto Pettarin (alberto@albertopettarin.it)
# Copyright © 2016-2020 Saeed Rasooli <saeed.gnu@gmail.com>

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

from formats_common import *
from pyglossary.ebook_base import *
from pyglossary.langs import Lang

enable = True
lname = "mobi"
format = "Mobi"
description = "Mobipocket (.mobi) E-Book"
extensions = (".mobi",)
extensionCreate = ".mobi"
sortOnWrite = DEFAULT_YES
kind = "package"
wiki = "https://en.wikipedia.org/wiki/Mobipocket"
website = None

optionsProp = {
	"group_by_prefix_length": IntOption(
		comment="Prefix length for grouping",
	),
	# "group_by_prefix_merge_min_size": IntOption(),
	# "group_by_prefix_merge_across_first": BoolOption(),

	# specific to mobi
	"kindlegen_path": StrOption(
		comment="Path to kindlegen executable",
	),
	"compress": BoolOption(
		disabled=True,
		comment="Enable compression",
	),
	"keep": BoolOption(
		comment="Keep temp files",
	),
	"include_index_page": BoolOption(
		disabled=True,
		comment="Include index page",
	),
	"css": StrOption(
		# disabled=True,
		comment="Path to css file",
	),
	"cover_path": StrOption(
		# disabled=True,
		comment="Path to cover file",
	),
	"file_size_approx": FileSizeOption(
		comment="Approximate size of each xhtml file (example: 200kb)",
	),
	"hide_word_index": BoolOption(
		comment="Hide headword in tap-to-check interface",
	),
	"spellcheck": BoolOption(
		comment="Enable wildcard search and spell correction during word lookup",
		# "Maybe it just enables the kindlegen's spellcheck."
	),
	"exact": BoolOption(
		comment="Exact-match Parameter",
		# "I guess it only works for inflections"
	),
}

extraDocs = [
	(
		"Other Requirements",
		"Install [KindleGen](https://wiki.mobileread.com/wiki/KindleGen)"
		" for creating Mobipocket e-books."
	),
]


class GroupStateBySize(object):
	def __init__(self, writer) -> None:
		self.writer = writer
		self.group_index = -1
		self.reset()

	def reset(self) -> None:
		self.group_contents = []
		self.group_size = 0

	def add(self, entry: "BaseEntry") -> None:
		word = entry.l_word
		defi = entry.defi
		content = self.writer.format_group_content(word, defi)
		self.group_contents.append(content)
		self.group_size += len(content.encode("utf-8"))


class Writer(EbookWriter):
	_compress: bool = False
	_keep: bool = False
	_kindlegen_path: str = ""
	_file_size_approx: int = 271360
	_hide_word_index: bool = False
	_spellcheck: bool = True
	_exact: bool = False
	CSS_CONTENTS = """"@charset "UTF-8";"""
	GROUP_XHTML_TEMPLATE = """<?xml version="1.0" encoding="utf-8" \
standalone="no"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" \
"http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns:cx=\
"https://kindlegen.s3.amazonaws.com/AmazonKindlePublishingGuidelines.pdf" \
xmlns:dc="http://purl.org/dc/elements/1.1/" \
xmlns:idx="https://kindlegen.s3.amazonaws.com\
/AmazonKindlePublishingGuidelines.pdf" \
xmlns:math="http://exslt.org/math" \
xmlns:mbp="https://kindlegen.s3.amazonaws.com\
/AmazonKindlePublishingGuidelines.pdf" \
xmlns:mmc="https://kindlegen.s3.amazonaws.com\
/AmazonKindlePublishingGuidelines.pdf" \
xmlns:saxon="http://saxon.sf.net/" xmlns:svg="http://www.w3.org/2000/svg" \
xmlns:tl="https://kindlegen.s3.amazonaws.com\
/AmazonKindlePublishingGuidelines.pdf" \
xmlns:xs="http://www.w3.org/2001/XMLSchema" \
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
<head>
<meta content="text/html; charset=utf-8" http-equiv="Content-Type" />
<link href="style.css" rel="stylesheet" type="text/css" />
</head>
<body>
<mbp:frameset>
{group_contents}
</mbp:frameset>
</body>
</html>"""

	GROUP_XHTML_WORD_DEFINITION_TEMPLATE = """<idx:entry \
scriptable="yes"{spellcheck_str}>
<idx:orth{value_headword}>{headword_visible}{infl}
</idx:orth>
<br/>{definition}
</idx:entry>
<hr/>"""

	GROUP_XHTML_WORD_INFL_TEMPLATE = """<idx:infl>
{iforms_str}
</idx:infl>"""

	GROUP_XHTML_WORD_IFORM_TEMPLATE = """<idx:iform \
value="{inflword}"{exact_str} />"""

	OPF_TEMPLATE = """<?xml version="1.0" encoding="utf-8"?>
<package unique-identifier="uid">
<metadata>
<dc-metadata xmlns:dc="http://purl.org/metadata/dublin_core"
xmlns:oebpackage="http://openebook.org/namespaces/oeb-package/1.0/">
<dc:Title>{title}</dc:Title>
<dc:Language>{sourceLang}</dc:Language>
<dc:Identifier id="uid">{identifier}</dc:Identifier>
<dc:Creator>{creator}</dc:Creator>
<dc:Rights>{copyright}</dc:Rights>
<dc:description>{description}</dc:description>
<dc:Subject BASICCode="REF008000">Dictionaries</dc:Subject>
</dc-metadata>
<x-metadata>
<output encoding="utf-8"></output>
<DictionaryInLanguage>{sourceLang}</DictionaryInLanguage>
<DictionaryOutLanguage>{targetLang}</DictionaryOutLanguage>
<EmbeddedCover>{cover}</EmbeddedCover>
</x-metadata>
</metadata>
<manifest>
{manifest}
</manifest>
<spine>
{spine}
</spine>
<tours></tours>
<guide></guide>
</package>"""

	def __init__(self, glos, **kwargs):
		import uuid
		EbookWriter.__init__(
			self,
			glos,
		)
		glos.setInfo("uuid", str(uuid.uuid4()).replace("-", ""))

	def format_group_content(self, word: "List[str]", defi: str) -> str:
		hide_word_index = self._hide_word_index
		if len(word) == 1:
			infl = ''
			mainword = word[0]
		else:
			mainword, *variants = word
			iforms_list = []
			for variant in variants:
				iforms_list.append(self.GROUP_XHTML_WORD_IFORM_TEMPLATE.format(
					inflword=variant,
					exact_str=' exact="yes"' if self._exact else '',
				))
			infl = '\n' + \
				self.GROUP_XHTML_WORD_INFL_TEMPLATE.format(
					iforms_str="\n".join(iforms_list))

		headword = self.escape_if_needed(mainword)

		defi = self.escape_if_needed(defi)

		if hide_word_index:
			headword_visible = ""
			value_headword = f' value="{headword}"'
		else:
			headword_visible = "\n" + self._glos.wordTitleStr(headword)
			value_headword = ""

		group_content = self.GROUP_XHTML_WORD_DEFINITION_TEMPLATE.format(
			spellcheck_str=' spell="yes"' if self._spellcheck else "",
			headword_visible=headword_visible,
			value_headword=value_headword,
			definition=defi,
			infl=infl,
		)
		return group_content

	def getLangCode(self, lang) -> str:
		return lang.code if isinstance(lang, Lang) else ""

	def get_opf_contents(self, manifest_contents, spine_contents):
		cover = ""
		if self.cover:
			cover = self.COVER_TEMPLATE.format(cover=self.cover)
		creationDate = datetime.now().strftime("%Y-%m-%d")

		return self.OPF_TEMPLATE.format(
			identifier=self._glos.getInfo("uuid"),
			# use Language code instead name for kindlegen
			sourceLang=self.getLangCode(self._glos.sourceLang),
			targetLang=self.getLangCode(self._glos.targetLang),
			title=self._glos.getInfo("name"),
			creator=self._glos.author,
			copyright=self._glos.getInfo("copyright"),
			description=self._glos.getInfo("description"),
			creationDate=creationDate,
			cover=cover,
			manifest=manifest_contents,
			spine=spine_contents,
		)

	def write_groups(self):

		def add_group(state):
			if state.group_size <= 0:
				return
			state.group_index += 1
			index = state.group_index + self.GROUP_START_INDEX
			group_xhtml_path = self.get_group_xhtml_file_name_from_index(index)
			self.add_file_manifest(
				"OEBPS/" + group_xhtml_path,
				group_xhtml_path,
				self.GROUP_XHTML_TEMPLATE.format(
					group_contents=self.GROUP_XHTML_WORD_DEFINITION_JOINER.join(
						state.group_contents,
					),
				),
				"application/xhtml+xml",
			)

		state = GroupStateBySize(self)
		while True:
			entry = yield
			if entry is None:
				break
			if entry.isData():
				continue

			if state.group_size >= self._file_size_approx:
				add_group(state)
				state.reset()

			state.add(entry)

		add_group(state)

	def write(self):
		import subprocess

		filename = self._filename
		kindlegen_path = self._kindlegen_path

		yield from EbookWriter.write(self)

		# download kindlegen from this page:
		# https://www.amazon.com/gp/feature.html?ie=UTF8&docId=1000765211

		# run kindlegen
		if not kindlegen_path:
			log.warn(f"Not running kindlegen, the raw files are located in {filename}")
			log.warn(
				"Provide KindleGen path with: "
				"--write-options 'kindlegen_path=...'"
			)
			return

		name = self._glos.getInfo("name")

		log.info("Creating .mobi file with kindlegen, using {kindlegen_path!r}")
		opf_path_abs = join(filename, "OEBPS", "content.opf")
		proc = subprocess.Popen(
			[kindlegen_path, opf_path_abs, "-o", "content.mobi"],
			stdout=subprocess.PIPE,
			stdin=subprocess.PIPE,
			stderr=subprocess.PIPE
		)
		output = proc.communicate()
		log.info(output[0].decode("utf-8"))
		mobi_path_abs = os.path.join(filename, "OEBPS", "content.mobi")
		log.info(f"Created .mobi file with kindlegen: {mobi_path_abs}")
