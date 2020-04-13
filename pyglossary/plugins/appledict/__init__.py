# -*- coding: utf-8 -*-
# appledict/__init__.py
# Output to Apple Dictionary xml sources for Dictionary Development Kit.
#
# Copyright (C) 2016 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
# Copyright (C) 2016 Ratijas <ratijas.t@me.com>
# Copyright (C) 2012-2015 Xiaoqiang Wang <xiaoqiangwang AT gmail DOT com>
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

from typing import TextIO

from pyglossary.plugins.formats_common import *
from ._dict import *

import xdxf

sys.setrecursionlimit(10000)

enable = True
format = "AppleDict"
description = "AppleDict Source (xml)"
extensions = [".xml"]
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
depends = {
	"lxml": "lxml",
	"bs4": "beautifulsoup4",
	"html5lib": "html5lib",
}

BeautifulSoup = None

def loadBeautifulSoup():
	global BeautifulSoup
	try:
		import bs4 as BeautifulSoup
	except:
		try:
			import BeautifulSoup
		except:
			return
	if int(BeautifulSoup.__version__.split(".")[0]) < 4:
		raise ImportError(
			"BeautifulSoup is too old, required at least version 4, " +
			"%r found.\n" % BeautifulSoup.__version__ +
			"Please run `sudo pip3 install lxml beautifulsoup4 html5lib`"
		)

def abspath_or_None(path):
	return os.path.abspath(os.path.expanduser(path)) if path else None


def write_header(glos: GlossaryType, toFile: TextIO, frontBackMatter: Optional[str]):
	# write header
	toFile.write(
		'<?xml version="1.0" encoding="UTF-8"?>\n'
		'<d:dictionary xmlns="http://www.w3.org/1999/xhtml" '
		'xmlns:d="http://www.apple.com/DTDs/DictionaryService-1.0.rng">\n'
	)

	if frontBackMatter:
		with open(frontBackMatter, "r") as front_back_matter:
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
		raise TypeError("defaultPrefs not a dictionary: %r" % defaultPrefs)
	if str(defaultPrefs.get("version", None)) != "1":
		log.error("default prefs does not contain {'version': '1'}.  prefs "
				  "will not be persistent between Dictionary.app restarts.")
	return "\n".join("\t\t<key>%s</key>\n\t\t<string>%s</string>" % i
					 for i in sorted(defaultPrefs.items())).strip()


def write_css(fname, css_file):
	with open(fname, "wb") as toFile:
		if css_file:
			with open(css_file, "rb") as fromFile:
				toFile.write(fromFile.read())
		else:
			toFile.write(pkgutil.get_data(
				__name__,
				"templates/Dictionary.css",
			))


def write(
	glos: GlossaryType,
	dirname: str,
	cleanHTML: bool = True,
	css: str = "",
	xsl: str = "",
	defaultPrefs: Optional[Dict] = None,
	prefsHTML: str = "",
	frontBackMatter: str = "",
	jing: bool = False,
	indexes: str = "",# FIXME: rename to indexes_lang?
):
	"""
	write glossary to Apple dictionary .xml and supporting files.

	:type glos: pyglossary.glossary.Glossary
	:type dirname: str, directory path, must not have extension

	:type cleanHTML: bool
	:param cleanHTML: pass True to use BeautifulSoup parser.

	:type css: str
	:param css: path to custom .css file

	:type xsl: str
	:param xsl: path to custom XSL transformations file.

	:type defaultPrefs: dict or None
	:param defaultPrefs: Default prefs in python dictionary literal format,
	i.e. {"key1": "value1", "key2": "value2", ...}.  All keys and values must
	be quoted strings; not allowed characters (e.g. single/double quotes,
	equal sign "=", semicolon) must be escaped as hex code according to
	python string literal rules.

	:type prefsHTML: str
	:param prefsHTML: path to XHTML file with user interface for dictionary's
	preferences.  refer to Apple's documentation for details.

	:type frontBackMatter: str
	:param frontBackMatter: path to XML file with top-level tag
	<d:entry id="front_back_matter" d:title="Your Front/Back Matter Title">
		your front/back matter entry content
	</d:entry>

	:type jing: bool
	:param jing: pass True to run Jing check on generated XML.

	# FIXME: rename to indexes_lang?
	:type indexes: str
	:param indexes: Dictionary.app is dummy and by default it don't know
	how to perform flexible search.  we can help it by manually providing
	additional indexes to dictionary entries.
	"""
	global BeautifulSoup

	if not isdir(dirname):
		os.mkdir(dirname)

	xdxf.xdxf_init()

	if cleanHTML:
		if BeautifulSoup is None:
			loadBeautifulSoup()
		if BeautifulSoup is None:
			log.warning(
				"cleanHTML option passed but BeautifulSoup not found.  " +
				"to fix this run `sudo pip3 install lxml beautifulsoup4 html5lib`"
			)
	else:
		BeautifulSoup = None

	fileNameBase = basename(dirname).replace(".", "_")
	filePathBase = join(dirname, fileNameBase)
	# before chdir (outside indir block)
	css = abspath_or_None(css)
	xsl = abspath_or_None(xsl)
	prefsHTML = abspath_or_None(prefsHTML)
	frontBackMatter = abspath_or_None(frontBackMatter)

	generate_id = id_generator()
	generate_indexes = indexes_generator(indexes)

	glos.setDefaultDefiFormat("h")

	myResDir = join(dirname, "OtherResources")
	if not isdir(myResDir):
		os.mkdir(myResDir)

	with open(filePathBase + ".xml", "w", encoding="utf-8") as toFile:
		write_header(glos, toFile, frontBackMatter)
		for entryI, entry in enumerate(glos):
			if entry.isData():
				entry.save(myResDir)
				continue

			words = entry.getWords()
			word, alts = words[0], words[1:]
			defi = entry.getDefi()

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
			if entry.getDefiFormat() == "x":
				defi = xdxf.xdxf_to_html(defi)
				content_title = None
			content = format_clean_content(content_title, defi, BeautifulSoup)

			toFile.write(
				'<d:entry id="%s" d:title=%s>\n' % (_id, title_attr) +
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

	with open(join(dirname, "Makefile"), "w") as toFile:
		toFile.write(
			toStr(pkgutil.get_data(
				__name__,
				"templates/Makefile",
			)) % {"dict_name": fileNameBase}
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
	with open(filePathBase + ".plist", "w", encoding="utf-8") as toFile:
		toFile.write(
			toStr(pkgutil.get_data(
				__name__,
				"templates/Info.plist",
			)) % {
				"CFBundleIdentifier":
					fileNameBase.replace(" ", ""),  # identifier must be unique
				"CFBundleDisplayName":
					glos.getInfo("name"),
				"CFBundleName":
					fileNameBase,
				"DCSDictionaryCopyright":
					copyright,
				"DCSDictionaryManufacturerName":
					glos.getInfo("author"),
				"DCSDictionaryXSL":
					basename(xsl) if xsl else "",
				"DCSDictionaryDefaultPrefs":
					format_default_prefs(defaultPrefs),
				"DCSDictionaryPrefsHTML":
					basename(prefsHTML) if prefsHTML else "",
				"DCSDictionaryFrontMatterReferenceID":
					"<key>DCSDictionaryFrontMatterReferenceID</key>\n"
					"\t<string>front_back_matter</string>" if frontBackMatter
					else "",
			}
		)

	if jing:
		from .jing import run as jing_run
		jing_run(filePathBase + ".xml")
