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

from typing import Callable
from typing.re import Pattern


from . import _normalize
from pyglossary.plugins.formats_common import *

log = logging.getLogger("root")

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


def id_generator() -> Iterator[str]:
	cnt = 1

	while True:
		yield "_" + str(base36(cnt))
		cnt += 1


def indexes_generator(indexes_lang: str) -> Callable[
	[str, List[str], str, Any],
	str,
]:
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


close_tag = re.compile("<(BR|HR)>", re.IGNORECASE)
nonprintable = re.compile("[\x00-\x07\x0e-\x1f]")
img_tag = re.compile("<IMG (.*?)>", re.IGNORECASE)

em0_9_re = re.compile(r'<div style="margin-left:(\d)em">')
em0_9_sub = r'<div class="m\1">'

em0_9_ex_re = re.compile(
	r'<div class="ex" style="margin-left:(\d)em;color:steelblue">',
)
em0_9_ex_sub = r'<div class="m\1 ex">'

href_re = re.compile(r"""href=(["'])(.*?)\1""")

margin_re = re.compile(r"margin-left:(\d)em")


def href_sub(x: Pattern) -> str:
	href = x.groups()[1]
	if href.startswith("http"):
		return x.group()

	href=_href_cleanup(href)

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


def format_clean_content(
	title: Optional[str],
	body: str,
	BeautifulSoup: Any,
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
				m = margin_re.search(tag["style"])
				if m:
					remove_style(tag, m.group(0))
					tag["class"] = tag.get("class", []) + ["m" + m.group(1)]

		for tag in soup(lambda x: 'xhtml:' in x.name):
			old_tag_name = tag.name
			tag.name = old_tag_name[len('xhtml:'):]
			if tag.string:
				tag.string = f'{tag.string} '

		for tag in soup.select("[href]"):
			href = tag["href"]
			href = _href_cleanup(href)

			if href.startswith("sound:"):
				src = href[len("sound://"):]
				if 'data-file' in tag.attrs:  # for webster
					del tag["href"]
					audio = BeautifulSoup.Tag(name="audio")
					audio['id'] = tag['data-file']
					audio['src'] = f"{src}"
					tag['onmousedown'] = f'document.getElementById("{tag["data-file"]}").play(); return false;'
					tag.insert_after(audio)

				elif 'class' in tag.attrs:
					if 'fayin' in tag['class']:  # for oxford8
						del tag["href"]
						audio = BeautifulSoup.Tag(name="audio")
						audio['src'] = f"{src}"
						tag['onmousedown'] = f'this.lastChild.play(); return false;'
						tag.append(audio)

				else:
					brk = False
					for ch in tag.children:
						if ch.find_all('a'):
							brk = True
							break

					if not brk:
						audio = BeautifulSoup.Tag(name="audio")
						audio['src'] = f"{src}"
						tag['onmousedown'] = f'this.lastChild.play(); return false;'
						tag.append(audio)
						del tag["href"]

			elif href.startswith("phonetics") or href.startswith("help:phonetics"):  # for oxford9
				# print(tag)
				if tag.audio and 'name' in tag.audio.attrs:
					tag['onmousedown'] = f'this.lastChild.play(); return false;'
					src_name = tag.audio['name'].replace('#', '_')
					tag.audio['src'] = f"{src_name}.mp3"
			# print
			elif not (href.startswith("http:")
					  or href.startswith("https:")

					  or href.startswith("addexample:")
					  or href.startswith("addid:")
					  or href.startswith("addpv:")

					  or href.startswith("help:")
					  or href.startswith("helpg:")
					  or href.startswith("helpp:")
					  or href.startswith("helpr:")
					  or href.startswith("helpxr:")

					  or href.startswith("xi:")
					  or href.startswith("xid:")
					  or href.startswith("xp:")
					  or href.startswith("sd:")
					  or href.startswith("#")
			):

				tag["href"] = f"x-dictionary:d:{href}"

		for thumb in soup.find_all('div', 'pic_thumb'):
			thumb['onclick'] = f'this.setAttribute("style", "display:none"); this.nextElementSibling.setAttribute("style", "display:block")'

		for pic in soup.find_all('div', 'big_pic'):
			pic['onclick'] = f'this.setAttribute("style", "display:none"), this.previousElementSibling.setAttribute("style", "display:block")'

		for pos in soup.find_all('pos', onclick='toggle_infl(this)'):
			pos['onclick'] = f'var e = this.parentElement.parentElement.parentElement.querySelector("res-g vp-gs"); style = window.getComputedStyle(e), display = style.getPropertyValue("display"), "none" === e.style.display || "none" === display ? e.style.display = "block" : e.style.display = "none", this.className.match(/(?:^|\s)Clicked(?!\S)/) ? this.className = this.className.replace(/(?:^|\s)Clicked(?!\S)/g, "") : this.setAttribute("class", "Clicked")'

		for tag in soup.select("[src]"):
			src = tag['src']
			if src.startswith("/"):
				tag['src'] = src[1:]
		for tag in soup("u"):
			tag.name = "span"
			tag["class"] = tag.get("class", []) + ["u"]
		for tag in soup("s"):
			tag.name = "del"

		if title and not '<h' in body:
			h1 = BeautifulSoup.Tag(name="h1")
			h1.string = title
			soup.insert(0, h1)
		# hence the name BeautifulSoup
		# soup.insert(0,head)
		content = toStr(soup.encode_contents())
	else:
		# somewhat analogue to what BeautifulSoup suppose to do
		body = em0_9_re.sub(em0_9_sub, body)
		body = em0_9_ex_re.sub(em0_9_ex_sub, body)
		body = href_re.sub(href_sub, body)

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
		content = close_tag.sub(r"<\g<1> />", content)
		content = img_tag.sub(r"<img \g<1>/>", content)
	content = content.replace("&nbsp;", "&#160;")
	content = nonprintable.sub("", content)
	return content


def _href_cleanup(href):
	if href.startswith("bword://"):
		href = href[len("bword://"):]

	if href.startswith("entry://"):
		href = href[len("entry://"):]

	xhtml_ns = ['d','x']
	for n in xhtml_ns:
		if href.startswith(f'{n}:'):
			href = href[len(n) + 1:]

	return href
