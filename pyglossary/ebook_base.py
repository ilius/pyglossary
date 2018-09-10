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

import logging
log = logging.getLogger('root')


from itertools import groupby
import os
from os.path import join
import zipfile
import tempfile
from datetime import datetime
import shutil

from pyglossary.text_utils import toUnicode
from pyglossary.os_utils import indir


def get_prefix(word, length):
    """
    Return the prefix for the given word,
    of length length.

    :param word: the word string
    :type  word: unicode
    :param length: prefix length
    :type  length: int
    :rtype: unicode
    """
    if not word:
        return None
    word = toUnicode(word)
    if 'Z' < word[0] < 'a':
        return u"SPECIAL"
    return word[:length] ## return a unicode? FIXME


class EbookWriter(object):
    """
    A class representing a generic ebook containing a dictionary.

    It can be used to output a MOBI or an EPUB 2 container.

    The ebook must have an OPF, and one or more group XHTML files.

    Optionally, it can have a cover image, an NCX TOC, an index XHTML file.

    The actual file templates are provided by the caller.
    """
    ebook_format = u''

    CSS_CONTENTS = u''
    GROUP_XHTML_TEMPLATE = u''
    GROUP_XHTML_INDEX_LINK = u''
    
    GROUP_XHTML_WORD_TEMPLATE = u''
    GROUP_XHTML_WORD_JOINER = u''
    GROUP_XHTML_WORD_DEFINITION_TEMPLATE = u''
    GROUP_XHTML_WORD_DEFINITION_JOINER = u'\n'
    
    MIMETYPE_CONTENTS = u''
    CONTAINER_XML_CONTENTS = u''
    
    GROUP_START_INDEX = 2

    COVER_TEMPLATE = '{cover}'

    INDEX_XHTML_TEMPLATE = u'''<?xml version="1.0" encoding="utf-8" standalone="no"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
 <head>
  <title>{title}</title>
  <link rel="stylesheet" type="text/css" href="style.css" />
 </head>
 <body class="indexPage">
  <h1 class="indexTitle">{indexTitle}</h1>
  <p class="indexGroupss">
{links}
  </p>
 </body>
</html>'''
    INDEX_XHTML_LINK_TEMPLATE = u'   <span class="indexGroup"><a href=\"{ref}\">{label}</a></span>'

    INDEX_XHTML_LINK_JOINER = u' &#8226;\n'


    OPF_MANIFEST_ITEM_TEMPLATE = u'  <item href="{ref}" id="{id}" media-type="{mediaType}" />'

    OPF_SPINE_ITEMREF_TEMPLATE = u'  <itemref idref="{id}" />'

    DEFAULT_ARGS = {
        #'bookeen_collation_function': None,## bookeen format
        #'bookeen_install_file': False,## bookeen format
        #'marisa_bin_path': None,## kobo format
        #'marisa_index_size': 1000000,## kobo format
        #'sd_ignore_sametypesequence': False,## stardict format
        #'sd_no_dictzip': False,## stardict format
        
        'group_by_prefix_length': 2,
        #'group_by_prefix_merge_across_first': False,
        #'group_by_prefix_merge_min_size': 0,
        
        'apply_css': None,
        'escape_strings': False,
        'ignore_synonyms': False,
        'flatten_synonyms': False,
        'include_index_page': False,
        'compress': False,
        'keep': False,
        'cover_path': None,
    }

    def get_opf_contents(self, manifest_contents, spine_contents):
        raise NotImplementedError

    def __init__(self, glos, **kwargs):
        self.glos = glos
        self.args = dict(self.DEFAULT_ARGS)
        self.args.update(kwargs)
        self.tmpDir = None
        self.cover = None
        self.files = []
        self.manifest_files = []
        self.groups = []

    def close(self):
        pass

    myOpen = lambda self, fname, mode: open(join(self.tmpDir, fname), mode)

    def add_file(self, relative_path, contents, mode=None):
        if mode is None:
            mode = zipfile.ZIP_DEFLATED
        file_path = os.path.join(self.tmpDir, relative_path)
        file_obj = self.myOpen(file_path, 'wb')
        try:
            # Python 2
            if isinstance(contents, unicode):
                contents = contents.encode('utf-8')
        except NameError:
            # Python 3
            if isinstance(contents, str):
                contents = contents.encode('utf-8')
        except:
            # should not occur
            pass
        file_obj.write(contents)
        file_obj.close()
        self.files.append({
            'path': relative_path,
            'mode': mode,
        })

    def write_cover(self, cover_path):
        if cover_path:
            try:
                basename = os.path.basename(cover_path)
                cover_obj = self.myOpen(cover_path, 'rb')
                cover = cover_obj.read()
                cover_obj.close()
                b = basename.lower()
                mimetype = 'image/jpeg'
                if b.endswith('.png'):
                    mimetype = 'image/png'
                elif b.endswith('.gif'):
                    mimetype = 'image/gif'
                self.add_file_manifest(u'OEBPS/%s' % basename, basename, cover, mimetype)
                self.cover = basename
            except:
                pass

    def write_css(self, custom_css_path_absolute):
        css = self.CSS_CONTENTS
        if custom_css_path_absolute is not None:
            try:
                css_obj = self.myOpen(custom_css_path_absolute, 'rb')
                css = css_obj.read()
                css_obj.close()
            except:
                pass
        self.add_file_manifest(u'OEBPS/style.css', u'style.css', css, 'text/css')

    def add_file_manifest(self, relative_path, id, contents, mimetype):
        self.add_file(relative_path, contents)
        self.manifest_files.append({
            'path': relative_path,
            'id': id, 'mimetype': mimetype,
        })

    def get_group_xhtml_file_name_from_index(self, index):
        if index < self.GROUP_START_INDEX:
        ## or index >= len(self.groups) + self.GROUP_START_INDEX:
        ## number of groups are not known## FIXME
        ## so we can't say if the current group is the last or not
            return u'#groupPage'
        return u'g%06d.xhtml' % index

    def add_group(self, key, entries):
        self.groups.append({'key': key, 'entries': entries})

    def write_groups(self):
        group_labels = []
        
        self.glos.sortWords()
        for group_i, (group_prefix, group_entry_iter) in enumerate(groupby(
            self.glos,
            lambda tmpEntry: get_prefix(
                tmpEntry.getWord(),
                self.args['group_by_prefix_length'],
            ),
        )):
            index = group_i + self.GROUP_START_INDEX
            first_word = ''
            last_word = ''
            group_contents = []
            for entry in group_entry_iter:
                word = entry.getWord()
                defi = entry.getDefi()
                if not first_word:
                    first_word = word
                last_word = word
                group_contents.append(self.GROUP_XHTML_WORD_DEFINITION_TEMPLATE.format(
                    headword=self.escape_if_needed(word),
                    definition=self.escape_if_needed(defi),
                ))

            group_label = group_prefix
            if group_prefix != u'SPECIAL':
                group_label = '%s&#8211;%s' % (first_word, last_word)
            group_labels.append(group_label)

            previous_link = self.get_group_xhtml_file_name_from_index(index - 1)
            next_link = self.get_group_xhtml_file_name_from_index(index + 1)

            group_contents = self.GROUP_XHTML_WORD_DEFINITION_JOINER.join(group_contents)
            group_contents = self.GROUP_XHTML_TEMPLATE.format(
                title=group_label,
                group_title=group_label,
                previous_link=previous_link,
                index_link=self.GROUP_XHTML_INDEX_LINK if self.args['include_index_page'] else u'',
                next_link=next_link,
                group_contents=group_contents,
            )
            
            group_xhtml_path = self.get_group_xhtml_file_name_from_index(index)

            self.add_file_manifest(
                u'OEBPS/%s' % group_xhtml_path,
                group_xhtml_path,
                group_contents,
                u'application/xhtml+xml',
            )
        
        return group_labels

    def escape_if_needed(self, string):
        if self.args['escape_strings']:
            string = string.replace('&', '&amp;')\
                .replace('"', '&quot;')\
                .replace("'", '&apos;')\
                .replace('>', '&gt;')\
                .replace('<', '&lt;')
        return string.decode('utf-8')


    def write_index(self, group_labels):
        """
            group_labels: a list of labels
        """
        links = []
        for label_i, label in enumerate(group_labels):
            links.append(self.INDEX_XHTML_LINK_TEMPLATE.format(
                ref = self.get_group_xhtml_file_name_from_index(
                    self.GROUP_START_INDEX + label_i
                ),
                label = label,
            ))
        links = self.INDEX_XHTML_LINK_JOINER.join(links)
        title = self.glos.getInfo('title')
        contents = self.INDEX_XHTML_TEMPLATE.format(
            title = title,
            indexTitle = title,
            links = links,
        )
        self.add_file_manifest(
            u'OEBPS/index.xhtml',
            u'index.xhtml',
            contents,
            u'application/xhtml+xml',
        )

    def get_opf_contents(self, manifest_contents, spine_contents):
        cover = u''
        if self.cover:
            cover = self.COVER_TEMPLATE.format(cover=self.cover)

        creationDate = datetime.now().strftime('%Y-%m-%d')
        
        return self.OPF_TEMPLATE.format(
            identifier = self.glos.getInfo('uuid'),
            sourceLang = self.glos.getInfo('sourceLang'),
            targetLang = self.glos.getInfo('sourceLang'),
            title = self.glos.getInfo('title'),
            creator = self.glos.getInfo('author'),
            copyright = self.glos.getInfo('copyright'),
            creationDate = creationDate,
            cover = cover,
            manifest = manifest_contents,
            spine = spine_contents,
        )

    def write_opf(self):
        manifest_lines = []
        spine_lines = []
        for mi in self.manifest_files:
            manifest_lines.append(self.OPF_MANIFEST_ITEM_TEMPLATE.format(
                ref=mi['id'],
                id=mi['id'],
                mediaType=mi['mimetype']
            ))
            if mi['mimetype'] == u'application/xhtml+xml':
                spine_lines.append(self.OPF_SPINE_ITEMREF_TEMPLATE.format(
                    id=mi['id'],
                ))

        manifest_contents = u'\n'.join(manifest_lines)
        spine_contents = u'\n'.join(spine_lines)
        opf_contents = self.get_opf_contents(
            manifest_contents,
            spine_contents,
        )

        self.add_file('OEBPS/content.opf', opf_contents)

    def write_ncx(self, group_labels):
        """
            write_ncx
            only for epub
        """
        pass

    def write(self, file_path_absolute):
        self.tmpDir = tempfile.mkdtemp()
        with indir(self.tmpDir):
            cover_path = self.glos.getInfo('cover_path') ## set from command line FIXME
            if cover_path:
                cover_path = os.path.abspath(cover_path)

            custom_css_path_absolute = self.glos.getInfo('apply_css') ## set from command line FIXME
            if custom_css_path_absolute:
                custom_css_path_absolute = os.path.abspath(custom_css_path_absolute)

            os.makedirs(u'META-INF')
            os.makedirs(u'OEBPS')

            if self.MIMETYPE_CONTENTS:
                self.add_file(u'mimetype', self.MIMETYPE_CONTENTS, mode=zipfile.ZIP_STORED)
            if self.CONTAINER_XML_CONTENTS:
                self.add_file(u'META-INF/container.xml', self.CONTAINER_XML_CONTENTS)

            self.write_cover(cover_path)

            self.write_css(custom_css_path_absolute)

            group_labels = self.write_groups()

            if self.args['include_index_page']:
                self.write_index()

            self.write_ncx(group_labels)

            self.write_opf()

            if self.args['compress']:
                zipFp = zipfile.ZipFile(
                    file_path_absolute,
                    'w',
                    compression=zipfile.ZIP_DEFLATED,
                )
                for fileDict in self.files:
                    zipFp.write(
                        fileDict['path'],
                        compress_type=fileDict['mode'],
                    )
                zipFp.close()
                if not self.args['keep']:
                    shutil.rmtree(self.tmpDir)
            else:
                if self.args['keep']:
                    shutil.copytree(self.tmpDir, file_path_absolute)
                else:
                    shutil.move(self.tmpDir, file_path_absolute)




