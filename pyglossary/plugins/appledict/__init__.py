# -*- coding: utf-8 -*-
# appledict/__init__.py
# Output to Apple Dictionary xml sources for Dictionary Development Kit.
#
# Copyright © 2016-2020 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
# Copyright © 2016 Ratijas <ratijas.t@me.com>
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

import sys
import os
from os.path import abspath, basename

import re
import pkgutil
import shutil

from pyglossary.plugins.formats_common import *
from pyglossary.xdxf_transform import xdxf_to_html_transformer
from ._dict import *

sys.setrecursionlimit(10000)

enable = True
format = "AppleDict"
description = "AppleDict Source"
extensions = (".apple",)
# FIXME: rename indexes arg/option to indexes_lang?
optionsProp = {
	"cleanHTML": BoolOption(comment="use BeautifulSoup parser"),
	"css": StrOption(comment="custom .css file path"),
	"xsl": StrOption(comment="custom XSL transformations file path"),
	"defaultPrefs": DictOption(
		comment='default prefs in python dict format',
		# example: {"key": "value", "version": "1"}
	),
	"prefsHTML": StrOption(comment="preferences XHTML file path"),
	"frontBackMatter": StrOption(comment="XML file path with top-level tag"),
	"jing": BoolOption(comment="run Jing check on generated XML"),
	"indexes": StrOption(customValue=False, values=["", "ru", "zh"]),
}

tools = [
	{
		"name": "Dictionary Development Kit",
		"web": "https://github.com/SebastianSzturo/Dictionary-Development-Kit",
		"platforms": ["Mac"],
		"license": "Unknown",
	},
]


BeautifulSoup = None


def loadBeautifulSoup():
	global BeautifulSoup
	try:
		import bs4 as BeautifulSoup
	except ImportError:
		try:
			import BeautifulSoup
		except ImportError:
			return
	if int(BeautifulSoup.__version__.split(".")[0]) < 4:
		raise ImportError(
			f"BeautifulSoup is too old, required at least version 4, "
			f"{BeautifulSoup.__version__!r} found.\n"
			f"Please run `{pip} install lxml beautifulsoup4 html5lib`"
		)


def abspath_or_None(path):
	return os.path.abspath(os.path.expanduser(path)) if path else None


def write_header(
	glos: "GlossaryType",
	toFile: "TextIO",
	frontBackMatter: "Optional[str]",
) -> None:
	# write header
	toFile.write(
		'<?xml version="1.0" encoding="UTF-8"?>\n'
		'<d:dictionary xmlns="http://www.w3.org/1999/xhtml" '
		'xmlns:d="http://www.apple.com/DTDs/DictionaryService-1.0.rng">\n'
	)

	if frontBackMatter:
		with open(frontBackMatter, mode="r", encoding="utf-8") as front_back_matter:
			toFile.write(front_back_matter.read())


def format_default_prefs(defaultPrefs):
	"""
	:type defaultPrefs: dict or None

	as by 14th of Jan 2016, it is highly recommended that prefs should contain
	{"version": "1"}, otherwise Dictionary.app does not keep user changes
	between restarts.
	"""
	if not defaultPrefs:
		return ""
	if not isinstance(defaultPrefs, dict):
		raise TypeError(f"defaultPrefs not a dictionary: {defaultPrefs!r}")
	if str(defaultPrefs.get("version", None)) != "1":
		log.error(
			"default prefs does not contain {'version': '1'}.  prefs "
			"will not be persistent between Dictionary.app restarts."
		)
	return "\n".join(
		f"\t\t<key>{key}</key>\n\t\t<string>{value}</string>"
		for key, value in sorted(defaultPrefs.items())
	).strip()


def write_css(fname, css_file):
	with open(fname, mode="wb") as toFile:
		if css_file:
			with open(css_file, mode="rb") as fromFile:
				toFile.write(fromFile.read())
		else:
			toFile.write(pkgutil.get_data(
				__name__,
				"templates/Dictionary.css",
			))


"""
write glossary to Apple dictionary .xml and supporting files.

:param dirname: directory path, must not have extension

:param cleanHTML: pass True to use BeautifulSoup parser.

:param css: path to custom .css file

:param xsl: path to custom XSL transformations file.

:param defaultPrefs: Default prefs in python dictionary literal format,
i.e. {"key1": "value1", "key2": "value2", ...}.  All keys and values 
must be quoted strings; not allowed characters (e.g. single/double
quotes,equal sign "=", semicolon) must be escaped as hex code
according to python string literal rules.

:param prefsHTML: path to XHTML file with user interface for
dictionary's preferences. refer to Apple's documentation for details.

:param frontBackMatter: path to XML file with top-level tag
<d:entry id="front_back_matter" d:title="Your Front/Back Matter Title">
	your front/back matter entry content
</d:entry>

:param jing: pass True to run Jing check on generated XML.

# FIXME: rename to indexes_lang?
:param indexes: Dictionary.app is dummy and by default it don't know
how to perform flexible search.  we can help it by manually providing
additional indexes to dictionary entries.
"""

