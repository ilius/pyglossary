from __future__ import annotations

import logging
from os.path import join
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from lxml.etree import _XSLTResultTree

	from pyglossary.lxml_types import Element


from pyglossary import core
from pyglossary.core import rootDir

log = logging.getLogger("pyglossary")

__all__ = [
	"XslXdxfTransformer",
]


class XslXdxfTransformer:
	_gram_color: str = "green"
	_example_padding: int = 10

	def __init__(self, encoding: str = "utf-8") -> None:
		try:
			from lxml import etree as ET
		except ModuleNotFoundError as e:
			e.msg += f", run `{core.pip} install lxml` to install"
			raise e

		with open(
			join(rootDir, "pyglossary", "xdxf", "xdxf.xsl"),
			encoding="utf-8",
		) as f:
			xslt_txt = f.read()

		xslt = ET.XML(xslt_txt)
		self._transform = ET.XSLT(xslt)
		self._encoding = encoding

	@staticmethod
	def tostring(elem: _XSLTResultTree | Element) -> str:
		from lxml import etree as ET

		return (
			ET.tostring(
				elem,
				method="html",
				pretty_print=True,
			)
			.decode("utf-8")
			.strip()
		)

	def transform(self, article: Element) -> str:
		result_tree = self._transform(article)
		text = self.tostring(result_tree)
		text = text.replace("<br/> ", "<br/>")
		return text  # noqa: RET504

	def transformByInnerString(self, articleInnerStr: str) -> str:
		from lxml import etree as ET

		return self.transform(
			ET.fromstring(f"<ar>{articleInnerStr}</ar>"),
		)
