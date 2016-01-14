# -*- coding: utf-8 -*-
## appledict.py
## Output to Apple Dictionary xml sources for Dictionary Development Kit.
##
## Copyright (C) 2012 Xiaoqiang Wang <xiaoqiangwang AT gmail DOT com>
##
## This program is a free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation, version 3 of the License.
##
## You can get a copy of GNU General Public License along this program
## But you can always get it from http://www.gnu.org/licenses/gpl.txt
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
## GNU General Public License for more details.

import pkgutil
import shutil

from formats_common import *

enable = True
format = 'AppleDict'
description = 'AppleDict Source (xml)'
extentions = ['.xml']
readOptions = []
writeOptions = [
    'cleanHTML',
    'css',
    'xsl',
    'defaultPrefs',
    'prefsHTML',
]

OtherResources = 'OtherResources'

import sys
sys.setrecursionlimit(10000)

import os
import re
import hashlib

def truncate(text, length=449):
    """
    trunct a string to given length
    :param str text:
    :return: truncated text
    :rtype: str
    """
    content = re.sub('(\t|\n|\r)', ' ', text)
    if (len(text)>length):
        # find the next space after max_len chars (do not break inside a word)
        pos = content[:length].rfind(' ')
        if pos == -1:
            pos = length
        text = text[:pos]
    return text

def abspath_or_None(path):
    return os.path.abspath(os.path.expanduser(path)) if path else None

def write_xsl(xsl):
    if not xsl:
        return
    with chdir(OtherResources, create=True):
        shutil.copyfile(xsl, os.path.basename(xsl))

def format_default_prefs(defaultPrefs):
    """
    :type defaultPrefs: dict or None

    as by 14th of Jan 2016, it is highly recommended that prefs should contain
    {'version': '1'}, otherwise Dictionary.app does not keep user changes
    between restarts.
    """
    if not defaultPrefs:
        return ""
    if not isinstance(defaultPrefs, dict):
        raise TypeError("defaultPrefs not a dictionary: %r" % defaultPrefs)
    if str(defaultPrefs.get('version', None)) != '1':
        from pyglossary.glossary import log
        log.error("default prefs does not contain {'version': '1'}.  prefs "
                  "will not be persistent between Dictionary.app restarts.")
    return "\n".join("\t\t<key>%s</key>\n\t\t<string>%s</string>" % i
                     for i in sorted(defaultPrefs.iteritems())).strip()

def write_plist(glos, filename, xsl=None, defaultPrefs=None, prefsHTML=None):
    try:
        from bs4 import BeautifulSoup
    except:
        from BeautifulSoup import BeautifulSoup

    template = pkgutil.get_data(__name__, 'project_templates/Info.plist')

    basename = os.path.splitext(filename)[0]
    # identifier must be unique
    # use file base name
    identifier = basename.replace(' ', '')
    # strip html tags
    copyright = (u'%s' % BeautifulSoup(glos.getInfo('copyright')).text).encode('utf-8')

    # if DCSDictionaryXSL provided but DCSDictionaryDefaultPrefs <dict/> not
    # present in Info.plist, Dictionary.app will crash.
    with open(filename, 'wb') as f:
        f.write(template % {
            "CFBundleIdentifier": identifier,
            "CFBundleDisplayName": glos.getInfo('name'),
            "CFBundleName": basename,
            "DCSDictionaryCopyright": copyright,
            "DCSDictionaryManufacturerName": glos.getInfo('author'),
            "DCSDictionaryXSL": (os.path.basename(xsl) if xsl else ""),
            "DCSDictionaryDefaultPrefs": format_default_prefs(defaultPrefs),
            "DCSDictionaryPrefsHTML": (os.path.basename(prefsHTML) if prefsHTML else ""),
        })