class Writer(object):
	depends = {
		"lxml": "lxml",
		"bs4": "beautifulsoup4",
		"html5lib": "html5lib",
	}

	_cleanHTML: bool = True
	_css: str = ""
	_xsl: str = ""
	_defaultPrefs: "Optional[Dict]" = None
	_prefsHTML: str = ""
	_frontBackMatter: str = ""
	_jing: bool = False
	_indexes: str = ""  # FIXME: rename to indexes_lang?

	def __init__(self, glos: GlossaryType) -> None:
		self._glos = glos
		self._dirname = None

	def finish(self):
		self._dirname = None

	def open(self, dirname: str) -> None:
		self._dirname = dirname
		if not isdir(dirname):
			os.mkdir(dirname)

	def write(self) -> "Generator[None, BaseEntry, None]":
		global BeautifulSoup

		glos = self._glos
		cleanHTML = self._cleanHTML
		css = self._css
		xsl = self._xsl
		defaultPrefs = self._defaultPrefs
		prefsHTML = self._prefsHTML
		frontBackMatter = self._frontBackMatter
		jing = self._jing
		indexes = self._indexes

		xdxf_to_html = xdxf_to_html_transformer()

		if cleanHTML:
			if BeautifulSoup is None:
				loadBeautifulSoup()
			if BeautifulSoup is None:
				log.warning(
					"cleanHTML option passed but BeautifulSoup not found. "
					f"to fix this run "
					f"`{pip} install lxml beautifulsoup4 html5lib`"
				)
		else:
			BeautifulSoup = None

		dirname = self._dirname
		fileNameBase = basename(dirname).replace(".", "_")
		filePathBase = join(dirname, fileNameBase)
		# before chdir (outside indir block)
		css = abspath_or_None(css)
		xsl = abspath_or_None(xsl)
		prefsHTML = abspath_or_None(prefsHTML)
		frontBackMatter = abspath_or_None(frontBackMatter)

		generate_id = id_generator()
		generate_indexes = indexes_generator(indexes)

		myResDir = join(dirname, "OtherResources")
		if not isdir(myResDir):
			os.mkdir(myResDir)

		with open(filePathBase + ".xml", mode="w", encoding="utf-8") as toFile:
			write_header(glos, toFile, frontBackMatter)
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

				long_title = _normalize.title_long(
					_normalize.title(word, BeautifulSoup)
				)
				if not long_title:
					continue

				_id = next(generate_id)
				if BeautifulSoup:
					title_attr = BeautifulSoup.dammit.EntitySubstitution\
						.substitute_xml(long_title, True)
				else:
					title_attr = str(long_title)

				content_title = long_title
				if entry.defiFormat == "x":
					defi = xdxf_to_html(defi)
					content_title = None
				content = prepare_content(content_title, defi, BeautifulSoup)

				toFile.write(
					f'<d:entry id="{_id}" d:title={title_attr}>\n' +
					generate_indexes(long_title, alts, content, BeautifulSoup) +
					content +
					"\n</d:entry>\n"
				)

			toFile.write("</d:dictionary>\n")

		if xsl:
			shutil.copy(xsl, myResDir)

		if prefsHTML:
			shutil.copy(prefsHTML, myResDir)

		write_css(filePathBase + ".css", css)

		with open(join(dirname, "Makefile"), mode="w", encoding="utf-8") as toFile:
			toFile.write(
				toStr(pkgutil.get_data(
					__name__,
					"templates/Makefile",
				)).format(dict_name=fileNameBase)
			)

		copyright = glos.getInfo("copyright")
		if BeautifulSoup:
			# strip html tags
			copyright = str(BeautifulSoup.BeautifulSoup(
				copyright,
				features="lxml"
			).text)

		# if DCSDictionaryXSL provided but DCSDictionaryDefaultPrefs <dict/> not
		# present in Info.plist, Dictionary.app will crash.
		with open(filePathBase + ".plist", mode="w", encoding="utf-8") as toFile:
			frontMatterReferenceID = (
				"<key>DCSDictionaryFrontMatterReferenceID</key>\n"
				"\t<string>front_back_matter</string>"
				if frontBackMatter
				else ""
			)
			toFile.write(
				toStr(pkgutil.get_data(
					__name__,
					"templates/Info.plist",
				)).format(
					# identifier must be unique
					CFBundleIdentifier=fileNameBase.replace(" ", ""),
					CFBundleDisplayName=glos.getInfo("name"),
					CFBundleName=fileNameBase,
					DCSDictionaryCopyright=copyright,
					DCSDictionaryManufacturerName=glos.getAuthor(),
					DCSDictionaryXSL=basename(xsl) if xsl else "",
					DCSDictionaryDefaultPrefs=format_default_prefs(defaultPrefs),
					DCSDictionaryPrefsHTML=basename(prefsHTML) if prefsHTML else "",
					DCSDictionaryFrontMatterReferenceID=frontMatterReferenceID,
				)
			)

		if jing:
			from .jing import run as jing_run
			jing_run(filePathBase + ".xml")
