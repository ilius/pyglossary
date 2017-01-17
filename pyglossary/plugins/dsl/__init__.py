# -*- coding: utf-8 -*-
# dsl/__init__.py
# Read ABBYY Lingvo DSL dictionary format
#
# Copyright (C) 2013 Xiaoqiang Wang <xiaoqiangwang AT gmail DOT com>
# Copyright (C) 2013-2016 Saeed Rasooli <saeed.gnu@gmail.com>
# Copyright (C) 2016 Ratijas <ratijas.t@me.com>
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

import re
import html.entities
from xml.sax.saxutils import escape, quoteattr

from formats_common import *
from . import flawless_dsl

enable = True
format = 'ABBYYLingvoDSL'
description = 'ABBYY Lingvo DSL (dsl)'
extentions = ['.dsl']
readOptions = ['encoding', 'audio', 'onlyFixMarkUp']
writeOptions = []

__all__ = ['read']

# {{{
# modified to work around codepoints that are not supported by `unichr`.
# http://effbot.org/zone/re-sub.htm#unescape-html
# January 15, 2003 | Fredrik Lundh


# Removes HTML or XML character references and entities from a text string.
#
# @param text The HTML (or XML) source text.
# @return The plain text, as a Unicode string, if necessary.

def unescape(text):
	def fixup(m):
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
					return ("\\U%08x" % i)\
						.decode('unicode-escape').encode('utf-8')
		else:
			# named entity
			try:
				text = chr(html.entities.name2codepoint[text[1:-1]])
			except KeyError:
				pass
		return text  # leave as is
	return re.sub("&#?\w+;", fixup, text)
# }}}


def make_a_href(s):
	return '<a href=%s>%s</a>' % (quoteattr(s), escape(s))


def ref_sub(x):
	return make_a_href(unescape(x.groups()[0]))


# order matters, a lot.
shortcuts = [
	# canonical: m > * > ex > i > c
	(
		r'[i][c](.*?)[/c][/i]',
		r'<i style="color:green">\g<1></i>'
	),
	(
		r'[m(\d)][ex](.*?)[/ex][/m]',
		r'<div class="ex" '
		r'style="margin-left:\g<1>em;color:steelblue">\g<2></div>'
	),
	(
		r'[m(\d)][*][ex](.*?)[/ex][/*][/m]',
		r'<div class="sec ex" '
		r'style="margin-left:\g<1>em;color:steelblue">\g<2></div>'
	),
	(
		r'[*][ex](.*?)[/ex][/*]',
		r'<span class="sec ex" style="color:steelblue">\g<1></span>'
	),
	(
		r'[m1](?:-{2,})[/m]',
		'<hr/>'
	),
	(
		r'[m(\d)](?:-{2,})[/m]',
		r'<hr style="margin-left:\g<1>em"/>'
	),
]

shortcuts = [
	(
		re.compile(repl.replace('[', r'\[').replace('*]', r'\*]')),
		sub
	) for (repl, sub) in shortcuts
]


# precompiled regexs
re_brackets_blocks = re.compile(r'\{\{[^}]*\}\}')
re_lang_open = re.compile(r'\[lang[^\]]*\]')
re_m_open = re.compile(r'(?<!\\)\[m\d\]')
re_c_open_color = re.compile(r'\[c (\w+)\]')
re_sound = re.compile(r'\[s\]([^\[]*?)(wav|mp3)\s*\[/s\]')
re_img = re.compile(r'\[s\]([^\[]*?)(jpg|jpeg|gif|tif|tiff)\s*\[/s\]')
re_m = re.compile(r'\[m(\d)\](.*?)\[/m\]')
wrapped_in_quotes_re = re.compile(r'^(\'|")(.*)(\1)$')

# single instance of parser
# it's safe as long as this script's not going multithread.
_parse = flawless_dsl.FlawlessDSLParser().parse


def apply_shortcuts(line):
	for repl, sub in shortcuts:
		line = re.sub(repl, sub, line)
	return line


