# -*- coding: utf-8 -*-
# The MIT License (MIT)

# Copyright (C) 2012-2016 Alberto Pettarin (alberto@albertopettarin.it)
# Copyright (C) 2016 Saeed Rasooli <saeed.gnu@gmail.com>

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


from formats_common import *
from pyglossary.ebook_base import *

enable = True
format = 'Epub2'
description = 'EPUB-2 E-Book'
extentions = ['.epub',]
readOptions = []

writeOptions = [
#    'group_by_prefix_length',
#    'group_by_prefix_merge_min_size',
#    'group_by_prefix_merge_across_first',
]



class Epub2Writer(EbookWriter):
    ebook_format = format
    ## MIMETYPE_CONTENTS, CONTAINER_XML_CONTENTS, NCX_TEMPLATE, NCX_NAVPOINT_TEMPLATE are only in Epub
    MIMETYPE_CONTENTS = u'application/epub+zip'
    CONTAINER_XML_CONTENTS = u'''<?xml version="1.0" encoding="UTF-8" ?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
   <rootfiles>
      <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
   </rootfiles>
</container>'''

    NCX_TEMPLATE = u'''<?xml version="1.0" encoding="utf-8" ?>
<!DOCTYPE ncx PUBLIC "-//NISO//DTD ncx 2005-1//EN" "http://www.daisy.org/z3986/2005/ncx-2005-1.dtd">
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
 <head>
  <meta name="dtb:uid" content="{identifier}" />
  <meta name="dtb:depth" content="1" />
  <meta name="dtb:totalPageCount" content="0" />
  <meta name="dtb:maxPageNumber" content="0" />
 </head>
 <docTitle>
  <text>{title}</text>
 </docTitle>
 <navMap>
{ncx_items}
 </navMap>
</ncx>'''

    NCX_NAVPOINT_TEMPLATE = u''' <navPoint id="n{index:06d}" playOrder="{index:d}">
  <navLabel>
   <text>{text}</text>
  </navLabel>
  <content src="{src}" />
 </navPoint>'''

    CSS_CONTENTS = u'''@charset "UTF-8";
body {
  margin: 10px 25px 10px 25px;
}  
h1 {
  font-size: 200%;
}
h2 {
  font-size: 150%;
}
p {
  margin-left: 0em;
  margin-right: 0em;
  margin-top: 0em;
  margin-bottom: 0em;
  line-height: 2em;
  text-align: justify;
}
a, a:focus, a:active, a:visited {
  color: black;
  text-decoration: none;
}
body.indexPage {}
h1.indexTitle {}
p.indexGroups {
  font-size: 150%;
}
span.indexGroup {}
body.groupPage {}
h1.groupTitle {}
div.groupNavigation {}
span.groupHeadword {}
div.groupEntry {
  margin-top: 0;
  margin-bottom: 1em;
}
h2.groupHeadword {
  margin-left: 5%;
}
p.groupDefinition {
  margin-left: 10%;
  margin-right: 10%;
}
'''


    GROUP_XHTML_TEMPLATE = u'''<?xml version="1.0" encoding="utf-8" standalone="no"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
 <head>
  <title>{title}</title>
  <link rel="stylesheet" type="text/css" href="style.css" />
 </head>
 <body id="groupPage" class="groupPage">
  <h1 class="groupTitle">{group_title}</h1>
  <div class="groupNavigation">
   <a href="{previous_link}">[ Previous ]</a>
{index_link}
   <a href="{next_link}">[ Next ]</a>
  </div>
{group_contents}
 </body>
</html>'''
    GROUP_XHTML_INDEX_LINK = u'   <a href="index.xhtml">[ Index ]</a>'

    GROUP_XHTML_WORD_TEMPLATE = u'   <span class="groupHeadword">{headword}</span>'

    GROUP_XHTML_WORD_JOINER = u' &#8226;\n'

    GROUP_XHTML_WORD_DEFINITION_TEMPLATE = u'''  <div class="groupEntry">
   <h2 class="groupHeadword">{headword}</h2>
   <p class="groupDefinition">{definition}</p>
  </div>'''

    OPF_TEMPLATE = u'''<?xml version="1.0" encoding="utf-8" ?>
<package xmlns="http://www.idpf.org/2007/opf" version="2.0" unique-identifier="uid">
    <metadata xmlns:opf="http://www.idpf.org/2007/opf" xmlns:dc="http://purl.org/dc/elements/1.1/">
        <dc:identifier id="uid" opf:scheme="uuid">{identifier}</dc:identifier>
        <dc:language>{sourceLang}</dc:language>
        <dc:title>{title}</dc:title>
        <dc:creator opf:role="aut">{creator}</dc:creator>
        <dc:rights>{copyright}</dc:rights>
        <dc:date opf:event="creation">{creationDate}</dc:date>
        {cover}
    </metadata>
 <manifest>
{manifest}
 </manifest>
 <spine toc="toc.ncx">
{spine}
 </spine>
</package>'''


    COVER_TEMPLATE = u'<meta name="cover" content="{cover}" />'

    def write_ncx(self, group_labels):
        """
            write_ncx
            only for epub
        """
        ncx_items = []
        index = 1
        if self.args['include_index_page']:
            ncx_items.append(self.NCX_NAVPOINT_TEMPLATE.format(
                index=index,
                text='Index',
                src='index.xhtml',
            ))
            index += 1
        for group_label in group_labels:
            ncx_items.append(self.NCX_NAVPOINT_TEMPLATE.format(
                index = index,
                text = group_label,
                src = self.get_group_xhtml_file_name_from_index(index),
            ))
            index += 1
        ncx_items_unicode = u'\n'.join(ncx_items)
        ncx_contents = self.NCX_TEMPLATE.format(
            identifier = self.glos.getInfo('uuid'),
            title = self.glos.getInfo('title'),
            ncx_items = ncx_items_unicode,
        )
        self.add_file_manifest(u'OEBPS/toc.ncx', u'toc.ncx', ncx_contents, u'application/x-dtbncx+xml')




def write(
    glos,
    filename,
    group_by_prefix_length=2,
    #group_by_prefix_merge_min_size=0,
    #group_by_prefix_merge_across_first=False,
    compress=False,
    keep=False,
):

    import uuid
    result = None

    filename_absolute = os.path.abspath(filename)

    glos.setInfo(
        'uuid',
        str(uuid.uuid4()).replace('-', ''),
    )

    writer = Epub2Writer(
        glos,
        group_by_prefix_length=group_by_prefix_length,
        compress=compress,
        keep=keep,
        ## **kwargs
    )

    #log.debug('Writing to file "%s"...'%filename_absolute)
    writer.write(filename_absolute)
    #log.debug('Writing to file "%s"... done'%(filename_absolute))

    writer.close()

    return True


