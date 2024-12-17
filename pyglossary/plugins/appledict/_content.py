# -*- coding: utf-8 -*-
#
# Copyright © 2016-2019 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
# Copyright © 2016 ivan tkachenko me@ratijas.tk
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
# FIXME:
# MDX-specific parts should be isolated and moved to MDX Reader
# and parts that are specific to one glossary
# (like Oxford_Advanced_English-Chinese_Dictionary_9th_Edition.mdx)
# should be moved to separate modules (like content processors) and enabled
# per-glossary (by title or something else)
from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING, Any
from xml.sax.saxutils import quoteattr, unescape

if TYPE_CHECKING:
	import bs4 as BeautifulSoup
	import bs4.element

from pyglossary.text_utils import toStr

__all__ = ["prepare_content"]

log = logging.getLogger("pyglossary")


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


def prepare_content(
	title: str | None,
	body: str,
	BeautifulSoup: Any,
) -> str:
	# heavily integrated with output of dsl reader plugin!
	# and with xdxf also.
	""":param title: str | None"""
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
	return content  # noqa: RET504


def prepare_content_without_soup(
	title: str | None,
	body: str,
) -> str:
	# somewhat analogue to what BeautifulSoup suppose to do
	body = re_div_margin_em.sub(sub_div_margin_em, body)
	body = re_div_margin_em_ex.sub(sub_div_margin_em_ex, body)
	body = re_href.sub(href_sub, body)

	body = (
		body.replace(
			'<i style="color:green">',
			'<i class="c">',
		)
		.replace(
			'<i class="p" style="color:green">',
			'<i class="p">',
		)
		.replace(
			'<span class="ex" style="color:steelblue">',
			'<span class="ex">',
		)
		.replace(
			'<span class="sec ex" style="color:steelblue">',
			'<span class="sec ex">',
		)
		.replace("<u>", '<span class="u">')
		.replace("</u>", "</span>")
		.replace("<s>", "<del>")
		.replace("</s>", "</del>")
	)

	# nice header to display
	content = f"<h1>{title}</h1>{body}" if title else body
	content = re_brhr.sub(r"<\g<1> />", content)
	content = re_img.sub(r"<img \g<1>/>", content)
	return content  # noqa: RET504


def _prepare_href(tag: bs4.element.Tag) -> None:
	href = tag["href"]
	href = cleanup_link_target(href)

	if href.startswith("sound:"):
		fix_sound_link(href, tag)

	elif href.startswith(("phonetics", "help:phonetics")):
		# for oxford9
		log.debug(f"phonetics: {tag=}")
		if tag.audio and "name" in tag.audio.attrs:
			tag["onmousedown"] = "this.lastChild.play(); return false;"
			src_name = tag.audio["name"].replace("#", "_")
			tag.audio["src"] = f"{src_name}.mp3"

	elif not link_is_url(href):
		tag["href"] = f"x-dictionary:d:{href}"


def _prepare_onclick(soup: BeautifulSoup.BeautifulSoup) -> None:
	for thumb in soup.find_all("div", "pic_thumb"):
		thumb["onclick"] = (
			'this.setAttribute("style", "display:none"); '
			'this.nextElementSibling.setAttribute("style", "display:block")'
		)

	for pic in soup.find_all("div", "big_pic"):
		pic["onclick"] = (
			'this.setAttribute("style", "display:none"), '
			'this.previousElementSibling.setAttribute("style", "display:block")'
		)

	# to unfold(expand) and fold(collapse) blocks
	for pos in soup.find_all("pos", onclick="toggle_infl(this)"):
		# TODO: simplify this!
		pos["onclick"] = (
			r"var e = this.parentElement.parentElement.parentElement"
			r'.querySelector("res-g vp-gs"); style = window.'
			r"getComputedStyle(e), display = style.getPropertyValue"
			r'("display"), "none" === e.style.display || "none" === display'
			r' ? e.style.display = "block" : e.style.display = "none", '
			r"this.className.match(/(?:^|\s)Clicked(?!\S)/) ? this."
			r"className = this.className.replace("
			r'/(?:^|\s)Clicked(?!\S)/g, "") : this.setAttribute('
			r'"class", "Clicked")'
		)


# TODO: PLR0912 Too many branches (18 > 12)
def prepare_content_with_soup(  # noqa: PLR0912
	title: str | None,
	body: str,
	BeautifulSoup: BeautifulSoup,
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
		tag.name = old_tag_name[len("xhtml:") :]
		if tag.string:
			tag.string = f"{tag.string} "

	for tag in soup.select("[href]"):
		_prepare_href(tag)

	_prepare_onclick(soup)

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
		h1 = BeautifulSoup.Tag(name="h1")  # type: ignore
		h1.string = title
		soup.insert(0, h1)

	# hence the name BeautifulSoup
	# soup.insert(0, head)
	return toStr(soup.encode_contents())


def cleanup_link_target(href: str) -> str:
	return href.removeprefix("bword://")


def href_sub(x: re.Match) -> str:
	href = x.groups()[1]
	if href.startswith("http"):
		return x.group()

	href = cleanup_link_target(href)

	return "href=" + quoteattr(
		"x-dictionary:d:"
		+ unescape(
			href,
			{"&quot;": '"'},
		),
	)


def is_green(x: dict) -> bool:
	return "color:green" in x.get("style", "")


def remove_style(tag: dict, line: str) -> None:
	s = "".join(tag["style"].replace(line, "").split(";"))
	if s:
		tag["style"] = s
	else:
		del tag["style"]


def fix_sound_link(href: str, tag: dict[str, Any]) -> None:
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
