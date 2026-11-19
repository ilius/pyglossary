"""Render each XDXF sample side-by-side (highlighted source + rendered HTML) to SVG."""

import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from lxml import etree as ET
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import XmlLexer
from weasyprint import HTML

from pyglossary.xdxf.py_transform import XdxfTransformer

OUT = Path(__file__).resolve().parent / "res"
BORDER = 20  # SVG user units == CSS px (pdftocairo emits unit-less width/height)

XINK_HREF = "{http://www.w3.org/1999/xlink}href"

PYGMENTS_CSS = HtmlFormatter(nowrap=True).get_style_defs(".src")

SAMPLES = [
	# (name, inner XDXF markup, description)
	(
		"issue562",
		(
			"<k>grzebiący</k><def> <def> <pos>прич. от</pos> <b>grzebać</b>; "
			"</def><def><co> grzebiące, grzebiących</co> <pos>мн. зоол.</pos> "
			"кури́ные <pos>lm</pos> (Galliformes) </def></def>"
		),
		"issue #562: spaces between tags preserved",
	),
	(
		"kref_spaces",
		(
			"<k>cross-reference</k>\n<dtrn>see <kref>other</kref> here and "
			'<kref k="target word">target</kref></dtrn>'
		),
		"issue #532: spaces before/after kref preserved",
	),
	(
		"newlines",
		"<k>newlines</k>\n<abr>noun</abr>\n<dtrn>line one\nline two\n\nline four</dtrn>",
		"issue #532: newlines render as line breaks",
	),
	(
		"lingvo_entry",
		(
			"<k>abstinence</k>\n<tr>ˈæbstɪnən(t)s</tr> \n <abr>сущ.</abr>\n"
			" 1) <c><dtrn><co>= abstention</co></dtrn></c>\n"
			"  а) <dtrn>воздержание; умеренность</dtrn>\n"
			"   <ex>abstinence from meat — вегетарианство</ex>\n"
			" 2) <dtrn><abr>рел.</abr> соблюдение поста, пост</dtrn>\n"
			"  <ex>day of abstinence — постный день</ex>"
		),
		"issue #532: Lingvo-style entry with numbered defs, grey indented examples",
	),
	(
		"ex_orig_tran",
		(
			"<k>example</k>\n<dtrn>definition text</dtrn>\n"
			"<ex>Пример <ex_orig>original</ex_orig> <ex_tran>translation</ex_tran></ex>"
		),
		"issue #532: <ex> grey + indented, ex_orig/ex_tran inline",
	),
	(
		"nested_defs",
		"<k>polysemy</k><def><def>first meaning</def><def>second meaning</def></def>",
		"2 nested <def> elements render as an unordered list",
	),
	(
		"single_def",
		"<k>single</k><def>one meaning only</def>",
		"single <def> renders as a block",
	),
	(
		"transcription",
		(
			"<k>'Arry</k>\n<tr>ˈærɪ</tr>\n <abr>сущ.</abr>\n"
			" 1) <c><dtrn><co><abr><i>прост.</i></abr>; = <kref>Harry</kref></co></dtrn></c>"
		),
		"transcription in brackets, <c>/<co>/<abr> inline formatting",
	),
	(
		"image_ex",
		'<k>image</k>\n<dtrn>see <img src="pic.png" alt="pic"/></dtrn>\n<ex>with an <img src="ex.png"/></ex>',
		"<img> rendered self-closing inside definition and example",
	),
	(
		"iref",
		(
			'<k>link</k>\n<dtrn>see <iref href="http://example.com">external</iref> and '
			'<iref href="sound.mp3">audio</iref></dtrn>'
		),
		"<iref> external link and audio speaker",
	),
	(
		"nu_opt",
		"<k>Glamorgan<nu /><opt>shire</opt><nu /></k>\n<dtrn>a county in Wales</dtrn>",
		"<nu> markers and <opt> suffix in headword",
	),
	(
		"blockquote",
		"<k>quote</k>\n<dtrn>definition</dtrn>\n<blockquote>quoted passage</blockquote>",
		"<blockquote> as indented block",
	),
	(
		"gr_c",
		(
			'<k>grammar</k>\n<dtrn>word <c c="blue">colored</c> <gr>gram.</gr> and '
			"<c>default green</c> text</dtrn>"
		),
		"<c> color tag and <gr> grammatical tag",
	),
	(
		"basic_format",
		(
			"<k>format</k>\n<dtrn>normal <b>bold</b> <i>italic</i> <u>under</u> "
			"<sub>sub</sub> <sup>sup</sup> <tt>mono</tt> text</dtrn>"
		),
		"basic inline formatting tags",
	),
	(
		"etm_abbr",
		"<k>etymology</k>\n<dtrn>from <etm>Latin word</etm>, <abbr>abbr.</abbr></dtrn>",
		"<etm> etymology and <abbr> abbreviation",
	),
	(
		"br_inline",
		"<k>br</k>\n<dtrn>first<br/>second <br/> third</dtrn>",
		"explicit <br/> inside a definition",
	),
]

