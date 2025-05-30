# -*- coding: utf-8 -*-
#
# Output to Apple Dictionary xml sources for Dictionary Development Kit.
#
# Copyright © 2016-2023 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
# Copyright © 2016 ivan tkachenko <me@ratijas.tk>
# Copyright © 2012-2015 Xiaoqiang Wang <xiaoqiangwang AT gmail DOT com>
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

from __future__ import annotations

import os
import pkgutil
import shutil
import sys
from os.path import basename, isdir, join
from typing import TYPE_CHECKING, Any

from pyglossary.core import log, pip
from pyglossary.text_utils import toStr

from ._content import prepare_content
from ._dict import (
	id_generator,
	indexes_generator,
	quote_string,
)
from ._normalize import title as normalize_title
from ._normalize import title_long as normalize_title_long

if TYPE_CHECKING:
	import io
	from collections.abc import Generator

	from pyglossary.glossary_types import EntryType, WriterGlossaryType

__all__ = ["Writer"]

sys.setrecursionlimit(10000)


BeautifulSoup = None


def _loadBeautifulSoup() -> None:
	global BeautifulSoup
	try:
		import bs4 as BeautifulSoup
	except ImportError:
		try:
			import BeautifulSoup  # type: ignore
		except ImportError:
			return
	version: str = BeautifulSoup.__version__  # type: ignore
	if int(version.split(".", maxsplit=1)[0]) < 4:
		raise ImportError(
			"BeautifulSoup is too old, required at least version 4, "
			f"{version!r} found.\n"
			f"Please run `{pip} install lxml beautifulsoup4 html5lib`",
		)


def _abspath_or_None(path: str | None) -> str | None:
	if not path:
		return None
	return os.path.abspath(os.path.expanduser(path))


def _write_header(
	toFile: io.TextIOBase,
	front_back_matter: str | None,
) -> None:
	# write header
	toFile.write(
		'<?xml version="1.0" encoding="UTF-8"?>\n'
		'<d:dictionary xmlns="http://www.w3.org/1999/xhtml" '
		'xmlns:d="http://www.apple.com/DTDs/DictionaryService-1.0.rng">\n',
	)

	if front_back_matter:
		with open(
			front_back_matter,
			encoding="utf-8",
		) as _file:
			toFile.write(_file.read())


def _format_default_prefs(default_prefs: dict[str, Any] | None) -> str:
	"""
	:type default_prefs: dict or None

	as by 14th of Jan 2016, it is highly recommended that prefs should contain
	{"version": "1"}, otherwise Dictionary.app does not keep user changes
	between restarts.
	"""
	if not default_prefs:
		return ""
	if not isinstance(default_prefs, dict):
		raise TypeError(f"default_prefs not a dictionary: {default_prefs!r}")
	if str(default_prefs.get("version", None)) != "1":
		log.error(
			"default prefs does not contain {'version': '1'}.  prefs "
			"will not be persistent between Dictionary.app restarts.",
		)
	return "\n".join(
		f"\t\t<key>{key}</key>\n\t\t<string>{value}</string>"
		for key, value in sorted(default_prefs.items())
	).strip()


def _write_css(fname: str, css_file: str) -> None:
	with open(fname, mode="wb") as toFile:
		if css_file:
			with open(css_file, mode="rb") as fromFile:
				toFile.write(fromFile.read())
		else:
			data = pkgutil.get_data(
				__name__,
				"templates/Dictionary.css",
			)
			if data is None:
				raise RuntimeError("failed to load templates/Dictionary.css")
			toFile.write(data)


"""
write glossary to Apple dictionary .xml and supporting files.

:param dirname: directory path, must not have extension

:param clean_html: pass True to use BeautifulSoup parser.

:param css: path to custom .css file

:param xsl: path to custom XSL transformations file.

:param default_prefs: Default prefs in python dictionary literal format,
i.e. {"key1": "value1", "key2": "value2", ...}.  All keys and values
must be quoted strings; not allowed characters (e.g. single/double
quotes,equal sign "=", semicolon) must be escaped as hex code
according to python string literal rules.

:param prefs_html: path to XHTML file with user interface for
dictionary's preferences. refer to Apple's documentation for details.

:param front_back_matter: path to XML file with top-level tag
<d:entry id="front_back_matter" d:title="Your Front/Back Matter Title">
	your front/back matter entry content
</d:entry>

:param jing: pass True to run Jing check on generated XML.

# FIXME: rename to indexes_lang?
:param indexes: Dictionary.app is dummy and by default it don't know
how to perform flexible search.  we can help it by manually providing
additional indexes to dictionary entries.
"""


