# -*- coding: utf-8 -*-
# xdxf/__init__.py
"""xdxf file format reader and utils to convert xdxf to html."""
#
# Copyright (C) 2016 Ratijas <ratijas.t@me.com>
#
# some parts of this file include code from:
# Aard Dictionary Tools <http://aarddict.org>.
# Copyright (C) 2008-2009  Igor Tkach
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

from os import path

from formats_common import *

enable = True
format = 'Xdxf'
description = 'XDXF'
extentions = ['.xdxf', '.xml']
readOptions = []
writeOptions = []

etree = None
XML = None
tostring = None
transform = None


def import_xml_stuff():
	from lxml import etree as _etree
	global etree, XML, tostring
	etree = _etree
	XML = etree.XML
	tostring = etree.tostring


def read(glos, filename):
	"""
	new format
	<xdxf ...>
		<meta_info>
			All meta information about the dictionary: its title, author etc.
		</meta_info>
		<lexicon>
			<ar>article 1</ar>
			<ar>article 2</ar>
			<ar>article 3</ar>
			<ar>article 4</ar>
			...
		</lexicon>
	</xdxf>

	old format
	<xdxf ...>
		<full_name>...</full_name>
		<description>...</description>
		<ar>article 1</ar>
		<ar>article 2</ar>
		<ar>article 3</ar>
		<ar>article 4</ar>
		...
	</xdxf>
	"""
	# <!DOCTYPE xdxf SYSTEM "http://xdxf.sourceforge.net/xdxf_lousy.dtd">
	import_xml_stuff()

	with open(filename, 'rb') as f:
		xdxf = XML(f.read())

	if len(xdxf) == 2:
		# new format
		read_metadata_new(glos, xdxf)
		read_xdxf_new(glos, xdxf)
	else:
		# old format
		read_metadata_old(glos, xdxf)
		read_xdxf_old(glos, xdxf)


def read_metadata_old(glos, xdxf):
	full_name = xdxf.find('full_name').text
	description = xdxf.find('description').text
	if full_name:
		glos.setInfo('name', full_name)
	if description:
		glos.setInfo('description', description)


def read_xdxf_old(glos, xdxf):
	add_articles(glos, xdxf.iterfind('ar'))


def read_metadata_new(glos, xdxf):
	meta_info = xdxf.find('meta_info')
	if meta_info is None:
		raise ValueError('meta_info not found')

	title = meta_info.find('full_title').text
	if not title:
		title = meta_info.find('title').text
	description = meta_info.find('description').text

	if title:
		glos.setInfo('name', title)
	if description:
		glos.setInfo('description', description)


def read_xdxf_new(glos, xdxf):
	add_articles(glos, xdxf.find('lexicon').iterfind('ar'))


def add_articles(glos, articles):
	"""

	:param articles: iterator on <ar> tags
	:return: None
	"""
	glos.setDefaultDefiFormat('x')
	for article in articles:
		article.tail = None
		defi = tostring(article, encoding='utf-8')
		# <ar>...</ar>
		defi = defi[4:-5].strip()
		glos.addEntry(
			[toStr(w) for w in titles(article)],
			toStr(defi),
		)


def titles(article):
	"""

	:param article: <ar> tag
	:return: (title (str) | None, alternative titles (set))
	"""
	from itertools import combinations
	titles = []
	for title_element in article.findall('k'):
		n_opts = len([c for c in title_element if c.tag == 'opt'])
		if n_opts:
			for j in range(n_opts + 1):
				for comb in combinations(list(range(n_opts)), j):
					titles.append(_mktitle(title_element, comb))
		else:
			titles.append(_mktitle(title_element))

	return titles


def _mktitle(title_element, include_opts=()):
	title = title_element.text
	opt_i = -1
	for c in title_element:
		if c.tag == 'nu' and c.tail:
			if title:
				title += c.tail
			else:
				title = c.tail
		if c.tag == 'opt':
			opt_i += 1
			if opt_i in include_opts:
				if title:
					title += c.text
				else:
					title = c.text
			if c.tail:
				if title:
					title += c.tail
				else:
					title = c.tail
	return title.strip()


def xdxf_init():
	"""
	call this only once, before `xdxf_to_html`.
	"""
	global transform

	import_xml_stuff()

	xsl = path.join(path.dirname(__file__), 'xdxf.xsl')
	with open(xsl, 'r') as f:
		xslt_root_txt = f.read()

	xslt_root = etree.XML(xslt_root_txt)
	transform = etree.XSLT(xslt_root)


def xdxf_to_html(xdxf_text):
	"""
	make sure to call `xdxf_init()` first.

	:param xdxf_text: xdxf formatted string
	:return: html formatted string
	"""
	from io import StringIO
	xdxf_txt = '<ar>%s</ar>' % xdxf_text
	f = StringIO(xdxf_txt)
	doc = etree.parse(f)
	result_tree = transform(doc)
	return tostring(result_tree, encoding='utf-8')