CSS = f"""
    @page {{ size: A4; margin: {BORDER}pt; }}
    body {{
        font-family: sans-serif;
        font-size: 13px;
        background: #ffffff;
        margin: 0;
        color: #111111;
    }}
    h1 {{ font-size: 15px; margin: 0 0 2px 0; }}
    h2 {{ font-size: 11px; color: #888888; font-weight: normal; margin: 0 0 12px 0; }}
    table {{
        border-collapse: collapse;
        width: 100%;
    }}
    td {{
        vertical-align: top;
        border: 1px solid #cccccc;
        padding: 10px;
        width: 50%;
    }}
    td.src {{
        background: #f7f7f7;
        font-family: monospace;
        font-size: 11px;
        white-space: pre-wrap;
        word-break: break-all;
        line-height: 1.4;
    }}
    td.render {{ background: #ffffff; }}
    .article {{ line-height: 1.5; }}
    .k {{ font-size: 1.25em; margin-bottom: 2px; }}
    {PYGMENTS_CSS}
"""


_Matrix = tuple[float, float, float, float, float, float]


def font_to_span(html: str) -> str:
	"""
	WeasyPrint ignores the deprecated ``<font color>`` attribute.

	Replace ``<font color="...">`` with an equivalent ``<span style="color:...">``
	so the colors in the transformed HTML survive the PDF/SVG preview.
	"""
	html = re.sub(r'<font color="([^"]*)">', r'<span style="color:\1">', html)
	return html.replace("</font>", "</span>")