def write_xml(glos, filename, cleanHTML):
    try:
        from bs4 import BeautifulSoup
    except:
        try:
            from BeautifulSoup import BeautifulSoup
        except:
            cleanHTML = False
    # progress bar
    ui = glos.ui
    if ui:
        ui.progressStart()

    f = open(filename, 'wb')

    # write header
    f.write('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<d:dictionary xmlns="http://www.w3.org/1999/xhtml" xmlns:d="http://www.apple.com/DTDs/DictionaryService-1.0.rng">\n')

    # write entries
    entry_ids = set([])
    total = len(glos.data)
    close_tag = re.compile('<(BR|HR)>', re.IGNORECASE)
    nonprintable = re.compile('[\x00-\x07\x0e-\x1f]')
    img_tag = re.compile('<IMG (.*?)>', re.IGNORECASE)
    for index, item in enumerate(glos.data):
        # strip double quotes and html tags
        title = re.sub('<[^<]+?>|"|[<>]|\xef\xbb\xbf', '', item[0])
        if not title:
            continue
        # use MD5 hash of title string as id
        id = hashlib.md5(title).hexdigest()

        # check entry id duplicates
        while id in entry_ids:
            id = id + '_'
        entry_ids.add(id)
        # get alternatives list
        try:
            alts = item[2]['alts']
        except:
            alts = []

        # begin entry
        f.write('<d:entry id="%(id)s" d:title="%(title)s">\n'%{'id':id, 'title':truncate(title.replace('&', '&amp;'), 1126)})

        # index values
        #   title as index
        f.write('    <d:index d:value="%s"/>\n'%truncate(title))
        #   alternative items as index also
        for alt in alts:
            if alt != title:
                f.write('    <d:index d:value="%s"/>\n'%truncate(alt))

        # nice header to display
        content = ('<h1>%s</h1>\n'%title) + item[1]
        # xhtml is strict
        if cleanHTML:
            soup  = BeautifulSoup(content, from_encoding='utf8')
            content = str(soup)
        else:
            content = close_tag.sub('<\g<1> />', content)
            content = img_tag.sub('<img \g<1>/>', content)
        content = content.replace('&nbsp;', '&#160;')
        content = nonprintable.sub('', content)
        f.write(content)

        # end entry
        f.write('\n</d:entry>\n')

        if index%1000==0 and ui:
            ui.progress(1.0*index/total)
    # end dictionary
    f.write('</d:dictionary>\n')
    f.close()

    # end progress bar
    if ui:
        ui.progressEnd()

def write_css(fname, css_file):
    if css_file:
        with open(css_file, 'r') as f:
            css = f.read()
    else:
        css = pkgutil.get_data(__name__, 'project_templates/Dictionary.css')
    with open(fname, 'w') as f:
        f.write(css)

def write_makefile(dict_name):
    template = pkgutil.get_data(__name__, 'project_templates/Makefile')
    with open('Makefile', 'w') as f:
        f.write(template % {'dict_name': dict_name})

def write_prefsHTML(prefsHTML_file):
    if not prefsHTML_file:
        return
    with chdir(OtherResources, create=True):
        shutil.copyfile(prefsHTML_file, os.path.basename(prefsHTML_file))

def write(glos, fpath, cleanHTML="yes", css=None, xsl=None, defaultPrefs=None, prefsHTML=None):
    basename = os.path.splitext(fpath)[0]
    dict_name = os.path.split(basename)[1]
    # before chdir
    css = abspath_or_None(css)
    xsl = abspath_or_None(xsl)
    prefsHTML = abspath_or_None(prefsHTML)
    with chdir(basename, create=True):
        write_plist(glos, dict_name + '.plist', xsl=xsl, defaultPrefs=defaultPrefs, prefsHTML=prefsHTML)
        write_xml(glos, dict_name + '.xml', cleanHTML=="yes")
        write_css(dict_name + '.css', css)
        write_makefile(dict_name)
        write_xsl(xsl)
        write_prefsHTML(prefsHTML)

if __name__ == '__main__':
    import sys, os.path
    import glossary as gl
    glos = gl.Glossary()

    informat = gl.Glossary.descFormat["Babylon (bgl)"]
    outformat = gl.Glossary.descFormat["AppleDict Source (xml)"]

    filename = sys.argv[1]
    basename = os.path.splitext(os.path.basename(filename))[0]

    outdir = sys.argv[2]
    if not os.path.exists(outdir):
        os.mkdir(outdir)

    glos.read(filename, format=informat, resPath=os.path.join(outdir, "OtherResources"))


    glos.write(os.path.join(outdir, basename), format=outformat)

