import unicodedata
from collections import namedtuple

WritingSystem = namedtuple(
	"WritingSystem", [
		"name",
		"iso",
		"unicode",
		"titleTag",
		"direction",  # ltr | rtl | ttb
		"comma",
		"pop",  # population in millions
	],
	defaults=(
		None,  # name
		None,  # iso
		[],  # unicode
		"b",  # titleTag
		"ltr",  # direction
		", ",  # comma
		0,  # pop
	),
)

# digits and FULLWIDTH DIGITs are considered neutral/ignored, not Latin

# scripts are separated into multiple groups based on their popularity
# (usage in multiple live languages, and number of native speakers)

writingSystemList = [
	WritingSystem(
		name="Latin",
		iso=(215, "Latn"),
		unicode=[
			"LATIN",
		],
		titleTag="b",
		comma=", ",
		pop=4900,
	),

	WritingSystem(
		name="Arabic",
		iso=(160, "Arab"),
		unicode=["ARABIC"],
		titleTag="b",
		direction="rtl",
		comma="، ",
		pop=670,
	),
	WritingSystem(
		name="Cyrillic",
		# iso=(220, "Cyrl"),
		unicode=["CYRILLIC"],
		titleTag="b",
		comma=", ",
		pop=250,
	),
	WritingSystem(
		name="CJK",
		# iso: 286=Hang, 500=Hani, 410=Hira, 412=Hrkt, 411=Kana,
		# 501=Hans, 502=Hant
		unicode=[
			"CJK",
			"HIRAGANA",
			"KATAKANA",
			"IDEOGRAPHIC",  # Ideographic Description Characters
			"DITTO",  # Ditto mark
			"HANGUL",  # Korean alphabet
			"HALFWIDTH KATAKANA",
			"HALFWIDTH HANGUL",
			"YI",  # https://en.wikipedia.org/wiki/Yi_script
			"FULLWIDTH LATIN",
		],
		titleTag="big",
		comma="、",
		pop=1540,  # Chinese=1340, Kana=120, Hangul=78.7
	),
	WritingSystem(
		name="Devanagari",
		# iso=(315 , "Deva"),
		unicode=["DEVANAGARI"],
		titleTag="big",
		comma=", ",
		pop=610,
	),

	# _____________________________________________________

	WritingSystem(
		name="Armenian",
		iso=(230, "Armn"),
		unicode=["ARMENIAN"],
		titleTag="big",
		comma=", ",
		pop=12,
	),
	WritingSystem(
		name="Bengali-Assamese",
		iso=(325, "Beng"),
		unicode=["BENGALI"],
		titleTag="big",
		comma=", ",
		pop=270,
	),
	WritingSystem(
		name="Burmese",
		iso=(350, "Mymr"),
		unicode=["MYANMAR"],
		titleTag="big",
		comma=", ",  # almost not used except in English phrases
		pop=39,
	),
	WritingSystem(
		name="Ge'ez",
		iso=(430, "Ethi"),
		unicode=["ETHIOPIC"],
		titleTag="big",
		comma=", ",
		pop=21,
	),
	WritingSystem(
		name="Greek",
		iso=(200, "Grek"),
		unicode=["GREEK"],
		titleTag="big",
		comma=", ",
		pop=11,
	),
	WritingSystem(
		name="Gujarati",
		iso=(320, "Gujr"),
		unicode=["GUJARATI"],
		titleTag="big",
		comma=", ",
		pop=48,
	),
	WritingSystem(
		name="Gurmukhi",
		iso=(310, "Guru"),
		unicode=["GURMUKHI"],
		titleTag="big",
		comma=", ",
		pop=22,
	),
	WritingSystem(
		name="Hebrew",
		iso=(125, "Hebr"),
		unicode=["HEBREW"],
		titleTag="big",
		direction="rtl",
		comma=", ",
		pop=14,
	),
	WritingSystem(
		name="Kannada",
		iso=(345, "Knda"),
		unicode=["KANNADA"],
		titleTag="big",
		comma=", ",
		pop=45,
	),
	WritingSystem(
		name="Khmer",
		iso=(355, "Khmr"),
		unicode=["KHMER"],
		titleTag="big",
		comma=", ",
		pop=11.4,
	),
	WritingSystem(
		name="Lao",
		iso=(356, "Laoo"),
		unicode=["LAO"],
		titleTag="big",
		comma=", ",
		pop=22,
	),
	WritingSystem(
		name="Malayalam",
		iso=(347, "Mlym"),
		unicode=["MALAYALAM"],
		titleTag="big",
		comma=", ",
		pop=38,
	),
	WritingSystem(
		name="Odia",
		iso=(327, "Orya"),
		unicode=["ORIYA"],
		titleTag="big",
		comma=", ",
		pop=21,
	),
	WritingSystem(
		name="Sinhala",
		iso=(348, "Sinh"),
		unicode=["SINHALA"],
		titleTag="big",
		comma=", ",
		pop=14.4,
	),
	WritingSystem(
		name="Sundanese",
		iso=(362, "Sund"),
		unicode=["SUNDANESE"],
		titleTag="big",
		comma=", ",
		pop=38,
	),
	WritingSystem(
		name="Tamil",
		iso=(346, "Taml"),
		unicode=["TAMIL"],
		titleTag="big",
		# Parent scripts: Brahmi, Tamil-Brahmi, Pallava
		comma=", ",
		pop=70,
	),
	WritingSystem(
		name="Telugu",
		iso=(340, "Telu"),
		unicode=["TELUGU"],
		titleTag="big",
		comma=", ",
		pop=74,
	),
	WritingSystem(
		name="Thai",
		iso=(352, "Thai"),
		unicode=["THAI"],
		titleTag="big",
		comma=", ",
		pop=38,
	),

	# _____________________________________________________

	WritingSystem(
		name="Syriac",
		iso=(135, "Syrc"),
		unicode=["SYRIAC"],
		titleTag="b",
		direction="rtl",
		comma="، ",
		pop=8,  # Syriac=0.4, Lontara=7.6
		# Lontara is a separate script according to Wikipedia
		# but not according to Unicode
	),
	WritingSystem(
		name="Tibetan",
		iso=(330, "Tibt"),
		unicode=["TIBETAN"],
		titleTag="big",
		comma=", ",  # almost not used expect in numbers!
		pop=5,
	),
	WritingSystem(
		name="Georgian",
		iso=(240, "Geor"),
		unicode=["GEORGIAN"],
		titleTag="big",
		comma=", ",
		pop=4.5,
	),
	WritingSystem(
		name="Mongolian",
		iso=(145, "Mong"),
		unicode=["MONGOLIAN"],
		titleTag="big",
		direction="ltr",  # historically ttb?
		comma=", ",
		pop=2,
	),
	WritingSystem(
		name="Thaana",
		iso=(170, "Thaa"),
		unicode=["THAANA"],
		titleTag="big",
		direction="rtl",
		comma="، ",
		pop=0.35,
	),

	# _____________________________________________________

	WritingSystem(
		name="Javanese",
		iso=(361, "Java"),
		unicode=["JAVANESE"],
		titleTag="big",
		# Since around 1945 Javanese script has largely been
		# supplanted by Latin script to write Javanese.
	),
	WritingSystem(
		name="Canadian syllabic",
		iso=(440, "Cans"),
		unicode=["CANADIAN SYLLABICS"],
		titleTag="big",
		comma=", ",
	),
	WritingSystem(
		name="Takri",
		iso=(321, "Takr"),
		unicode=["TAKRI"],
		titleTag="b",
		# comma="", FIXME
	),

	# _____________________________________________________

	WritingSystem(
		name="SignWriting",
		iso=(95, "Sgnw"),
		unicode=["SIGNWRITING"],
		titleTag="big",
		direction="ttb",
		comma="𝪇",
	),

	# _____________________________________________________

	WritingSystem(
		name="Adlam",
		iso=(166, "Adlm"),
		unicode=["ADLAM"],
		titleTag="big",
		direction="rtl",
	),
	WritingSystem(
		name="Avestan",
		iso=(134, "Avst"),
		unicode=["AVESTAN"],
		titleTag="b",
		direction="rtl",
	),
	WritingSystem(
		name="Glagolitic",
		iso=(225, "Glag"),
		unicode=["GLAGOLITIC"],
		titleTag="b",
	),
	WritingSystem(
		name="Khojki",
		iso=(322, "Khoj"),
		unicode=["KHOJKI"],
		titleTag="big",
	),
	WritingSystem(
		name="Khudabadi",  # aka: "Khudawadi", "Sindhi"
		iso=(318, "Sind"),
		unicode=["KHUDAWADI"],
		titleTag="big",
	),
	WritingSystem(
		name="N'Ko",
		iso=(165, "Nkoo"),
		unicode=["NKO"],
		titleTag="big",
	),

	# _____________________________________________________

	# WritingSystem(
	# 	name="Baybayin",
	# 	unicode=["TAGALOG"],
	# ),
	# WritingSystem(
	# 	name="Rejang",
	# 	unicode=["REJANG"],
	# ),
	# WritingSystem(
	# 	name="Mandombe",
	# 	unicode=[],
	# ),
	# WritingSystem(
	# 	name="Mwangwego",
	# 	unicode=[],
	# ),

]

for ws in writingSystemList:
	if not ws.name:
		raise ValueError(f"empty name in {ws}")

writingSystemByUnicode = {
	uni: ws
	for ws in writingSystemList
	for uni in ws.unicode
}

writingSystemByName = {
	ws.name: ws
	for ws in writingSystemList
}

unicodeNextWord = {
	"HALFWIDTH",
	"FULLWIDTH",
	"CANADIAN",
}


def _getWritingSystemFromText(st: str, start: int, end: int):
	for c in st[start:end]:
		unicodeWords = unicodedata.name(c).split(' ')
		alias = unicodeWords[0]
		ws = writingSystemByUnicode.get(alias)
		if ws:
			return ws
		if alias in unicodeNextWord:
			ws = writingSystemByUnicode.get(" ".join(unicodeWords[:2]))
			if ws:
				return ws


def getWritingSystemFromText(st: str):
	# some special first words in unicodedata.name(c):
	# "RIGHT", "ASTERISK", "MODIFIER"
	k = (len(st) + 1) // 2 - 1
	ws = _getWritingSystemFromText(st, k, len(st))
	if ws:
		return ws
	return _getWritingSystemFromText(st, 0, k)
