import unicodedata
from collections import namedtuple

WritingSystem = namedtuple("WritingSystem", [
	"name",
	"unicode",
	"titleTag",
])

# digits and FULLWIDTH DIGITs are considered neutral/ignored, not Latin

writingSystemList = [
	WritingSystem(
		name="Latin",
		unicode=[
			"LATIN",
			"FULLWIDTH LATIN",
		],
		titleTag="b",
	),

	WritingSystem(
		name="Cyrillic",
		unicode=["CYRILLIC"],
		titleTag="b",
	),

	WritingSystem(
		name="Arabic",
		unicode=["ARABIC"],
		titleTag="b",
	),

	WritingSystem(
		name="CJK",
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
		name="Bengali-Assamese",
		unicode=["BENGALI"],
		titleTag="big",
	),
	WritingSystem(
		name="Hebrew",
		unicode=["HEBREW"],
		titleTag="big",
	),
	WritingSystem(name="Greek", unicode=["GREEK"], titleTag="big"),
	WritingSystem(name="Armenian", unicode=["ARMENIAN"], titleTag="big"),
	WritingSystem(name="Devanagari", unicode=["DEVANAGARI"], titleTag="big"),
	WritingSystem(name="Gujarati", unicode=["GUJARATI"], titleTag="big"),
	WritingSystem(name="Gurmukhi", unicode=["GURMUKHI"], titleTag="big"),
	WritingSystem(name="Adlam", unicode=["ADLAM"], titleTag="big"),
	WritingSystem(name="Georgian", unicode=["GEORGIAN"], titleTag="big"),

	# https://en.wikipedia.org/wiki/Ge%CA%BDez_script
	WritingSystem(name="Ge'ez", unicode=["ETHIOPIC"], titleTag="big"),

	WritingSystem(name="Javanese", unicode=["JAVANESE"], titleTag="big"),
	WritingSystem(name="Kannada", unicode=["KANNADA"], titleTag="big"),
	WritingSystem(name="Khmer", unicode=["KHMER"], titleTag="big"),
	WritingSystem(name="Khojki", unicode=["KHOJKI"], titleTag="big"),
	WritingSystem(name="Khudabadi", unicode=["KHUDAWADI"], titleTag="big"),
	WritingSystem(name="Lao", unicode=["LAO"], titleTag="big"),
	WritingSystem(name="Malayalam", unicode=["MALAYALAM"], titleTag="big"),
	WritingSystem(name="Mongolian", unicode=["MONGOLIAN"], titleTag="big"),
	WritingSystem(name="Burmese", unicode=["MYANMAR"], titleTag="big"),
	WritingSystem(name="N'Ko", unicode=["NKO"], titleTag="big"),
	WritingSystem(name="Odia", unicode=["ORIYA"], titleTag="big"),
	WritingSystem(name="Rejang", unicode=["REJANG"], titleTag="big"),
	WritingSystem(name="Sinhala", unicode=["SINHALA"], titleTag="big"),
	WritingSystem(name="Sundanese", unicode=["SUNDANESE"], titleTag="big"),

	# Parent scripts: Brahmi, Tamil-Brahmi, Pallava
	WritingSystem(name="Tamil", unicode=["TAMIL"], titleTag="big"),

	WritingSystem(name="Telugu", unicode=["TELUGU"], titleTag="big"),
	WritingSystem(name="Thaana", unicode=["THAANA"], titleTag="big"),
	WritingSystem(name="Thai", unicode=["THAI"], titleTag="big"),
	WritingSystem(name="Tibetan", unicode=["TIBETAN"], titleTag="big"),
	# WritingSystem(name="Baybayin", unicode=["TAGALOG"], titleTag="big"),
	WritingSystem(name="Avestan", unicode=["AVESTAN"], titleTag="b"),
	WritingSystem(name="Bengali", unicode=["BENGALI"], titleTag="b"),
	WritingSystem(name="Glagolitic", unicode=["GLAGOLITIC"], titleTag="b"),
	WritingSystem(name="Takri", unicode=["TAKRI"], titleTag="b"),
	# WritingSystem(name="Mwangwego", unicode=[], titleTag="b"),

	WritingSystem(
		name="Canadian syllabic",
		unicode=["CANADIAN SYLLABICS"],
		titleTag="big",
	),
]

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