def _parse_matrix(s: str | None) -> _Matrix:
	"""Parse an SVG ``matrix(a b c d e f)`` transform (identity if absent)."""
	if not s:
		return (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
	nums = [float(v) for v in re.findall(r"[-+]?\d*\.?\d+", s)]
	if not nums:
		return (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
	# translate/scale/rotate variants have 1-3 values; default the rest
	a, b, c, d, e, f = (nums + [0.0] * 6)[:6]
	if len(nums) == 1:  # translate
		e, f = a, b
		a, d = 1.0, 1.0
		b, c = 0.0, 0.0
	if len(nums) == 2:  # translate(x y)
		e, f = nums
		a, b, c, d = 1.0, 0.0, 0.0, 1.0
	return (a, b, c, d, e, f)


def _mul_matrix(m1: _Matrix, m2: _Matrix) -> _Matrix:
	a1, b1, c1, d1, e1, f1 = m1
	a2, b2, c2, d2, e2, f2 = m2
	return (
		a1 * a2 + c1 * b2,
		b1 * a2 + d1 * b2,
		a1 * c2 + c1 * d2,
		b1 * c2 + d1 * d2,
		a1 * e2 + c1 * f2 + e1,
		b1 * e2 + d1 * f2 + f1,
	)


def _apply_matrix(m: _Matrix, x: float, y: float) -> tuple[float, float]:
	a, b, c, d, e, f = m
	return (a * x + c * y + e, b * x + d * y + f)


def _svg_content_bbox(svg_path: Path) -> tuple[float, float, float, float]:
	"""Return the bounding box of all drawn content, in SVG user units."""
	root = ET.parse(svg_path).getroot()
	ids = {el.get("id"): el for el in root.iter() if el.get("id")}
	inf = 1e30
	minX = minY = inf
	maxX = maxY = -inf

	def visit(el: ET._Element, m: _Matrix) -> None:
		nonlocal minX, minY, maxX, maxY
		tag = el.tag.split("}")[-1]
		m = _mul_matrix(m, _parse_matrix(el.get("transform")))
		if tag == "use":
			href = el.get(XINK_HREF) or el.get("href")
			if href and href.startswith("#"):
				target = ids.get(href[1:])
				if target is not None:
					tx = float(el.get("x", 0))
					ty = float(el.get("y", 0))
					if tx or ty:
						m = _mul_matrix(m, (1.0, 0.0, 0.0, 1.0, tx, ty))
					visit(target, m)
			return
		if tag in {"defs", "clipPath", "filter", "mask", "pattern", "symbol"}:
			return
		if tag != "g":  # geometry-bearing leaf elements
			if tag == "path" and el.get("clip-rule"):
				# clip-region geometry, not drawn content
				return
			fill = el.get("fill") or ""
			if fill and (
				"100%, 100%, 100%" in fill
				or "255, 255, 255" in fill
				or fill.lower() in {"white", "#fff", "#ffffff"}
			):
				# invisible white fill on the white page
				return
			pts: list[tuple[float, float]] = []
			if tag == "path":
				nums = [
					float(v) for v in re.findall(r"[-+]?\d*\.?\d+", el.get("d") or "")
				]
				pts = [(nums[i], nums[i + 1]) for i in range(0, len(nums) - 1, 2)]
			elif tag in {"rect", "image"}:
				x = float(el.get("x", 0))
				y = float(el.get("y", 0))
				w = float(el.get("width", 0))
				h = float(el.get("height", 0))
				pts = [(x, y), (x + w, y), (x, y + h), (x + w, y + h)]
			elif tag == "circle":
				cx = float(el.get("cx", 0))
				cy = float(el.get("cy", 0))
				r = float(el.get("r", 0))
				pts = [(cx - r, cy - r), (cx + r, cy + r)]
			elif tag == "ellipse":
				cx = float(el.get("cx", 0))
				cy = float(el.get("cy", 0))
				rx = float(el.get("rx", 0))
				ry = float(el.get("ry", 0))
				pts = [(cx - rx, cy - ry), (cx + rx, cy + ry)]
			elif tag == "line":
				pts = [
					(float(el.get("x1", 0)), float(el.get("y1", 0))),
					(float(el.get("x2", 0)), float(el.get("y2", 0))),
				]
			elif tag in {"polygon", "polyline"}:
				nums = [
					float(v)
					for v in re.findall(r"[-+]?\d*\.?\d+", el.get("points") or "")
				]
				pts = [(nums[i], nums[i + 1]) for i in range(0, len(nums) - 1, 2)]
			for px, py in pts:
				x, y = _apply_matrix(m, px, py)
				minX = min(minX, x)
				minY = min(minY, y)
				maxX = max(maxX, x)
				maxY = max(maxY, y)
		# containers (svg, g, a, ...): recurse
		for child in el:
			if isinstance(child.tag, str):
				visit(child, m)

	visit(root, (1.0, 0.0, 0.0, 1.0, 0.0, 0.0))
	if minX == inf:
		return (0.0, 0.0, 0.0, 0.0)
	return (minX, minY, maxX, maxY)


def _adjust_svg(svg_path: Path) -> None:
	bbox = _svg_content_bbox(svg_path)
	left = bbox[0] - BORDER
	top = bbox[1] - BORDER
	width = (bbox[2] - bbox[0]) + 2 * BORDER
	height = (bbox[3] - bbox[1]) + 2 * BORDER

	def repl(m: re.Match[str]) -> str:
		tag = m.group(0)
		tag = re.sub(r'\swidth="[^"]*"', f' width="{width:g}"', tag)
		tag = re.sub(r'\sheight="[^"]*"', f' height="{height:g}"', tag)
		tag = re.sub(
			r'\sviewBox="[^"]*"',
			f' viewBox="{left:g} {top:g} {width:g} {height:g}"',
			tag,
		)
		# opaque white background so the 20px border is visible in any viewer
		tag += (
			f'<rect x="{left:g}" y="{top:g}" width="{width:g}" '
			f'height="{height:g}" fill="#ffffff"/>'
		)
		return tag

	s = open(svg_path, encoding="utf-8").read()
	s = re.sub(r"<svg[^>]*>", repl, s, count=1)
	open(svg_path, "w", encoding="utf-8").write(s)


def main() -> None:
	OUT.mkdir(parents=True, exist_ok=True)
	tr = XdxfTransformer()
	for name, inner, desc in SAMPLES:
		html = font_to_span(tr.transform(ET.fromstring(f"<ar>{inner}</ar>")))
		src = highlight(inner, XmlLexer(), HtmlFormatter(nowrap=True))
		full = (
			f"<!DOCTYPE html><html><head><meta charset='utf-8'><style>{CSS}</style></head>"
			f"<body>"
			f"<h1>{name}</h1><h2>{desc}</h2>"
			f"<table><tr>"
			f'<td class="src">{src}</td>'
			f'<td class="render">{html}</td>'
			f"</tr></table>"
			f"</body></html>"
		)
		pdf = OUT / f"{name}.pdf"
		HTML(string=full).write_pdf(str(pdf))
		svg = OUT / f"{name}.svg"
		subprocess.run(["pdftocairo", "-svg", str(pdf), str(svg)], check=True)
		pdf.unlink()
		_adjust_svg(svg)


if __name__ == "__main__":
	main()
