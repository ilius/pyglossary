# from xml.sax.saxutils import escape as xml_escape
# from xml.sax.saxutils import unescape as xml_unescape


def xml_escape(data: str, quotation: bool = True) -> str:
	"""Escape &, <, and > in a string of data.
	"""
	# must do ampersand first
	data = data.replace("&", "&amp;")
	data = data.replace(">", "&gt;")
	data = data.replace("<", "&lt;")
	if quotation:
		data = data.replace("\"", "&quot;").replace("'", "&apos;")
	return data


def xml_unescape(data: str, quotation: bool = True) -> str:
	"""Unescape &amp;, &lt;, and &gt; in a string of data.
	"""
	data = data.replace("&lt;", "<")
	data = data.replace("&gt;", ">")
	if quotation:
		data = data.replace("&quot;", "\"").replace("&apos;", "'")
	# must do ampersand last
	return data.replace("&amp;", "&")
