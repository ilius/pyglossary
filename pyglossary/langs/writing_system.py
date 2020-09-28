import unicodedata
from collections import namedtuple

WritingSystem = namedtuple(
	"WritingSystem", [
		"name",
		"iso",
		"unicode",
		"titleTag",
		"direction",  # ltr | rtl | ttb
	],
	defaults=(
		None,  # name
		None,  # iso
		[],  # unicode
		"b",  # titleTag
		"ltr",  # direction
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
			"FULLWIDTH LATIN",
		],
		titleTag="b",
	),

	WritingSystem(
		name="Arabic",
		iso=(160, "Arab"),
		unicode=["ARABIC"],
		titleTag="b",
		direction="rtl",
	),
	WritingSystem(
		name="Cyrillic",
		# iso=(220, "Cyrl"),
		unicode=["CYRILLIC"],
		titleTag="b",
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
		],
		titleTag="big",
	),
	WritingSystem(
		name="Devanagari",
		# iso=(315 , "Deva"),
		unicode=["DEVANAGARI"],
		titleTag="big",
	),

	# _____________________________________________________

	WritingSystem(
		name="Armenian",
		iso=(230, "Armn"),
		unicode=["ARMENIAN"],
		titleTag="big",
	),
	WritingSystem(
		name="Bengali-Assamese",
		iso=(325, "Beng"),
		unicode=["BENGALI"],
		titleTag="big",
	),
	WritingSystem(
		name="Burmese",
		iso=(350 , "Mymr"),
		unicode=["MYANMAR"],
		titleTag="big",
	),
	WritingSystem(
		name="Canadian syllabic",
		iso=(440, "Cans"),
		unicode=["CANADIAN SYLLABICS"],
		titleTag="big",
	),
	WritingSystem(
		name="Ge'ez",
		iso=(430, "Ethi"),
		unicode=["ETHIOPIC"],
		titleTag="big",
	),
	WritingSystem(
		name="Georgian",
		iso=(240, "Geor"),
		unicode=["GEORGIAN"],
		titleTag="big",
	),
	WritingSystem(
		name="Greek",
		iso=(200, "Grek"),
		unicode=["GREEK"],
		titleTag="big",
	),
	WritingSystem(
		name="Gujarati",
		iso=(320, "Gujr"),
		unicode=["GUJARATI"],
		titleTag="big",
	),
	WritingSystem(
		name="Gurmukhi",
		iso=(310, "Guru"),
		unicode=["GURMUKHI"],
		titleTag="big",
	),
	WritingSystem(
		name="Hebrew",
		iso=(125, "Hebr"),
		unicode=["HEBREW"],
		titleTag="big",
		direction="rtl",
	),
	WritingSystem(
		name="Kannada",
		iso=(345, "Knda"),
		unicode=["KANNADA"],
		titleTag="big",
	),
	WritingSystem(
		name="Khmer",
		iso=(355, "Khmr"),
		unicode=["KHMER"],
		titleTag="big",
	),
	WritingSystem(
		name="Lao",
		iso=(356, "Laoo"),
		unicode=["LAO"],
		titleTag="big",
	),
	WritingSystem(
		name="Malayalam",
		iso=(347, "Mlym"),
		unicode=["MALAYALAM"],
		titleTag="big",
	),
	WritingSystem(
		name="Mongolian",
		iso=(145, "Mong"),
		unicode=["MONGOLIAN"],
		titleTag="big",
		direction="ttb",
	),
	WritingSystem(
		name="Odia",
		iso=(327, "Orya"),
		unicode=["ORIYA"],
		titleTag="big",
	),
	WritingSystem(
		name="Sinhala",
		iso=(348, "Sinh"),
		unicode=["SINHALA"],
		titleTag="big",
	),
	WritingSystem(
		name="Sundanese",
		iso=(362, "Sund"),
		unicode=["SUNDANESE"],
		titleTag="big",
	),
	WritingSystem(
		name="Tamil",
		iso=(346, "Taml"),
		unicode=["TAMIL"],
		titleTag="big",
		# Parent scripts: Brahmi, Tamil-Brahmi, Pallava
	),
	WritingSystem(
		name="Telugu",
		iso=(340, "Telu"),
		unicode=["TELUGU"],
		titleTag="big",
	),
	WritingSystem(
		name="Thai",
		iso=(352, "Thai"),
		unicode=["THAI"],
		titleTag="big",
	),
	WritingSystem(
		name="Tibetan",
		iso=(330, "Tibt"),
		unicode=["TIBETAN"],
		titleTag="big",
	),

	# _____________________________________________________

	WritingSystem(
		name="Takri",
		iso=(321, "Takr"),
		unicode=["TAKRI"],
		titleTag="b",
	),
	WritingSystem(
		name="Thaana",
		iso=(170, "Thaa"),
		unicode=["THAANA"],
		titleTag="big",
		direction="rtl",
	),

	# _____________________________________________________

	WritingSystem(
		name="SignWriting",
		iso=(95, "Sgnw"),
		unicode=["SIGNWRITING"],
		titleTag="big",
		direction="ttb",
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
		name="Javanese",
		iso=(361, "Java"),
		unicode=["JAVANESE"],
		titleTag="big",
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
	#	name="Baybayin",
	#	unicode=["TAGALOG"],
	# ),
	# WritingSystem(
	#	name="Rejang",
	#	unicode=["REJANG"],
	# ),
	# WritingSystem(
	#	name="Mandombe",
	#	unicode=[],
	# ),
	# WritingSystem(
	#	name="Mwangwego",
	#	unicode=[],
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


def getWritingSystemFromText(st: str):
	# some special first words in unicodedata.name(c):
	# "RIGHT", "ASTERISK", "MODIFIER"
	k = (len(st) + 1) // 2 - 1
	for c in st[k:]:
		unicodeWords = unicodedata.name(c).split(' ')
		alias = unicodeWords[0]
		ws = writingSystemByUnicode.get(alias)
		if ws:
			return ws
		if alias in unicodeNextWord:
			ws = writingSystemByUnicode.get(" ".join(unicodeWords[:2]))
			if ws:
				return ws
