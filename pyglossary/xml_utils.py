# from xml.sax.saxutils import escape as xml_escape
# from xml.sax.saxutils import unescape as xml_unescape

from __future__ import annotations

__all__ = ["xml_escape"]


def xml_escape(data: str, quotation: bool = True) -> str:
	"""Escape &, <, and > in a string of data."""
	# must do ampersand first
	data = data.replace("&", "&amp;")
	data = data.replace(">", "&gt;")
	data = data.replace("<", "&lt;")
	if quotation:
		data = data.replace('"', "&quot;").replace("'", "&apos;")
	return data  # noqa: RET504
