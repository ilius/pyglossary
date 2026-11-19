import sys
import unittest
from os.path import abspath, dirname

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from lxml import etree as ET

from pyglossary.xdxf.py_transform import XdxfTransformer

# (name, inner XDXF markup, expected HTML).
# Cover issue #562 (spaces around tags), issue #532 (spaces before kref,
# newline rendering, indents, padded <ex>) and other tag handling.
SAMPLES = [
	(
		"issue562",  # issue #562: spaces between tags preserved
		(
			"<k>grzebiący</k><def> <def> <pos>прич. от</pos> <b>grzebać</b>; "
			"</def><def><co> grzebiące, grzebiących</co> <pos>мн. зоол.</pos> "
			"кури́ные <pos>lm</pos> (Galliformes) </def></def>"
		),
		(
			'<div class="article"><div class="k"><b>grzebiący</b></div>'
			'<ul><li><span class="pos"><font color="green"><i>прич. от</i>'
			"</font></span> <b>grzebać</b>; </li>"
			'<li><span class="co">(grzebiące, grzebiących)</span> '
			'<span class="pos"><font color="green"><i>мн. зоол.</i>'
			'</font></span> кури́ные <span class="pos">'
			'<font color="green"><i>lm</i></font></span>'
			" (Galliformes) </li></ul></div>"
		),
	),
	(
		"kref_spaces",  # issue #532: spaces before/after kref preserved
		(
			"<k>cross-reference</k>\n<dtrn>see <kref>other</kref> here and "
			'<kref k="target word">target</kref></dtrn>'
		),
		(
			'<div class="article"><div class="k"><b>cross-reference</b></div>'
			'see <a class="kref" href="bword://other">other</a> here and '
			'<a class="kref" href="bword://target%20word">target</a></div>'
		),
	),
	(
		"newlines",  # issue #532: newlines render as line breaks
		"<k>newlines</k>\n<abr>noun</abr>\n<dtrn>line one\nline two\n\nline four</dtrn>",
		(
			'<div class="article"><div class="k"><b>newlines</b></div>'
			'<span class="abr"><font color="green"><i>noun</i></font></span>'
			"<br/>line one<br/>line two<br/>line four</div>"
		),
	),
	(
		"lingvo_entry",  # issue #532: Lingvo-style entry with numbered defs, padded examples
		(
			"<k>abstinence</k>\n<tr>ˈæbstɪnən(t)s</tr> \n <abr>сущ.</abr>\n"
			" 1) <c><dtrn><co>= abstention</co></dtrn></c>\n"
			"  а) <dtrn>воздержание; умеренность</dtrn>\n"
			"   <ex>abstinence from meat — вегетарианство</ex>\n"
			" 2) <dtrn><abr>рел.</abr> соблюдение поста, пост</dtrn>\n"
			"  <ex>day of abstinence — постный день</ex>"
		),
		(
			'<div class="article"><div class="k"><b>abstinence</b></div>'
			'[ˈæbstɪnən(t)s]<br/><span class="abr"><font color="green">'
			"<i>сущ.</i></font></span><br/> 1) "
			'<font color="green"><span class="co">(= abstention)</span></font>'
			"<br/>  а) воздержание; умеренность<br/>   "
			'<div class="example" style="padding: 10px 0px;">'
			"abstinence from meat — вегетарианство</div>"
			"2) "
			'<span class="abr"><font color="green"><i>рел.</i></font></span> '
			"соблюдение поста, пост<br/>  "
			'<div class="example" style="padding: 10px 0px;">'
			"day of abstinence — постный день</div></div>"
		),
	),
	(
		"ex_orig_tran",  # issue #532: <ex> padded, ex_orig/ex_tran inline
		(
			"<k>example</k>\n<dtrn>definition text</dtrn>\n"
			"<ex>Пример <ex_orig>original</ex_orig> <ex_tran>translation</ex_tran></ex>"
		),
		(
			'<div class="article"><div class="k"><b>example</b></div>'
			"definition text<br/>"
			'<div class="example" style="padding: 10px 0px;">'
			"Пример <i>original</i> <i>translation</i></div></div>"
		),
	),
	(
		"nested_defs",  # 2 nested <def> elements render as an unordered list
		"<k>polysemy</k><def><def>first meaning</def><def>second meaning</def></def>",
		(
			'<div class="article"><div class="k"><b>polysemy</b></div>'
			"<ul><li>first meaning</li><li>second meaning</li></ul></div>"
		),
	),
	(
		"nested_defs_three",  # 3 nested <def> elements render as a numbered list
		("<k>polysemy</k><def><def>first</def><def>second</def><def>third</def></def>"),
		(
			'<div class="article"><div class="k"><b>polysemy</b></div>'
			"<ol><li>first</li><li>second</li><li>third</li></ol></div>"
		),
	),
	(
		"nested_defs_deep",  # 2 nested <def> elements at every level
		"<k>deep</k><def><def><def>a</def><def>b</def></def><def>c</def></def>",
		(
			'<div class="article"><div class="k"><b>deep</b></div>'
			"<ul><li><ul><li>a</li><li>b</li></ul></li><li>c</li></ul></div>"
		),
	),
	(
		"single_def",  # single <def> renders as a block
		"<k>single</k><def>one meaning only</def>",
		(
			'<div class="article"><div class="k"><b>single</b></div>'
			"<div>one meaning only</div></div>"
		),
	),
	(
		"transcription",  # transcription in brackets, <c>/<co>/<abr> inline formatting
		(
			"<k>'Arry</k>\n<tr>ˈærɪ</tr>\n <abr>сущ.</abr>\n "
			"1) <c><dtrn><co><abr><i>прост.</i></abr>; = <kref>Harry</kref></co></dtrn></c>"
		),
		(
			'<div class="article"><div class="k"><b>\'Arry</b></div>'
			'[ˈærɪ]<br/><span class="abr"><font color="green"><i>сущ.</i>'
			"</font></span><br/> 1) "
			'<font color="green"><span class="co">(<span class="abr">'
			'<font color="green"><i><i>прост.</i></i></font></span>; = '
			'<a class="kref" href="bword://Harry">Harry</a>)</span></font></div>'
		),
	),
	(
		"image_ex",  # <img> rendered self-closing inside definition and example
		(
			'<k>image</k>\n<dtrn>see <img src="pic.png" alt="pic"/></dtrn>\n'
			'<ex>with an <img src="ex.png"/></ex>'
		),
		(
			'<div class="article"><div class="k"><b>image</b></div>'
			'see <img src="pic.png" alt="pic"/><br/>'
			'<div class="example" style="padding: 10px 0px;">'
			'with an <img src="ex.png"/></div></div>'
		),
	),
	(
		"iref",  # <iref> external link and audio speaker
		(
			'<k>link</k>\n<dtrn>see <iref href="http://example.com">external</iref> '
			'and <iref href="sound.mp3">audio</iref></dtrn>'
		),
		(
			'<div class="article"><div class="k"><b>link</b></div>'
			'see <a class="iref" href="http://example.com">external</a> and '
			'<a class="iref" href="sound.mp3">🔊</a></div>'
		),
	),
	(
		"nu_opt",  # <nu> markers and <opt> suffix in headword
		"<k>Glamorgan<nu /><opt>shire</opt><nu /></k>\n<dtrn>a county in Wales</dtrn>",
		(
			'<div class="article"><div class="k"><b>Glamorgan (shire)</b></div>'
			"a county in Wales</div>"
		),
	),
	(
		"blockquote",  # <blockquote> as indented block
		"<k>quote</k>\n<dtrn>definition</dtrn>\n<blockquote>quoted passage</blockquote>",
		(
			'<div class="article"><div class="k"><b>quote</b></div>'
			'definition<br/><div class="m">quoted passage</div></div>'
		),
	),
	(
		"gr_c",  # <c> color tag and <gr> grammatical tag
		(
			'<k>grammar</k>\n<dtrn>word <c c="blue">colored</c> <gr>gram.</gr> '
			"and <c>default green</c> text</dtrn>"
		),
		(
			'<div class="article"><div class="k"><b>grammar</b></div>'
			'word <font color="blue">colored</font> '
			'<font color="green">gram.</font><br/>'
			'and <font color="green">default green</font> text</div>'
		),
	),
	(
		"basic_format",  # `basic_format` — basic inline formatting tags
		(
			"<k>format</k>\n<dtrn>normal <b>bold</b> <i>italic</i> <u>under</u> "
			"<sub>sub</sub> <sup>sup</sup> <tt>mono</tt> text</dtrn>"
		),
		(
			'<div class="article"><div class="k"><b>format</b></div>'
			"normal <b>bold</b> <i>italic</i> <u>under</u> "
			"<sub>sub</sub> <sup>sup</sup> <tt>mono</tt> text</div>"
		),
	),
	(
		"etm_abbr",  # <etm> etymology and <abbr> abbreviation
		"<k>etymology</k>\n<dtrn>from <etm>Latin word</etm>, <abbr>abbr.</abbr></dtrn>",
		(
			'<div class="article"><div class="k"><b>etymology</b></div>'
			"from Latin word, <i>abbr.</i></div>"
		),
	),
	(
		"br_inline",  # explicit <br/> inside a definition
		"<k>br</k>\n<dtrn>first<br/>second <br/> third</dtrn>",
		(
			'<div class="article"><div class="k"><b>br</b></div>'
			"first<br/>second <br/>third</div>"
		),
	),
]


