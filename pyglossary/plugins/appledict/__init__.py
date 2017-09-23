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

from pyglossary.plugins.formats_common import *
from ._dict import *

import xdxf

sys.setrecursionlimit(10000)

enable = True
format = "AppleDict"
description = "AppleDict Source (xml)"
extentions = [".xml"]
readOptions = []
writeOptions = [
	"cleanHTML",  # bool
	"css",  # str or None
	"xsl",  # str or None
	"defaultPrefs",  # dict or None, FIXME
	"prefsHTML",  # str or None
	"frontBackMatter",  # str or None
	"jing",  # str or None
	"indexes",  # str or None
]


def abspath_or_None(path):
	return os.path.abspath(os.path.expanduser(path)) if path else None


def write_header(glos, toFile, frontBackMatter):
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
	glos,
	dirPath,
	cleanHTML=True,
	css=None,
	xsl=None,
	defaultPrefs=None,
	prefsHTML=None,
	frontBackMatter=None,
	jing=None,
	indexes=None,
):
	"""
	write glossary to Apple dictionary .xml and supporting files.

	:type glos: pyglossary.glossary.Glossary
	:type dirPath: str, directory path, must not have extension

	:type cleanHTML: str
	:param cleanHTML: pass "yes" to use BeautifulSoup parser.

	:type css: str or None
	:param css: path to custom .css file

	:type xsl: str or None
	:param xsl: path to custom XSL transformations file.

	:type defaultPrefs: dict or None
	:param defaultPrefs: Default prefs in python dictionary literal format,
	i.e. {"key1": "value1", "key2": "value2", ...}.  All keys and values must
	be quoted strings; not allowed characters (e.g. single/double quotes,
	equal sign "=", semicolon) must be escaped as hex code according to
	python string literal rules.

	:type prefsHTML: str or None
	:param prefsHTML: path to XHTML file with user interface for dictionary's
	preferences.  refer to Apple's documentation for details.

	:type frontBackMatter: str or None
	:param frontBackMatter: path to XML file with top-level tag
	<d:entry id="front_back_matter" d:title="Your Front/Back Matter Title">
		your front/back matter entry content
	</d:entry>

	:type jing: str or None
	:param jing: pass "yes" to run Jing check on generated XML.

	:type indexes: str or None
	:param indexes: Dictionary.app is dummy and by default it don't know
	how to perform flexible search.  we can help it by manually providing
	additional indexes to dictionary entries.
	# for now no languages supported yet.
	"""
	if not isdir(dirPath):
		os.mkdir(dirPath)

	xdxf.xdxf_init()

	if cleanHTML:
		BeautifulSoup = get_beautiful_soup()
		if not BeautifulSoup:
			log.warning(
				"cleanHTML option passed but BeautifulSoup not found.  " +
				"to fix this run `sudo pip3 install lxml beautifulsoup4 html5lib`"
			)
	else:
		BeautifulSoup = None

	fileNameBase = basename(dirPath).replace(".", "_")
	filePathBase = join(dirPath, fileNameBase)
	# before chdir (outside indir block)
	css = abspath_or_None(css)
	xsl = abspath_or_None(xsl)
	prefsHTML = abspath_or_None(prefsHTML)
	frontBackMatter = abspath_or_None(frontBackMatter)

	generate_id = id_generator()
	generate_indexes = indexes_generator(indexes)

	glos.setDefaultDefiFormat("h")

	myResDir = join(dirPath, "OtherResources")
	if not isdir(myResDir):
		os.mkdir(myResDir)

	with open(filePathBase + ".xml", "w", encoding="utf8") as toFile:
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

	with open(join(dirPath, "Makefile"), "w") as toFile:
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
			"lxml"
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

	if jing == "yes":
		from .jing import run as jing_run
		jing_run(filePathBase + ".xml")
