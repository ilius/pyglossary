# -*- coding: utf-8 -*-

from __future__ import annotations

import logging
import re

__all__ = ["name2codepoint", "unescape_unicode"]

log = logging.getLogger("pyglossary")

re_entity = re.compile(
	r"&#?\w+;",
)


special_chars = {
	"<",
	">",
	"&",
	'"',
	"'",
	"\xa0",  # "&#160;" or "&nbsp;"
}


# these are not included in html.entities.name2codepoint
name2codepoint_extra = {
	"itilde": 0x0129,  # ĩ
	"utilde": 0x0169,  # ũ
	"uring": 0x016F,  # ů
	"ycirc": 0x0177,  # ŷ
	"wring": 0x1E98,  # ẘ
	"yring": 0x1E99,  # ẙ
	"etilde": 0x1EBD,  # ẽ
	"ygrave": 0x1EF3,  # ỳ
	"ytilde": 0x1EF9,  # ỹ
	"ldash": 0x2013,  # –
	"frac13": 0x2153,  # ⅓
	"xfrac13": 0x2153,  # ⅓
	"frac23": 0x2154,  # ⅔
}


# Use build_name2codepoint_dict function to update this dictionary
name2codepoint = {
	"Aacute": 0x00C1,  # Á
	"aacute": 0x00E1,  # á
	"Acirc": 0x00C2,  # Â
	"acirc": 0x00E2,  # â
	"acute": 0x00B4,  # ´
	"AElig": 0x00C6,  # Æ
	"aelig": 0x00E6,  # æ
	"Agrave": 0x00C0,  # À
	"agrave": 0x00E0,  # à
	"alefsym": 0x2135,  # ℵ
	"Alpha": 0x0391,  # Α
	"alpha": 0x03B1,  # α
	"amp": 0x0026,  # &
	"and": 0x2227,  # ∧
	"ang": 0x2220,  # ∠
	"Aring": 0x00C5,  # Å
	"aring": 0x00E5,  # å
	"asymp": 0x2248,  # ≈
	"Atilde": 0x00C3,  # Ã
	"atilde": 0x00E3,  # ã
	"Auml": 0x00C4,  # Ä
	"auml": 0x00E4,  # ä
	"bdquo": 0x201E,  # „
	"Beta": 0x0392,  # Β
	"beta": 0x03B2,  # β
	"brvbar": 0x00A6,  # ¦
	"bull": 0x2022,  # •
	"cap": 0x2229,  # ∩
	"Ccedil": 0x00C7,  # Ç
	"ccedil": 0x00E7,  # ç
	"cedil": 0x00B8,  # ¸
	"cent": 0x00A2,  # ¢
	"Chi": 0x03A7,  # Χ
	"chi": 0x03C7,  # χ
	"circ": 0x02C6,  # ˆ
	"clubs": 0x2663,  # ♣
	"cong": 0x2245,  # ≅
	"copy": 0x00A9,  # ©
	"crarr": 0x21B5,  # ↵
	"cup": 0x222A,  # ∪
	"curren": 0x00A4,  # ¤
	"Dagger": 0x2021,  # ‡
	"dagger": 0x2020,  # †
	"dArr": 0x21D3,  # ⇓
	"darr": 0x2193,  # ↓
	"deg": 0x00B0,  # °
	"Delta": 0x0394,  # Δ
	"delta": 0x03B4,  # δ
	"diams": 0x2666,  # ♦
	"divide": 0x00F7,  # ÷
	"Eacute": 0x00C9,  # É
	"eacute": 0x00E9,  # é
	"Ecirc": 0x00CA,  # Ê
	"ecirc": 0x00EA,  # ê
	"Egrave": 0x00C8,  # È
	"egrave": 0x00E8,  # è
	"empty": 0x2205,  # ∅
	"emsp": 0x2003,
	"ensp": 0x2002,
	"Epsilon": 0x0395,  # Ε
	"epsilon": 0x03B5,  # ε
	"equiv": 0x2261,  # ≡
	"Eta": 0x0397,  # Η
	"eta": 0x03B7,  # η
	"ETH": 0x00D0,  # Ð
	"eth": 0x00F0,  # ð
	"etilde": 0x1EBD,  # ẽ
	"Euml": 0x00CB,  # Ë
	"euml": 0x00EB,  # ë
	"euro": 0x20AC,  # €
	"exist": 0x2203,  # ∃
	"fnof": 0x0192,  # ƒ
	"forall": 0x2200,  # ∀
	"frac12": 0x00BD,  # ½
	"frac13": 0x2153,  # ⅓
	"frac14": 0x00BC,  # ¼
	"frac23": 0x2154,  # ⅔
	"frac34": 0x00BE,  # ¾
	"frasl": 0x2044,  # ⁄
	"Gamma": 0x0393,  # Γ
	"gamma": 0x03B3,  # γ
	"ge": 0x2265,  # ≥
	"gt": 0x003E,  # >
	"hArr": 0x21D4,  # ⇔
	"harr": 0x2194,  # ↔
	"hearts": 0x2665,  # ♥
	"hellip": 0x2026,  # …
	"Iacute": 0x00CD,  # Í
	"iacute": 0x00ED,  # í
	"Icirc": 0x00CE,  # Î
	"icirc": 0x00EE,  # î
	"iexcl": 0x00A1,  # ¡
	"Igrave": 0x00CC,  # Ì
	"igrave": 0x00EC,  # ì
	"image": 0x2111,  # ℑ
	"infin": 0x221E,  # ∞
	"int": 0x222B,  # ∫
	"Iota": 0x0399,  # Ι
	"iota": 0x03B9,  # ι
	"iquest": 0x00BF,  # ¿
	"isin": 0x2208,  # ∈
	"itilde": 0x0129,  # ĩ
	"Iuml": 0x00CF,  # Ï
	"iuml": 0x00EF,  # ï
	"Kappa": 0x039A,  # Κ
	"kappa": 0x03BA,  # κ
	"Lambda": 0x039B,  # Λ
	"lambda": 0x03BB,  # λ
	"lang": 0x2329,  # 〈
	"laquo": 0x00AB,  # «
	"lArr": 0x21D0,  # ⇐
	"larr": 0x2190,  # ←
	"lceil": 0x2308,  # ⌈
	"ldash": 0x2013,  # –
	"ldquo": 0x201C,  # “
	"le": 0x2264,  # ≤
	"lfloor": 0x230A,  # ⌊
	"lowast": 0x2217,  # ∗
	"loz": 0x25CA,  # ◊
	"lrm": 0x200E,  # ‎
	"lsaquo": 0x2039,  # ‹
	"lsquo": 0x2018,  # ‘
	"lt": 0x003C,  # <
	"macr": 0x00AF,  # ¯
	"mdash": 0x2014,  # —
	"micro": 0x00B5,  # µ
	"middot": 0x00B7,  # ·
	"minus": 0x2212,  # −
	"Mu": 0x039C,  # Μ
	"mu": 0x03BC,  # μ
	"nabla": 0x2207,  # ∇
	"nbsp": 0x00A0,  # space
	"ndash": 0x2013,  # –
	"ne": 0x2260,  # ≠
	"ni": 0x220B,  # ∋
	"not": 0x00AC,  # ¬
	"notin": 0x2209,  # ∉
	"nsub": 0x2284,  # ⊄
	"Ntilde": 0x00D1,  # Ñ
	"ntilde": 0x00F1,  # ñ
	"Nu": 0x039D,  # Ν
	"nu": 0x03BD,  # ν
	"Oacute": 0x00D3,  # Ó
	"oacute": 0x00F3,  # ó
	"Ocirc": 0x00D4,  # Ô
	"ocirc": 0x00F4,  # ô
	"OElig": 0x0152,  # Œ
	"oelig": 0x0153,  # œ
	"Ograve": 0x00D2,  # Ò
	"ograve": 0x00F2,  # ò
	"oline": 0x203E,  # ‾
	"Omega": 0x03A9,  # Ω
	"omega": 0x03C9,  # ω
	"Omicron": 0x039F,  # Ο
	"omicron": 0x03BF,  # ο
	"oplus": 0x2295,  # ⊕
	"or": 0x2228,  # ∨
	"ordf": 0x00AA,  # ª
	"ordm": 0x00BA,  # º
	"Oslash": 0x00D8,  # Ø
	"oslash": 0x00F8,  # ø
	"Otilde": 0x00D5,  # Õ
	"otilde": 0x00F5,  # õ
	"otimes": 0x2297,  # ⊗
	"Ouml": 0x00D6,  # Ö
	"ouml": 0x00F6,  # ö
	"para": 0x00B6,  # ¶
	"part": 0x2202,  # ∂
	"permil": 0x2030,  # ‰
	"perp": 0x22A5,  # ⊥
	"Phi": 0x03A6,  # Φ
	"phi": 0x03C6,  # φ
	"Pi": 0x03A0,  # Π
	"pi": 0x03C0,  # π
	"piv": 0x03D6,  # ϖ
	"plusmn": 0x00B1,  # ±
	"pound": 0x00A3,  # £
	"Prime": 0x2033,  # ″
	"prime": 0x2032,  # ′
	"prod": 0x220F,  # ∏
	"prop": 0x221D,  # ∝
	"Psi": 0x03A8,  # Ψ
	"psi": 0x03C8,  # ψ
	"quot": 0x0022,  # "
	"radic": 0x221A,  # √
	"rang": 0x232A,  # 〉
	"raquo": 0x00BB,  # »
	"rArr": 0x21D2,  # ⇒
	"rarr": 0x2192,  # →
	"rceil": 0x2309,  # ⌉
	"rdquo": 0x201D,  # ”
	"real": 0x211C,  # ℜ
	"reg": 0x00AE,  # ®
	"rfloor": 0x230B,  # ⌋
	"Rho": 0x03A1,  # Ρ
	"rho": 0x03C1,  # ρ
	"rlm": 0x200F,  # U+200F
	"rsaquo": 0x203A,  # ›
	"rsquo": 0x2019,  # ’
	"sbquo": 0x201A,  # ‚
	"Scaron": 0x0160,  # Š
	"scaron": 0x0161,  # š
	"sdot": 0x22C5,  # ⋅
	"sect": 0x00A7,  # §
	"shy": 0x00AD,  # ­
	"Sigma": 0x03A3,  # Σ
	"sigma": 0x03C3,  # σ
	"sigmaf": 0x03C2,  # ς
	"sim": 0x223C,  # ∼
	"spades": 0x2660,  # ♠
	"sub": 0x2282,  # ⊂
	"sube": 0x2286,  # ⊆
	"sum": 0x2211,  # ∑
	"sup": 0x2283,  # ⊃
	"sup1": 0x00B9,  # ¹
	"sup2": 0x00B2,  # ²
	"sup3": 0x00B3,  # ³
	"supe": 0x2287,  # ⊇
	"szlig": 0x00DF,  # ß
	"Tau": 0x03A4,  # Τ
	"tau": 0x03C4,  # τ
	"there4": 0x2234,  # ∴
	"Theta": 0x0398,  # Θ
	"theta": 0x03B8,  # θ
	"thetasym": 0x03D1,  # ϑ
	"thinsp": 0x2009,
	"THORN": 0x00DE,  # Þ
	"thorn": 0x00FE,  # þ
	"tilde": 0x02DC,  # ˜
	"times": 0x00D7,  # ×
	"trade": 0x2122,  # ™
	"Uacute": 0x00DA,  # Ú
	"uacute": 0x00FA,  # ú
	"uArr": 0x21D1,  # ⇑
	"uarr": 0x2191,  # ↑
	"Ucirc": 0x00DB,  # Û
	"ucirc": 0x00FB,  # û
	"Ugrave": 0x00D9,  # Ù
	"ugrave": 0x00F9,  # ù
	"uml": 0x00A8,  # ¨
	"upsih": 0x03D2,  # ϒ
	"Upsilon": 0x03A5,  # Υ
	"upsilon": 0x03C5,  # υ
	"uring": 0x016F,  # ů
	"utilde": 0x0169,  # ũ
	"Uuml": 0x00DC,  # Ü
	"uuml": 0x00FC,  # ü
	"weierp": 0x2118,  # ℘
	"wring": 0x1E98,  # ẘ
	"xfrac13": 0x2153,  # ⅓
	"Xi": 0x039E,  # Ξ
	"xi": 0x03BE,  # ξ
	"Yacute": 0x00DD,  # Ý
	"yacute": 0x00FD,  # ý
	"ycirc": 0x0177,  # ŷ
	"yen": 0x00A5,  # ¥
	"ygrave": 0x1EF3,  # ỳ
	"yring": 0x1E99,  # ẙ
	"ytilde": 0x1EF9,  # ỹ
	"Yuml": 0x0178,  # Ÿ
	"yuml": 0x00FF,  # ÿ
	"Zeta": 0x0396,  # Ζ
	"zeta": 0x03B6,  # ζ
	"zwj": 0x200D,  # ‍
	"zwnj": 0x200C,  # ‌
}


