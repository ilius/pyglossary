# -*- coding: utf-8 -*-

from formats_common import *

enable = True
format = "Freedict"
description = "FreeDict (tei)"
extensions = [".tei"]
optionsProp = {}
depends = {}


def write(glos: GlossaryType, filename: str):
	fp = open(filename, "w")
	title = glos.getInfo("title")

	fp.write(f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE TEI.2 PUBLIC "-//TEI P3//DTD Main Document Type//EN"
"/usr/share/sgml/tei-3/tei2.dtd" [
<!ENTITY %% TEI.dictionaries "INCLUDE" > ]>
<tei.2>
<teiHeader>
<fileDesc>
<titleStmt>
	<title>{title}</title>
	<respStmt><resp>converted with</resp><name>PyGlossary</name></respStmt>
</titleStmt>
<publicationStmt><p>freedict.de</p></publicationStmt>
<sourceDesc><p>{filename}</p></sourceDesc>
</fileDesc>
</teiHeader>
<text><body>""")

	for entry in glos:
		if entry.isData():
			# FIXME
			continue
		word = entry.getWord()
		defi = entry.getDefi()
		fp.write(f"""<entry>
<form><orth>{word}</orth></form>
<gramgrp><pos>n</pos></gramgrp>
<trans><tr>{defi}</tr></trans>
</entry>""")
	fp.write("</body></text></tei.2>")
	fp.close()
