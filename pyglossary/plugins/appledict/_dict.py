# -*- coding: utf-8 -*-
# appledict/_dict.py
# Output to Apple Dictionary xml sources for Dictionary Development Kit.
#
# Copyright © 2016-2019 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
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

import logging
import re
import string
from xml.sax.saxutils import unescape, quoteattr

from . import _normalize
from pyglossary.plugins.formats_common import *

log = logging.getLogger("pyglossary")

digs = string.digits + string.ascii_letters


def base36(x: int) -> str:
	"""
	simplified version of int2base
	http://stackoverflow.com/questions/2267362/convert-integer-to-a-string-in-a-given-numeric-base-in-python#2267446
	"""
	digits = []
	while x:
		digits.append(digs[x % 36])
		x //= 36
	digits.reverse()
	return "".join(digits)


def id_generator() -> "Iterator[str]":
	cnt = 1

	while True:
		yield "_" + str(base36(cnt))
		cnt += 1


def indexes_generator(indexes_lang: str) -> """Callable[
	[str, List[str], str, Any],
	str,
]""":
	"""
	factory that acts according to glossary language
	"""
	indexer = None
	"""Callable[[Sequence[str], str], Sequence[str]]"""
	if indexes_lang:
		from . import indexes as idxs
		indexer = idxs.languages.get(indexes_lang, None)
		if not indexer:
			keys_str = ", ".join(list(idxs.languages.keys()))
			msg = "extended indexes not supported for the" \
				f" specified language: {indexes_lang}.\n" \
				f"following languages available: {keys_str}."
			log.error(msg)
			raise ValueError(msg)

	def generate_indexes(title, alts, content, BeautifulSoup):
		indexes = [title]
		indexes.extend(alts)

		if BeautifulSoup:
			quoted_title = BeautifulSoup.dammit.EntitySubstitution\
				.substitute_xml(title, True)
		else:
			quoted_title = '"' + \
				title.replace(">", "&gt;").replace('"', "&quot;") + \
				'"'

		if indexer:
			indexes = set(indexer(indexes, content))

		normal_indexes = set()
		for idx in indexes:
			normal = _normalize.title(idx, BeautifulSoup)
			normal_indexes.add(_normalize.title_long(normal))
			normal_indexes.add(_normalize.title_short(normal))
		normal_indexes.discard(title)

		normal_indexes = [s for s in normal_indexes if s.strip()]
		# skip empty titles.  everything could happen.

		s = f"<d:index d:value={quoted_title} d:title={quoted_title}/>"
		if BeautifulSoup:
			for idx in normal_indexes:
				quoted_idx = BeautifulSoup.dammit.\
					EntitySubstitution.substitute_xml(idx, True)
				s += f"<d:index d:value={quoted_idx} d:title={quoted_title}/>"
		else:
			for idx in normal_indexes:
				quoted_idx = '"' + \
					idx.replace(">", "&gt;").replace('"', "&quot;") + \
					'"'
				s += f"<d:index d:value={quoted_idx} d:title={quoted_title}/>"
		return s
	return generate_indexes


# FIXME:
# MDX-specific parts should be isolated and moved to MDX Reader
# and parts that are specific to one glossary
# (like Oxford_Advanced_English-Chinese_Dictionary_9th_Edition.mdx)
# should be moved to separate modules (like content processors) and enabled
# per-glossary (by title or something else)

re_brhr = re.compile("<(BR|HR)>", re.IGNORECASE)
re_nonprintable = re.compile("[\x00-\x07\x0e-\x1f]")
re_img = re.compile("<IMG (.*?)>", re.IGNORECASE)

re_div_margin_em = re.compile(r'<div style="margin-left:(\d)em">')
sub_div_margin_em = r'<div class="m\1">'

re_div_margin_em_ex = re.compile(
	r'<div class="ex" style="margin-left:(\d)em;color:steelblue">',
)
sub_div_margin_em_ex = r'<div class="m\1 ex">'

re_href = re.compile(r"""href=(["'])(.*?)\1""")

re_margin = re.compile(r"margin-left:(\d)em")


def href_sub(x: "typing.re.Pattern") -> str:
	href = x.groups()[1]
	if href.startswith("http"):
		return x.group()

	href = cleanup_link_target(href)

	return "href=" + quoteattr(
		"x-dictionary:d:" + unescape(
			href,
			{"&quot;": '"'},
		)
	)


def is_green(x: dict) -> bool:
	return "color:green" in x.get("style", "")


def remove_style(tag: dict, line: str) -> None:
	s = "".join(tag["style"].replace(line, "").split(";"))
	if s:
		tag["style"] = s
	else:
		del tag["style"]


def fix_sound_link(href: str, tag: dict):
	tag["href"] = f'javascript:new Audio("{href[len("sound://"):]}").play();'


def link_is_url(href: str) -> bool:
	for prefix in (
		"http:",
		"https:",
		"addexample:",
		"addid:",
		"addpv:",
		"help:",
		"helpg:",
		"helpp:",
		"helpr:",
		"helpxr:",
		"xi:",
		"xid:",
		"xp:",
		"sd:",
		"#",
	):
		if href.startswith(prefix):
			return True
	return False


