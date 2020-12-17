from pyglossary import core
from pyglossary.core import rootDir
from os.path import join


def xdxf_to_html_transformer():
	from lxml import etree
	from lxml.etree import tostring
	from io import StringIO
	try:
		from lxml import etree as ET
	except ModuleNotFoundError as e:
		e.msg += f", run `{core.pip} install lxml` to install"
		raise e

	with open(join(rootDir, "pyglossary", "xdxf.xsl"), "r") as f:
		xslt_txt = f.read()

	xslt = ET.XML(xslt_txt)
	_transform = ET.XSLT(xslt)

	def transform(input_text: str) -> str:
		doc = etree.parse(StringIO(f"<ar>{input_text}</ar>"))
		result_tree = _transform(doc)
		text = tostring(result_tree, encoding="utf-8").decode("utf-8")
		text = text.replace("<br/> ", "<br/>")
		return text

	return transform
