# -*- coding: utf-8 -*-

import re

import logging
log = logging.getLogger("pyglossary")


def toStr(s: "AnyStr") -> str:
	return str(s, "utf-8") if isinstance(s, bytes) else str(s)


re_entity = re.compile(
	r"&#?\w+;",
)


special_chars = {
	"<",
	">",
	"&",
	'"',
	"'",
}


# these are not included in html.entities.name2codepoint
name2codepoint_extra = {
	"itilde": 0x0129,  # ĩ
	"utilde": 0x0169,  # ũ
	"uring": 0x016f,  # ů
	"ycirc": 0x0177,  # ŷ
	"wring": 0x1e98,  # ẘ
	"yring": 0x1e99,  # ẙ
	"etilde": 0x1ebd,  # ẽ
	"ygrave": 0x1ef3,  # ỳ
	"ytilde": 0x1ef9,  # ỹ
	"ldash": 0x2013,  # –
	"frac13": 0x2153,  # ⅓
	"xfrac13": 0x2153,  # ⅓
	"frac23": 0x2154,  # ⅔
}


# Use build_name2codepoint_dict function to update this dictionary
name2codepoint = {
	"Aacute": 0x00c1,  # Á
	"aacute": 0x00e1,  # á
	"Acirc": 0x00c2,  # Â
	"acirc": 0x00e2,  # â
	"acute": 0x00b4,  # ´
	"AElig": 0x00c6,  # Æ
	"aelig": 0x00e6,  # æ
	"Agrave": 0x00c0,  # À
	"agrave": 0x00e0,  # à
	"alefsym": 0x2135,  # ℵ
	"Alpha": 0x0391,  # Α
	"alpha": 0x03b1,  # α
	"amp": 0x0026,  # &
	"and": 0x2227,  # ∧
	"ang": 0x2220,  # ∠
	"Aring": 0x00c5,  # Å
	"aring": 0x00e5,  # å
	"asymp": 0x2248,  # ≈
	"Atilde": 0x00c3,  # Ã
	"atilde": 0x00e3,  # ã
	"Auml": 0x00c4,  # Ä
	"auml": 0x00e4,  # ä
	"bdquo": 0x201e,  # „
	"Beta": 0x0392,  # Β
	"beta": 0x03b2,  # β
	"brvbar": 0x00a6,  # ¦
	"bull": 0x2022,  # •
	"cap": 0x2229,  # ∩
	"Ccedil": 0x00c7,  # Ç
	"ccedil": 0x00e7,  # ç
	"cedil": 0x00b8,  # ¸
	"cent": 0x00a2,  # ¢
	"Chi": 0x03a7,  # Χ
	"chi": 0x03c7,  # χ
	"circ": 0x02c6,  # ˆ
	"clubs": 0x2663,  # ♣
	"cong": 0x2245,  # ≅
	"copy": 0x00a9,  # ©
	"crarr": 0x21b5,  # ↵
	"cup": 0x222a,  # ∪
	"curren": 0x00a4,  # ¤
	"Dagger": 0x2021,  # ‡
	"dagger": 0x2020,  # †
	"dArr": 0x21d3,  # ⇓
	"darr": 0x2193,  # ↓
	"deg": 0x00b0,  # °
	"Delta": 0x0394,  # Δ
	"delta": 0x03b4,  # δ
	"diams": 0x2666,  # ♦
	"divide": 0x00f7,  # ÷
	"Eacute": 0x00c9,  # É
	"eacute": 0x00e9,  # é
	"Ecirc": 0x00ca,  # Ê
	"ecirc": 0x00ea,  # ê
	"Egrave": 0x00c8,  # È
	"egrave": 0x00e8,  # è
	"empty": 0x2205,  # ∅
	"emsp": 0x2003,  #  
	"ensp": 0x2002,  #  
	"Epsilon": 0x0395,  # Ε
	"epsilon": 0x03b5,  # ε
	"equiv": 0x2261,  # ≡
	"Eta": 0x0397,  # Η
	"eta": 0x03b7,  # η
	"ETH": 0x00d0,  # Ð
	"eth": 0x00f0,  # ð
	"etilde": 0x1ebd,  # ẽ
	"Euml": 0x00cb,  # Ë
	"euml": 0x00eb,  # ë
	"euro": 0x20ac,  # €
	"exist": 0x2203,  # ∃
	"fnof": 0x0192,  # ƒ
	"forall": 0x2200,  # ∀
	"frac12": 0x00bd,  # ½
	"frac13": 0x2153,  # ⅓
	"frac14": 0x00bc,  # ¼
	"frac23": 0x2154,  # ⅔
	"frac34": 0x00be,  # ¾
	"frasl": 0x2044,  # ⁄
	"Gamma": 0x0393,  # Γ
	"gamma": 0x03b3,  # γ
	"ge": 0x2265,  # ≥
	"gt": 0x003e,  # >
	"hArr": 0x21d4,  # ⇔
	"harr": 0x2194,  # ↔
	"hearts": 0x2665,  # ♥
	"hellip": 0x2026,  # …
	"Iacute": 0x00cd,  # Í
	"iacute": 0x00ed,  # í
	"Icirc": 0x00ce,  # Î
	"icirc": 0x00ee,  # î
	"iexcl": 0x00a1,  # ¡
	"Igrave": 0x00cc,  # Ì
	"igrave": 0x00ec,  # ì
	"image": 0x2111,  # ℑ
	"infin": 0x221e,  # ∞
	"int": 0x222b,  # ∫
	"Iota": 0x0399,  # Ι
	"iota": 0x03b9,  # ι
	"iquest": 0x00bf,  # ¿
	"isin": 0x2208,  # ∈
	"itilde": 0x0129,  # ĩ
	"Iuml": 0x00cf,  # Ï
	"iuml": 0x00ef,  # ï
	"Kappa": 0x039a,  # Κ
	"kappa": 0x03ba,  # κ
	"Lambda": 0x039b,  # Λ
	"lambda": 0x03bb,  # λ
	"lang": 0x2329,  # 〈
	"laquo": 0x00ab,  # «
	"lArr": 0x21d0,  # ⇐
	"larr": 0x2190,  # ←
	"lceil": 0x2308,  # ⌈
	"ldash": 0x2013,  # –
	"ldquo": 0x201c,  # “
	"le": 0x2264,  # ≤
	"lfloor": 0x230a,  # ⌊
	"lowast": 0x2217,  # ∗
	"loz": 0x25ca,  # ◊
	"lrm": 0x200e,  # ‎
	"lsaquo": 0x2039,  # ‹
	"lsquo": 0x2018,  # ‘
	"lt": 0x003c,  # <
	"macr": 0x00af,  # ¯
	"mdash": 0x2014,  # —
	"micro": 0x00b5,  # µ
	"middot": 0x00b7,  # ·
	"minus": 0x2212,  # −
	"Mu": 0x039c,  # Μ
	"mu": 0x03bc,  # μ
	"nabla": 0x2207,  # ∇
	"nbsp": 0x00a0,  #  
	"ndash": 0x2013,  # –
	"ne": 0x2260,  # ≠
	"ni": 0x220b,  # ∋
	"not": 0x00ac,  # ¬
	"notin": 0x2209,  # ∉
	"nsub": 0x2284,  # ⊄
	"Ntilde": 0x00d1,  # Ñ
	"ntilde": 0x00f1,  # ñ
	"Nu": 0x039d,  # Ν
	"nu": 0x03bd,  # ν
	"Oacute": 0x00d3,  # Ó
	"oacute": 0x00f3,  # ó
	"Ocirc": 0x00d4,  # Ô
	"ocirc": 0x00f4,  # ô
	"OElig": 0x0152,  # Œ
	"oelig": 0x0153,  # œ
	"Ograve": 0x00d2,  # Ò
	"ograve": 0x00f2,  # ò
	"oline": 0x203e,  # ‾
	"Omega": 0x03a9,  # Ω
	"omega": 0x03c9,  # ω
	"Omicron": 0x039f,  # Ο
	"omicron": 0x03bf,  # ο
	"oplus": 0x2295,  # ⊕
	"or": 0x2228,  # ∨
	"ordf": 0x00aa,  # ª
	"ordm": 0x00ba,  # º
	"Oslash": 0x00d8,  # Ø
	"oslash": 0x00f8,  # ø
	"Otilde": 0x00d5,  # Õ
	"otilde": 0x00f5,  # õ
	"otimes": 0x2297,  # ⊗
	"Ouml": 0x00d6,  # Ö
	"ouml": 0x00f6,  # ö
	"para": 0x00b6,  # ¶
	"part": 0x2202,  # ∂
	"permil": 0x2030,  # ‰
	"perp": 0x22a5,  # ⊥
	"Phi": 0x03a6,  # Φ
	"phi": 0x03c6,  # φ
	"Pi": 0x03a0,  # Π
	"pi": 0x03c0,  # π
	"piv": 0x03d6,  # ϖ
	"plusmn": 0x00b1,  # ±
	"pound": 0x00a3,  # £
	"Prime": 0x2033,  # ″
	"prime": 0x2032,  # ′
	"prod": 0x220f,  # ∏
	"prop": 0x221d,  # ∝
	"Psi": 0x03a8,  # Ψ
	"psi": 0x03c8,  # ψ
	"quot": 0x0022,  # "
	"radic": 0x221a,  # √
	"rang": 0x232a,  # 〉
	"raquo": 0x00bb,  # »
	"rArr": 0x21d2,  # ⇒
	"rarr": 0x2192,  # →
	"rceil": 0x2309,  # ⌉
	"rdquo": 0x201d,  # ”
	"real": 0x211c,  # ℜ
	"reg": 0x00ae,  # ®
	"rfloor": 0x230b,  # ⌋
	"Rho": 0x03a1,  # Ρ
	"rho": 0x03c1,  # ρ
	"rlm": 0x200f,  # ‏
	"rsaquo": 0x203a,  # ›
	"rsquo": 0x2019,  # ’
	"sbquo": 0x201a,  # ‚
	"Scaron": 0x0160,  # Š
	"scaron": 0x0161,  # š
	"sdot": 0x22c5,  # ⋅
	"sect": 0x00a7,  # §
	"shy": 0x00ad,  # ­
	"Sigma": 0x03a3,  # Σ
	"sigma": 0x03c3,  # σ
	"sigmaf": 0x03c2,  # ς
	"sim": 0x223c,  # ∼
	"spades": 0x2660,  # ♠
	"sub": 0x2282,  # ⊂
	"sube": 0x2286,  # ⊆
	"sum": 0x2211,  # ∑
	"sup": 0x2283,  # ⊃
	"sup1": 0x00b9,  # ¹
	"sup2": 0x00b2,  # ²
	"sup3": 0x00b3,  # ³
	"supe": 0x2287,  # ⊇
	"szlig": 0x00df,  # ß
	"Tau": 0x03a4,  # Τ
	"tau": 0x03c4,  # τ
	"there4": 0x2234,  # ∴
	"Theta": 0x0398,  # Θ
	"theta": 0x03b8,  # θ
	"thetasym": 0x03d1,  # ϑ
	"thinsp": 0x2009,  #  
	"THORN": 0x00de,  # Þ
	"thorn": 0x00fe,  # þ
	"tilde": 0x02dc,  # ˜
	"times": 0x00d7,  # ×
	"trade": 0x2122,  # ™
	"Uacute": 0x00da,  # Ú
	"uacute": 0x00fa,  # ú
	"uArr": 0x21d1,  # ⇑
	"uarr": 0x2191,  # ↑
	"Ucirc": 0x00db,  # Û
	"ucirc": 0x00fb,  # û
	"Ugrave": 0x00d9,  # Ù
	"ugrave": 0x00f9,  # ù
	"uml": 0x00a8,  # ¨
	"upsih": 0x03d2,  # ϒ
	"Upsilon": 0x03a5,  # Υ
	"upsilon": 0x03c5,  # υ
	"uring": 0x016f,  # ů
	"utilde": 0x0169,  # ũ
	"Uuml": 0x00dc,  # Ü
	"uuml": 0x00fc,  # ü
	"weierp": 0x2118,  # ℘
	"wring": 0x1e98,  # ẘ
	"xfrac13": 0x2153,  # ⅓
	"Xi": 0x039e,  # Ξ
	"xi": 0x03be,  # ξ
	"Yacute": 0x00dd,  # Ý
	"yacute": 0x00fd,  # ý
	"ycirc": 0x0177,  # ŷ
	"yen": 0x00a5,  # ¥
	"ygrave": 0x1ef3,  # ỳ
	"yring": 0x1e99,  # ẙ
	"ytilde": 0x1ef9,  # ỹ
	"Yuml": 0x0178,  # Ÿ
	"yuml": 0x00ff,  # ÿ
	"Zeta": 0x0396,  # Ζ
	"zeta": 0x03b6,  # ζ
	"zwj": 0x200d,  # ‍
	"zwnj": 0x200c,  # ‌
}


