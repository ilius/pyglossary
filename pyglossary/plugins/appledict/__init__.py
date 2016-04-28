# -*- coding: utf-8 -*-
## appledict/__init__.py
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

import sys
sys.setrecursionlimit(10000)

import os
import re
import pkgutil
import shutil

from formats_common import *
from ._dict import write_xml, get_beautiful_soup

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
    'frontBackMatter',
    'OtherResources',
    'jing',
    'indexes',
]

OtherResources = 'OtherResources'

def abspath_or_None(path):
    return os.path.abspath(os.path.expanduser(path)) if path else None

def write_xsl(xsl):
    if not xsl:
        return
    with indir(OtherResources, create=True):
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
                     for i in sorted(defaultPrefs.items())).strip()

def write_plist(glos, filename, xsl, defaultPrefs, prefsHTML, frontBackMatter):
    bs4 = get_beautiful_soup()

    template = toStr(pkgutil.get_data(__name__, 'project_templates/Info.plist'))

    basename = os.path.splitext(filename)[0]
    # identifier must be unique
    # use file base name
    identifier = basename.replace(' ', '')

    if bs4:
        # strip html tags
        copyright = ('%s' % bs4.BeautifulSoup(glos.getInfo('copyright'), "lxml").text)
    else:
        copyright = glos.getInfo('copyright')

    # if DCSDictionaryXSL provided but DCSDictionaryDefaultPrefs <dict/> not
    # present in Info.plist, Dictionary.app will crash.
    with open(filename, 'w') as f:
        f.write(template % {
            "CFBundleIdentifier": identifier,
            "CFBundleDisplayName": glos.getInfo('name'),
            "CFBundleName": basename,
            "DCSDictionaryCopyright": copyright,
            "DCSDictionaryManufacturerName": glos.getInfo('author'),
            "DCSDictionaryXSL": (os.path.basename(xsl) if xsl else ""),
            "DCSDictionaryDefaultPrefs": format_default_prefs(defaultPrefs),
            "DCSDictionaryPrefsHTML": (os.path.basename(prefsHTML) if prefsHTML else ""),
            "DCSDictionaryFrontMatterReferenceID":
                ("<key>DCSDictionaryFrontMatterReferenceID</key>\n"
                 "\t<string>front_back_matter</string>" if frontBackMatter else ""),
        })

def write_css(fname, css_file):
    if css_file:
        with open(css_file, 'rb') as f:
            css = f.read()
    else:
        css = pkgutil.get_data(__name__, 'project_templates/Dictionary.css')
    with open(fname, 'wb') as f:
        f.write(css)

def write_makefile(dict_name):
    template = toStr(pkgutil.get_data(__name__, 'project_templates/Makefile'))
    with open('Makefile', 'w') as f:
        f.write(template % {'dict_name': dict_name})

def write_prefsHTML(prefsHTML_file):
    if not prefsHTML_file:
        return
    with indir(OtherResources, create=True):
        shutil.copyfile(prefsHTML_file, os.path.basename(prefsHTML_file))

def write_resources(paths):
    """copy files and directories 'paths' to 'OtherResources'.
    each item of 'paths' must be an absolute path.
    """
    if not paths:
        return
    with indir(OtherResources, create=True):
        # cannot just shutil.copytree as it will fail with error if
        # destination exists, but we want to merge instead.
        for path in paths:
            name = os.path.split(path)[1]
            if os.path.isdir(path):
                shutil.copytree(path, name)
            else:
                shutil.copy2(path, name)

def safe_listdir_set(path):
    """
    :rtype: set
    """
    if not path:
        return set()
    if not os.path.isdir(path):
        from pyglossary.glossary import log
        log.error("resource path is not a directory: %r" % path)
        return set()
    return {os.path.join(path, node) for node in os.listdir(path)}

def write(glos, fpath, cleanHTML="yes", css=None, xsl=None, defaultPrefs=None, prefsHTML=None, frontBackMatter=None, OtherResources=None, jing=None, indexes=None):
    """write glossary to Apple dictionary .xml and supporting files.

    :type glos: pyglossary.glossary.Glossary
    :type fpath: str

    :type cleanHTML: str
    :param cleanHTML: pass "yes" to use BeautifulSoup parser.

    :type css: str or None
    :param css: path to custom .css file

    :type xsl: str or None
    :param xsl: path to custom XSL transformations file.

    :type defaultPrefs: dict or None
    :param defaultPrefs: Default prefs in python dictionary literal format,
    i.e. {'key1': 'value1', "key2": "value2", ...}.  All keys and values must
    be quoted strings; not allowed characters (e.g. single/double quotes,
    equal sign '=', semicolon) must be escaped as hex code according to
    python string literal rules.

    :type prefsHTML: str or None
    :param prefsHTML: path to XHTML file with user interface for dictionary's
    preferences.  refer to Apple's documentation for details.

    :type frontBackMatter: str or None
    :param frontBackMatter: path to XML file with top-level tag
    <d:entry id="front_back_matter" d:title="Your Front/Back Matter Title">
        your front/back matter entry content
    </d:entry>

    :type OtherResources: str or None
    :param OtherResources: path to 'OtherResources' directory.  Apple
    recommending store images in 'OtherResources/Images'.

    :type jing: str or None
    :param jing: pass "yes" to run Jing check on generated XML.

    :type indexes: str or None
    :param indexes: Dictionary.app is dummy and by default it don't know
    how to perform flexible search.  we can help it by manually providing
    additional indexes to dictionary entries.
    # for now no languages supported yet.
    """
    basename = os.path.splitext(fpath)[0]
    dict_name = os.path.split(basename)[1]
    # before chdir (outside indir block)
    css = abspath_or_None(css)
    xsl = abspath_or_None(xsl)
    prefsHTML = abspath_or_None(prefsHTML)
    frontBackMatter = abspath_or_None(frontBackMatter)
    glos.resPath = abspath_or_None(glos.resPath)
    OtherResources = abspath_or_None(OtherResources)

    # to avoid copying css, prefs or something like that.
    res = safe_listdir_set(glos.resPath).union(safe_listdir_set(OtherResources))
    res -= {css, xsl, prefsHTML, frontBackMatter}

    with indir(basename, create=True, clear=True):
        write_plist(glos, dict_name + '.plist', xsl=xsl, defaultPrefs=defaultPrefs, prefsHTML=prefsHTML, frontBackMatter=frontBackMatter)
        write_xml(glos, dict_name + '.xml', cleanHTML=="yes", frontBackMatter=frontBackMatter, indexes=indexes)
        write_css(dict_name + '.css', css)
        write_makefile(dict_name)
        write_xsl(xsl)
        write_prefsHTML(prefsHTML)
        write_resources(res)
        if jing == "yes":
            from .jing import run
            run(dict_name + '.xml')

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

