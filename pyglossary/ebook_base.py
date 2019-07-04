# -*- coding: utf-8 -*-
# The MIT License (MIT)

# Copyright (C) 2012-2016 Alberto Pettarin (alberto@albertopettarin.it)
# Copyright (C) 2016 Saeed Rasooli <saeed.gnu@gmail.com>

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import logging
log = logging.getLogger("root")


from itertools import groupby
import os
from os.path import join
import zipfile
import tempfile
from datetime import datetime
import shutil

from pyglossary.text_utils import toStr, toBytes
from pyglossary.os_utils import indir


def get_prefix(word, length):
	"""
	Return the prefix for the given word,
	of length length.

	:param word: the word string
	:type  word: unicode
	:param length: prefix length
	:type  length: int
	:rtype: unicode
	"""
	if not word:
		return None
	word = toStr(word)
	if "Z" < word[0] < "a":
		return "SPECIAL"
	return word[:length] ## return a unicode? FIXME


class EbookWriter(object):
	"""
	A class representing a generic ebook containing a dictionary.

	It can be used to output a MOBI or an EPUB 2 container.

	The ebook must have an OPF, and one or more group XHTML files.

	Optionally, it can have a cover image, an NCX TOC, an index XHTML file.

	The actual file templates are provided by the caller.
	"""
	ebook_format = ""

	CSS_CONTENTS = ""
	GROUP_XHTML_TEMPLATE = ""
	GROUP_XHTML_INDEX_LINK = ""
	
	GROUP_XHTML_WORD_TEMPLATE = ""
	GROUP_XHTML_WORD_JOINER = ""
	GROUP_XHTML_WORD_DEFINITION_TEMPLATE = ""
	GROUP_XHTML_WORD_DEFINITION_JOINER = "\n"
	
	MIMETYPE_CONTENTS = ""
	CONTAINER_XML_CONTENTS = ""
	
	GROUP_START_INDEX = 2

	COVER_TEMPLATE = "{cover}"

	INDEX_XHTML_TEMPLATE = """<?xml version="1.0" encoding="utf-8" standalone="no"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
 <head>
  <title>{title}</title>
  <link rel="stylesheet" type="text/css" href="style.css" />
 </head>
 <body class="indexPage">
  <h1 class="indexTitle">{indexTitle}</h1>
  <p class="indexGroupss">
{links}
  </p>
 </body>
</html>"""
	INDEX_XHTML_LINK_TEMPLATE = "   <span class=\"indexGroup\"><a href=\"{ref}\">{label}</a></span>"

	INDEX_XHTML_LINK_JOINER = " &#8226;\n"


	OPF_MANIFEST_ITEM_TEMPLATE = "  <item href=\"{ref}\" id=\"{id}\" media-type=\"{mediaType}\" />"

	OPF_SPINE_ITEMREF_TEMPLATE = "  <itemref idref=\"{id}\" />"


	def get_opf_contents(self, manifest_contents, spine_contents):
		raise NotImplementedError

	def __init__(
		self,
		glos,
		escape_strings=False,
		ignore_synonyms=False,
		flatten_synonyms=False,
	):
		self.glos = glos

		self._escape_strings = escape_strings
		self._ignore_synonyms = ignore_synonyms
		self._flatten_synonyms = flatten_synonyms

		#"bookeen_collation_function": None,## bookeen format
		#"bookeen_install_file": False,## bookeen format
		#"marisa_bin_path": None,## kobo format
		#"marisa_index_size": 1000000,## kobo format
		#"sd_ignore_sametypesequence": False,## stardict format
		#"sd_no_dictzip": False,## stardict format
		
		#"group_by_prefix_merge_across_first": False,
		#"group_by_prefix_merge_min_size": 0,

		self.tmpDir = None
		self.cover = None
		self.files = []
		self.manifest_files = []
		self.groups = []

	def close(self):
		pass

	myOpen = lambda self, fname, mode: open(join(self.tmpDir, fname), mode)

	def add_file(self, relative_path, contents, mode=None):
		if mode is None:
			mode = zipfile.ZIP_DEFLATED
		file_path = os.path.join(self.tmpDir, relative_path)
		file_obj = self.myOpen(file_path, "wb")
		contents = toBytes(contents)
		file_obj.write(contents)
		file_obj.close()
		self.files.append({
			"path": relative_path,
			"mode": mode,
		})

	def write_cover(self, cover_path):
		basename = os.path.basename(cover_path)
		cover_obj = self.myOpen(cover_path, "rb")
		cover = cover_obj.read()
		cover_obj.close()
		b = basename.lower()
		mimetype = "image/jpeg"
		if b.endswith(".png"):
			mimetype = "image/png"
		elif b.endswith(".gif"):
			mimetype = "image/gif"
		self.add_file_manifest("OEBPS/%s" % basename, basename, cover, mimetype)
		self.cover = basename

	def write_css(self, custom_css_path_absolute):
		css = self.CSS_CONTENTS
		if custom_css_path_absolute is not None:
			try:
				css_obj = self.myOpen(custom_css_path_absolute, "rb")
				css = css_obj.read()
				css_obj.close()
			except:
				pass
		self.add_file_manifest("OEBPS/style.css", "style.css", css, "text/css")

	def add_file_manifest(self, relative_path, id, contents, mimetype):
		self.add_file(relative_path, contents)
		self.manifest_files.append({
			"path": relative_path,
			"id": id, "mimetype": mimetype,
		})

	def get_group_xhtml_file_name_from_index(self, index):
		if index < self.GROUP_START_INDEX:
		## or index >= len(self.groups) + self.GROUP_START_INDEX:
		## number of groups are not known## FIXME
		## so we can not say if the current group is the last or not
			return "#groupPage"
		return "g%06d.xhtml" % index

	def add_group(self, key, entries):
		self.groups.append({"key": key, "entries": entries})

	def write_groups(self, group_by_prefix_length, include_index_page):
		# TODO: rtl=False option
		# TODO: handle alternates better (now shows word1|word2... in title)

		group_labels = []
		
		self.glos.sortWords()
		for group_i, (group_prefix, group_entry_iter) in enumerate(groupby(
			self.glos,
			lambda tmpEntry: get_prefix(
				tmpEntry.getWord(),
				group_by_prefix_length,
			),
		)):
			index = group_i + self.GROUP_START_INDEX
			first_word = ""
			last_word = ""
			group_contents = []
			for entry in group_entry_iter:
				if entry.isData():
					continue
				word = entry.getWord()
				defi = entry.getDefi()
				if not first_word:
					first_word = word
				last_word = word
				group_contents.append(self.GROUP_XHTML_WORD_DEFINITION_TEMPLATE.format(
					headword=self.escape_if_needed(word),
					definition=self.escape_if_needed(defi),
				))

			group_label = group_prefix
			if group_prefix != "SPECIAL":
				group_label = "%s&#8211;%s" % (first_word, last_word)
			group_labels.append(group_label)

			previous_link = self.get_group_xhtml_file_name_from_index(index - 1)
			next_link = self.get_group_xhtml_file_name_from_index(index + 1)

			group_contents = self.GROUP_XHTML_WORD_DEFINITION_JOINER.join(group_contents)
			group_contents = self.GROUP_XHTML_TEMPLATE.format(
				title=group_label,
				group_title=group_label,
				previous_link=previous_link,
				index_link=self.GROUP_XHTML_INDEX_LINK if include_index_page else "",
				next_link=next_link,
				group_contents=group_contents,
			)
			
			group_xhtml_path = self.get_group_xhtml_file_name_from_index(index)

			self.add_file_manifest(
				"OEBPS/%s" % group_xhtml_path,
				group_xhtml_path,
				group_contents,
				"application/xhtml+xml",
			)
		
		return group_labels

	def escape_if_needed(self, string):
		if self._escape_strings:
			string = string.replace("&", "&amp;")\
				.replace('"', "&quot;")\
				.replace("'", "&apos;")\
				.replace(">", "&gt;")\
				.replace("<", "&lt;")
		return string


	def write_index(self, group_labels):
		"""
			group_labels: a list of labels
		"""
		links = []
		for label_i, label in enumerate(group_labels):
			links.append(self.INDEX_XHTML_LINK_TEMPLATE.format(
				ref = self.get_group_xhtml_file_name_from_index(
					self.GROUP_START_INDEX + label_i
				),
				label = label,
			))
		links = self.INDEX_XHTML_LINK_JOINER.join(links)
		title = self.glos.getInfo("title")
		contents = self.INDEX_XHTML_TEMPLATE.format(
			title = title,
			indexTitle = title,
			links = links,
		)
		self.add_file_manifest(
			"OEBPS/index.xhtml",
			"index.xhtml",
			contents,
			"application/xhtml+xml",
		)

	def get_opf_contents(self, manifest_contents, spine_contents):
		cover = ""
		if self.cover:
			cover = self.COVER_TEMPLATE.format(cover=self.cover)

		creationDate = datetime.now().strftime("%Y-%m-%d")
		
		return self.OPF_TEMPLATE.format(
			identifier = self.glos.getInfo("uuid"),
			sourceLang = self.glos.getInfo("sourceLang"),
			targetLang = self.glos.getInfo("sourceLang"),
			title = self.glos.getInfo("title"),
			creator = self.glos.getInfo("author"),
			copyright = self.glos.getInfo("copyright"),
			creationDate = creationDate,
			cover = cover,
			manifest = manifest_contents,
			spine = spine_contents,
		)

	def write_opf(self):
		manifest_lines = []
		spine_lines = []
		for mi in self.manifest_files:
			manifest_lines.append(self.OPF_MANIFEST_ITEM_TEMPLATE.format(
				ref=mi["id"],
				id=mi["id"],
				mediaType=mi["mimetype"]
			))
			if mi["mimetype"] == "application/xhtml+xml":
				spine_lines.append(self.OPF_SPINE_ITEMREF_TEMPLATE.format(
					id=mi["id"],
				))

		manifest_contents = "\n".join(manifest_lines)
		spine_contents = "\n".join(spine_lines)
		opf_contents = self.get_opf_contents(
			manifest_contents,
			spine_contents,
		)

		self.add_file("OEBPS/content.opf", opf_contents)

	def write_ncx(self, group_labels, include_index_page):
		"""
			write_ncx
			only for epub
		"""
		pass

	def write(
		self,
		filename,
		keep=False,
		group_by_prefix_length=2,
		include_index_page=False,
		compress=True,
		apply_css="", # path to css file, or ""
		cover_path="", # path to cover file, or ""
	):
		self.tmpDir = tempfile.mkdtemp()
		with indir(self.tmpDir):
			if cover_path:
				cover_path = os.path.abspath(cover_path)

			if apply_css:
				apply_css = os.path.abspath(apply_css)

			os.makedirs("META-INF")
			os.makedirs("OEBPS")

			if self.MIMETYPE_CONTENTS:
				self.add_file("mimetype", self.MIMETYPE_CONTENTS, mode=zipfile.ZIP_STORED)
			if self.CONTAINER_XML_CONTENTS:
				self.add_file("META-INF/container.xml", self.CONTAINER_XML_CONTENTS)

			if cover_path:
				try:
					self.write_cover(cover_path)
				except:
					log.exception("")

			self.write_css(apply_css)

			group_labels = self.write_groups(
				group_by_prefix_length,
				include_index_page,
			)

			if include_index_page:
				self.write_index()

			self.write_ncx(group_labels, include_index_page)

			self.write_opf()

			if compress:
				zipFp = zipfile.ZipFile(
					filename,
					"w",
					compression=zipfile.ZIP_DEFLATED,
				)
				for fileDict in self.files:
					zipFp.write(
						fileDict["path"],
						compress_type=fileDict["mode"],
					)
				zipFp.close()
				if not keep:
					shutil.rmtree(self.tmpDir)
			else:
				if keep:
					shutil.copytree(self.tmpDir, filename)
				else:
					shutil.move(self.tmpDir, filename)