class Writer:
	depends = {
		"lxml": "lxml",
		"bs4": "beautifulsoup4",
		"html5lib": "html5lib",
	}

	_clean_html: bool = True
	_css: str = ""
	_xsl: str = ""
	_default_prefs: dict | None = None
	_prefs_html: str = ""
	_front_back_matter: str = ""
	_jing: bool = False
	_indexes: str = ""  # FIXME: rename to indexes_lang?

	def __init__(self, glos: WriterGlossaryType) -> None:
		self._glos = glos
		self._dirname = ""

	def finish(self) -> None:
		self._dirname = ""

	def open(self, dirname: str) -> None:
		self._dirname = dirname
		if not isdir(dirname):
			os.mkdir(dirname)

	# TODO: PLR0915 Too many statements (74 > 50)
	def write(self) -> Generator[None, EntryType, None]:  # noqa: PLR0912, PLR0915
		global BeautifulSoup
		from pyglossary.xdxf.transform import XdxfTransformer

		glos = self._glos
		clean_html = self._clean_html
		css: str | None = self._css
		xsl: str | None = self._xsl
		default_prefs = self._default_prefs
		prefs_html: str | None = self._prefs_html
		front_back_matter: str | None = self._front_back_matter
		jing = self._jing
		indexes = self._indexes

		xdxf_to_html = XdxfTransformer(encoding="utf-8")

		if clean_html:
			if BeautifulSoup is None:
				_loadBeautifulSoup()
			if BeautifulSoup is None:
				log.warning(
					"clean_html option passed but BeautifulSoup not found. "
					"to fix this run "
					f"`{pip} install lxml beautifulsoup4 html5lib`",
				)
		else:
			BeautifulSoup = None

		dirname = self._dirname
		fileNameBase = basename(dirname).replace(".", "_")
		filePathBase = join(dirname, fileNameBase)
		# before chdir (outside indir block)
		css = _abspath_or_None(css)
		xsl = _abspath_or_None(xsl)
		prefs_html = _abspath_or_None(prefs_html)
		front_back_matter = _abspath_or_None(front_back_matter)

		generate_id = id_generator()
		generate_indexes = indexes_generator(indexes)

		myResDir = join(dirname, "OtherResources")
		if not isdir(myResDir):
			os.mkdir(myResDir)

		with open(filePathBase + ".xml", mode="w", encoding="utf-8") as toFile:
			_write_header(toFile, front_back_matter)
			while True:
				entry = yield
				if entry is None:
					break
				if entry.isData():
					entry.save(myResDir)
					continue

				words = entry.l_word
				word, alts = words[0], words[1:]
				defi = entry.defi

				long_title = normalize_title_long(
					normalize_title(word, BeautifulSoup),
				)
				if not long_title:
					continue

				id_ = next(generate_id)
				quoted_title = quote_string(long_title, BeautifulSoup)

				content_title: str | None = long_title
				if entry.defiFormat == "x":
					defi = xdxf_to_html.transformByInnerString(defi)
					content_title = None
				content = prepare_content(content_title, defi, BeautifulSoup)

				toFile.write(
					f'<d:entry id="{id_}" d:title={quoted_title}>\n'
					+ generate_indexes(long_title, alts, content, BeautifulSoup)
					+ content
					+ "\n</d:entry>\n",
				)

			toFile.write("</d:dictionary>\n")

		if xsl:
			shutil.copy(xsl, myResDir)

		if prefs_html:
			shutil.copy(prefs_html, myResDir)

		_write_css(filePathBase + ".css", css)

		with open(join(dirname, "Makefile"), mode="w", encoding="utf-8") as toFile:
			toFile.write(
				toStr(
					pkgutil.get_data(
						__name__,
						"templates/Makefile",
					),
				).format(dict_name=fileNameBase),
			)

		copyright_ = glos.getInfo("copyright")
		if BeautifulSoup:
			# strip html tags
			copyright_ = str(
				BeautifulSoup.BeautifulSoup(
					copyright_,
					features="lxml",
				).text,
			)

		# if DCSDictionaryXSL provided but DCSDictionaryDefaultPrefs <dict/> not
		# present in Info.plist, Dictionary.app will crash.
		with open(filePathBase + ".plist", mode="w", encoding="utf-8") as toFile:
			frontMatterReferenceID = (
				"<key>DCSDictionaryFrontMatterReferenceID</key>\n"
				"\t<string>front_back_matter</string>"
				if front_back_matter
				else ""
			)
			bundle_id = glos.getInfo("CFBundleIdentifier")
			if not bundle_id:
				bundle_id = fileNameBase.replace(" ", "")
			toFile.write(
				toStr(
					pkgutil.get_data(
						__name__,
						"templates/Info.plist",
					),
				).format(
					# identifier must be unique
					CFBundleIdentifier=bundle_id,
					CFBundleDisplayName=glos.getInfo("name"),
					CFBundleName=fileNameBase,
					DCSDictionaryCopyright=copyright_,
					DCSDictionaryManufacturerName=glos.author,
					DCSDictionaryXSL=basename(xsl) if xsl else "",
					DCSDictionaryDefaultPrefs=_format_default_prefs(default_prefs),
					DCSDictionaryPrefsHTML=basename(prefs_html) if prefs_html else "",
					DCSDictionaryFrontMatterReferenceID=frontMatterReferenceID,
				),
			)

		if jing:
			from .jing import run as jing_run

			jing_run(filePathBase + ".xml")
