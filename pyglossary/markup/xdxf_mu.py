

def escape(text):
	return text

def unescape(text):
	return text

def to_plain_text(xdxf_text):
	pass

def to_html(xdxf_text):## replaces `xdxf_to_html`
    """
    make sure to call `xdxf_init()` first.

    :param xdxf_text: xdxf formatted string
    :return: html formatted string
    """
    xdxf_txt = '<ar>%s</ar>' % xdxf_text
    f = StringIO(xdxf_txt)
    doc = etree.parse(f)
    result_tree = transform(doc)
    return tostring(result_tree, encoding='utf-8')