def prepare_content_without_soup(
	title: "Optional[str]",
	body: str,
) -> str:
	# somewhat analogue to what BeautifulSoup suppose to do
	body = re_div_margin_em.sub(sub_div_margin_em, body)
	body = re_div_margin_em_ex.sub(sub_div_margin_em_ex, body)
	body = re_href.sub(href_sub, body)

	body = body \
		.replace(
			'<i style="color:green">',
			'<i class="c">',
		) \
		.replace(
			'<i class="p" style="color:green">',
			'<i class="p">',
		) \
		.replace(
			'<span class="ex" style="color:steelblue">',
			'<span class="ex">',
		) \
		.replace(
			'<span class="sec ex" style="color:steelblue">',
			'<span class="sec ex">',
		) \
		.replace("<u>", '<span class="u">').replace("</u>", "</span>") \
		.replace("<s>", "<del>").replace("</s>", "</del>")

	# nice header to display
	content = f"<h1>{title}</h1>{body}" if title else body
	content = re_brhr.sub(r"<\g<1> />", content)
	content = re_img.sub(r"<img \g<1>/>", content)
	return content


def prepare_content_with_soup(
	title: "Optional[str]",
	body: str,
	BeautifulSoup: "Any",
) -> str:
	soup = BeautifulSoup.BeautifulSoup(body, features="lxml")
	# difference between "lxml" and "html.parser"
	if soup.body:
		soup = soup.body

	for tag in soup(class_="sec"):
		tag["class"].remove("sec")
		if not tag["class"]:
			del tag["class"]
		tag["d:priority"] = "2"
	for tag in soup(lambda x: "color:steelblue" in x.get("style", "")):
		remove_style(tag, "color:steelblue")
		if "ex" not in tag.get("class", []):
			tag["class"] = tag.get("class", []) + ["ex"]
	for tag in soup(is_green):
		remove_style(tag, "color:green")
		if "p" not in tag.get("class", ""):
			tag["class"] = tag.get("class", []) + ["c"]
	for tag in soup(True):
		if "style" in tag.attrs:
			m = re_margin.search(tag["style"])
			if m:
				remove_style(tag, m.group(0))
				tag["class"] = tag.get("class", []) + ["m" + m.group(1)]

	for tag in soup(lambda x: "xhtml:" in x.name):
		old_tag_name = tag.name
		tag.name = old_tag_name[len("xhtml:"):]
		if tag.string:
			tag.string = f"{tag.string} "

	for tag in soup.select("[href]"):
		href = tag["href"]
		href = cleanup_link_target(href)

		if href.startswith("sound:"):
			fix_sound_link(href, tag)

		elif href.startswith("phonetics") or href.startswith("help:phonetics"):
			# for oxford9
			log.debug(f"phonetics: tag={tag}")
			if tag.audio and "name" in tag.audio.attrs:
				tag["onmousedown"] = f"this.lastChild.play(); return false;"
				src_name = tag.audio["name"].replace("#", "_")
				tag.audio["src"] = f"{src_name}.mp3"

		elif not link_is_url(href):
			tag["href"] = f"x-dictionary:d:{href}"

	for thumb in soup.find_all("div", "pic_thumb"):
		thumb["onclick"] = 'this.setAttribute("style", "display:none"); ' \
			'this.nextElementSibling.setAttribute("style", "display:block")'

	for pic in soup.find_all("div", "big_pic"):
		pic["onclick"] = 'this.setAttribute("style", "display:none"), ' \
			'this.previousElementSibling.setAttribute("style", "display:block")'

	# to unfold(expand) and fold(collapse) blocks
	for pos in soup.find_all("pos", onclick="toggle_infl(this)"):
		# TODO: simplify this!
		pos["onclick"] = (
			r'var e = this.parentElement.parentElement.parentElement'
			r'.querySelector("res-g vp-gs"); style = window.'
			r'getComputedStyle(e), display = style.getPropertyValue'
			r'("display"), "none" === e.style.display || "none" === display'
			r' ? e.style.display = "block" : e.style.display = "none", '
			r'this.className.match(/(?:^|\s)Clicked(?!\S)/) ? this.'
			r'className = this.className.replace('
			r'/(?:^|\s)Clicked(?!\S)/g, "") : this.setAttribute('
			r'"class", "Clicked")'
		)

	for tag in soup.select("[src]"):
		src = tag["src"]
		if src.startswith("/"):
			tag["src"] = src[1:]
	for tag in soup("u"):
		tag.name = "span"
		tag["class"] = tag.get("class", []) + ["u"]
	for tag in soup("s"):
		tag.name = "del"

	if title and "<h" not in body:
		h1 = BeautifulSoup.Tag(name="h1")
		h1.string = title
		soup.insert(0, h1)

	# hence the name BeautifulSoup
	# soup.insert(0,head)
	content = toStr(soup.encode_contents())
	return content


def prepare_content(
	title: "Optional[str]",
	body: str,
	BeautifulSoup: "Any",
) -> str:
	# heavily integrated with output of dsl reader plugin!
	# and with xdxf also.
	"""
	:param title: str | None
	"""

	# class="sec" => d:priority="2"
	# style="color:steelblue" => class="ex"
	# class="p" style="color:green" => class="p"
	# style="color:green" => class="c"
	# style="margin-left:{}em" => class="m{}"
	# <s> => <del>

	# xhtml is strict
	if BeautifulSoup:
		content = prepare_content_with_soup(title, body, BeautifulSoup)
	else:
		content = prepare_content_without_soup(title, body)

	content = content.replace("&nbsp;", "&#160;")
	content = re_nonprintable.sub("", content)
	return content


def cleanup_link_target(href):
	if href.startswith("bword://"):
		href = href[len("bword://"):]
	return href