def build_name2codepoint_dict():
	"""
		Builds name to codepoint dictionary
		copy and paste the output to the name2codepoint dictionary
		name2str - name to utf-8 string dictionary
	"""
	import html.entities
	name2str = {}
	for k, v in name2codepoint_extra.items():
		name2str[k] = chr(v)
	for k, v in html.entities.name2codepoint.items():
		name2str[k] = chr(v)
	for key in sorted(name2str.keys(), key=lambda s: (s.lower(), s)):
		value = name2str[key]
		if len(value) > 1:
			raise ValueError(f"value = {value!r}")
		print(f"\t\"{key}\": 0x{ord(value):0>4x},  # {value}")


def _sub_unescape_unicode(m: "re.Match") -> str:
	text = m.group(0)
	if text[:2] == "&#":
		# character reference
		if text.startswith("&#x"):
			code = int(text[3:-1], 16)
		else:
			code = int(text[2:-1])
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


def unescape_unicode(text):
	"""
		unscape unicode entities, but not "&lt;", "&gt;" and "&amp;"
		leave these 3 special entities alone, since unscaping them
		creates invalid html
		we also ignore quotations: "&quot;" and "&#x27;"
	"""
	return re_entity.sub(_sub_unescape_unicode, text)


if __name__ == "__main__":
	build_name2codepoint_dict()