def build_name2codepoint_dict() -> None:
	"""
	Build name -> codepoint dictionary
	copy and paste the output to the name2codepoint dictionary
	name2str - name to utf-8 string dictionary.
	"""
	import html.entities

	name2str = {}
	for k, v in name2codepoint_extra.items():
		name2str[k] = chr(v)
	for k, v in html.entities.name2codepoint.items():
		name2str[k] = chr(v)
	for key in sorted(name2str, key=lambda s: (s.lower(), s)):
		value = name2str[key]
		if len(value) > 1:
			raise ValueError(f"{value = }")
		print(f'\t"{key}": 0x{ord(value):0>4x},  # {value}')  # noqa: T201


def _sub_unescape_unicode(m: re.Match) -> str:
	text = m.group(0)
	if text[:2] == "&#":
		# character reference
		code = int(text[3:-1], 16) if text.startswith("&#x") else int(text[2:-1])
		try:
			char = chr(code)
		except ValueError:
			return text
		if char not in special_chars:
			return char
		return text

	# named entity
	name = text[1:-1]
	if name in name2codepoint:
		char = chr(name2codepoint[name])
		if char not in special_chars:
			return char

	return text


def unescape_unicode(text: str) -> str:
	"""
	Unscape unicode entities, but not "&lt;", "&gt;" and "&amp;"
	leave these 3 special entities alone, since unescaping them
	creates invalid html
	we also ignore quotations: "&quot;" and "&#x27;".
	"""
	return re_entity.sub(_sub_unescape_unicode, text)


if __name__ == "__main__":
	build_name2codepoint_dict()