class XdxfTransformerTest(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		cls.tr = XdxfTransformer()

	def case(self, inner, expected):
		article = ET.fromstring(f"<ar>{inner}</ar>")
		self.assertEqual(self.tr.transform(article), expected)

	def test_samples(self):
		for name, inner, expected in SAMPLES:
			with self.subTest(name=name):
				self.case(inner, expected)

	def test_newline_after_keyword_no_br(self):
		# newline between <k> (block) and the definition must not add a <br/>
		self.case(
			"<k>w</k>\n <abr>noun</abr>\n <dtrn>def <abr>m</abr> text</dtrn>",
			'<div class="article"><div class="k"><b>w</b></div>'
			'<span class="abr"><font color="green"><i>noun</i></font></span>'
			'<br/> def <span class="abr"><font color="green"><i>m</i>'
			"</font></span> text</div>",
		)

	def test_whitespace_only_between_tags(self):
		# whitespace-only text nodes (newline + space) must not be dropped
		self.case(
			"<k>ADSL</k>\n See: <dtrn><kref>asymmetrical digital subscriber line</kref></dtrn>",
			'<div class="article"><div class="k"><b>ADSL</b></div>'
			'See: <a class="kref" href="bword://asymmetrical%20digital%20subscriber%20line">'
			"asymmetrical digital subscriber line</a></div>",
		)

	def test_example_padding(self):
		tr = XdxfTransformer(example_padding=25)
		article = ET.fromstring("<ar><k>x</k><ex>example</ex></ar>")
		self.assertEqual(
			tr.transform(article),
			'<div class="article"><div class="k"><b>x</b></div>'
			'<div class="example" style="padding: 25px 0px;">example</div></div>',
		)

	def test_auto_rtl(self):
		tr = XdxfTransformer()
		article = ET.fromstring('<ar><k>x</k><def xml:lang="fa">سلام</def></ar>')
		self.assertEqual(
			tr.transform(article),
			'<div class="article"><div class="k"><b>x</b></div>'
			'<div lang="fa" dir="rtl">سلام</div></div>',
		)

	def test_auto_rtl_lang(self):
		cases = (
			("fa", "rtl"),
			("fa-IR", "rtl"),
			("en", "ltr"),
			("en-US", "ltr"),
		)
		for lang, direction in cases:
			with self.subTest(lang=lang):
				article = ET.fromstring(
					f'<ar><k>x</k><def xml:lang="{lang}">text</def></ar>',
				)
				self.assertIn(
					f' lang="{lang}" dir="{direction}"',
					XdxfTransformer().transform(article),
				)

	def test_auto_rtl_disabled(self):
		tr = XdxfTransformer(auto_rtl=False)
		article = ET.fromstring('<ar><k>x</k><def xml:lang="fa">سلام</def></ar>')
		self.assertEqual(
			tr.transform(article),
			'<div class="article"><div class="k"><b>x</b></div>'
			'<div lang="fa">سلام</div></div>',
		)

	def test_auto_rtl_nested(self):
		inner = (
			'<k>x</k><def xml:lang="fa"><def xml:lang="fa">a</def>'
			'<def xml:lang="en">b</def></def>'
		)
		self.case(
			inner,
			'<div class="article"><div class="k"><b>x</b></div>'
			'<ul lang="fa" dir="rtl"><li lang="fa" dir="rtl">a</li>'
			'<li lang="en" dir="ltr">b</li></ul></div>',
		)

	def test_div_dir(self):
		self.case(
			'<k>x</k><def><div dir="rtl">سلام</div></def>',
			'<div class="article"><div class="k"><b>x</b></div>'
			'<div><div dir="rtl">سلام</div></div></div>',
		)

	def test_div_lang_auto_rtl(self):
		self.case(
			'<k>x</k><def><div lang="fa">سلام</div></def>',
			'<div class="article"><div class="k"><b>x</b></div>'
			'<div><div lang="fa" dir="rtl">سلام</div></div></div>',
		)

	def test_div_explicit_dir_overrides_auto_rtl(self):
		self.case(
			'<k>x</k><def><div xml:lang="en" dir="rtl">a</div></def>',
			'<div class="article"><div class="k"><b>x</b></div>'
			'<div><div lang="en" dir="rtl">a</div></div></div>',
		)

	def test_div_inside_definition_list(self):
		self.case(
			'<k>x</k><def><div dir="rtl"><def><def>a</def><def>b</def></def></div></def>',
			'<div class="article"><div class="k"><b>x</b></div>'
			'<div><div dir="rtl"><ul><li>a</li><li>b</li></ul></div></div></div>',
		)


if __name__ == "__main__":
	unittest.main()