def _clean_tags(line, audio):
	r"""
	WARNING! shortcuts may apply:
		[m2][*][ex]{}[/ex][/*][/m]
		=>
		<div class="sec ex" style="margin-left:2em;color:steelblue">{}</div>
	[m{}] => <div style="margin-left:{}em">
	[*]   => <span class="sec">
	[ex]  => <span class="ex" style="color:steelblue">
	[c]   => <span style="color:green">
	[p]   => <i class="p" style="color:green">

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

	[t] => <!-- T --><span style="font-family:'Helvetica'">

	{{...}}   \
	[trn]      |
	[!trn]     |
	[trs]      } => remove
	[!trs]     |
	[lang ...] |
	[com]     /
	"""
	# remove {{...}} blocks
	line = re_brackets_blocks.sub('', line)
	# remove trn tags
	# re_trn = re.compile('\[\/?!?tr[ns]\]')
	line = line \
		.replace('[trn]', '') \
		.replace('[/trn]', '') \
		.replace('[trs]', '') \
		.replace('[/trs]', '') \
		.replace('[!trn]', '') \
		.replace('[/!trn]', '') \
		.replace('[!trs]', '') \
		.replace('[/!trs]', '')

	# remove lang tags
	line = re_lang_open.sub('', line).replace('[/lang]', '')
	# remove com tags
	line = line.replace('[com]', '').replace('[/com]', '')
	# remove t tags
	line = line.replace(
		'[t]',
		'<!-- T --><span style="font-family:\'Helvetica\'">'
	)
	line = line.replace('[/t]', '</span><!-- T -->')

	line = _parse(line)

	line = re.sub(r'\\$', '<br/>', line)

	# paragraph, part one: before shortcuts.
	line = line.replace('[m]', '[m1]')
	# if line somewhere contains '[m_]' tag like
	# "[b]I[/b][m1] [c][i]conj.[/i][/c][/m][m1]1) ...[/m]"
	# then leave it alone.  only wrap in '[m1]' when no 'm' tag found at all.
	if not re_m_open.search(line):
		line = '[m1]%s[/m]' % line

	line = apply_shortcuts(line)

	# paragraph, part two: if any not shourcuted [m] left?
	line = re_m.sub('<div style="margin-left:\g<1>em">\g<2></div>', line)

	# text formats

	line = line.replace("[']", '<u>').replace("[/']", '</u>')
	line = line.replace('[b]', '<b>').replace('[/b]', '</b>')
	line = line.replace('[i]', '<i>').replace('[/i]', '</i>')
	line = line.replace('[u]', '<u>').replace('[/u]', '</u>')
	line = line.replace('[sup]', '<sup>').replace('[/sup]', '</sup>')
	line = line.replace('[sub]', '<sub>').replace('[/sub]', '</sub>')

	# color
	line = line.replace('[c]', '<span style="color:green">')
	line = re_c_open_color.sub('<span style="color:\g<1>">', line)
	line = line.replace('[/c]', '</span>')

	# example zone
	line = line.replace('[ex]', '<span class="ex" style="color:steelblue">')
	line = line.replace('[/ex]', '</span>')

	# secondary zone
	line = line.replace('[*]', '<span class="sec">')\
		.replace('[/*]', '</span>')

	# abbrev. label
	line = line.replace('[p]', '<i class="p" style="color:green">')
	line = line.replace('[/p]', '</i>')

	# cross reference
	line = line.replace('[ref]', '<<').replace('[/ref]', '>>')
	line = line.replace('[url]', '<<').replace('[/url]', '>>')
	line = re.sub('<<(.*?)>>', ref_sub, line)

	# sound file
	if audio:
		sound_tag = '<object type="audio/x-wav" data="\g<1>\g<2>" ' \
			'width="40" height="40">' \
			'<param name="autoplay" value="false" />' \
			'</object>'
	else:
		sound_tag = ''
	line = re_sound.sub(sound_tag, line)

	# image file
	line = re_img.sub(
		'<img align="top" src="\g<1>\g<2>" alt="\g<1>\g<2>" />',
		line,
	)

	# \[...\]
	line = line.replace(r'\[', '[').replace(r'\]', ']')
	return line


def unwrap_quotes(s):
	return wrapped_in_quotes_re.sub(r'\2', s)


def read(glos, fname, **options):
	encoding = options.get('encoding', 'utf-8')
	audio = (options.get('audio', 'no') == 'yes')
	onlyFixMarkUp = (options.get('onlyFixMarkUp', 'no') == 'yes')
	if onlyFixMarkUp:
		def clean_tags(line, audio):
			return _parse(line)
	else:
		clean_tags = _clean_tags

	def setInfo(key, value):
		glos.setInfo(key, unwrap_quotes(value))

	current_key = ''
	current_key_alters = []
	current_text = []
	line_type = 'header'
	unfinished_line = ''

	fp = open(fname, 'r', encoding=encoding)
	for line in fp:
		line = line.rstrip()
		if not line:
			continue
		# header
		if line.startswith('#'):
			if line.startswith('#NAME'):
				setInfo('title', line[6:])
			elif line.startswith('#INDEX_LANGUAGE'):
				setInfo('sourceLang', line[16:])
			elif line.startswith('#CONTENTS_LANGUAGE'):
				setInfo('targetLang', line[20:])
			line_type = 'header'
		# texts
		elif line.startswith(' ') or line.startswith('\t'):
			line_type = 'text'
			line = unfinished_line + line.lstrip()

			# some ill formated source may have tags spanned into
			# multiple lines
			# try to match opening and closing tags
			tags_open = re.findall('(?<!\\\\)\[(c |[cuib]\])', line)
			tags_close = re.findall('\[/[cuib]\]', line)
			if len(tags_open) != len(tags_close):
				unfinished_line = line
				continue

			unfinished_line = ''

			# convert DSL tags to HTML tags
			line = clean_tags(line, audio)
			current_text.append(line)
		# title word(s)
		else:
			# alternative titles
			if line_type == 'title':
				current_key_alters.append(line)
			# previous line type is text -> start new title
			else:
				# append previous entry
				if line_type == 'text':
					if unfinished_line:
						# line may be skipped if ill formated
						current_text.append(clean_tags(unfinished_line, audio))
					glos.addEntry(
						[current_key] + current_key_alters,
						'\n'.join(current_text),
					)
				# start new entry
				current_key = line
				current_key_alters = []
				current_text = []
				unfinished_line = ''
			line_type = 'title'
	fp.close()

	# last entry
	if line_type == 'text':
		glos.addEntry(
			[current_key] + current_key_alters,
			'\n'.join(current_text),
		)
