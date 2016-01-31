# -*- coding: utf-8 -*-

from itertools import combinations

from text_utils import toStr
from formats_common import *

enable = True
format = 'Xdxf'
description = 'XDXF'
extentions = ['.xdxf', '.xml']
readOptions = []
writeOptions = []

etree = None
XML = None
tostring = None


def import_xml_stuff():
    from lxml import etree as _etree
    global etree, XML, tostring
    etree = _etree
    XML = etree.XML
    tostring = etree.tostring


def read(glos, filename):
    """
    new format
    <xdxf ...>
        <meta_info>
            All meta information about the dictionary: its title, author etc.
        </meta_info>
        <lexicon>
            <ar>article 1</ar>
            <ar>article 2</ar>
            <ar>article 3</ar>
            <ar>article 4</ar>
            ...
        </lexicon>
    </xdxf>

    old format
    <xdxf ...>
        <full_name>...</full_name>
        <description>...</description>
        <ar>article 1</ar>
        <ar>article 2</ar>
        <ar>article 3</ar>
        <ar>article 4</ar>
        ...
    </xdxf>
    """
    ##<!DOCTYPE xdxf SYSTEM "http://xdxf.sourceforge.net/xdxf_lousy.dtd">
    import_xml_stuff()

    glos.data = []

    with open(filename, 'rb') as f:
        xdxf = XML(f.read())

    if xdxf[0].tag == 'meta_info':
        # new format
        pass
    else:
        # old format
        read_metadata_old(glos, xdxf)
        read_xdxf_old(glos, xdxf)


def read_metadata_old(glos, xdxf):
    full_name = xdxf.find('full_name').text
    description = xdxf.find('description').text
    if full_name:
        glos.setInfo('name', full_name)
    if description:
        glos.setInfo('description', description)


def read_xdxf_old(glos, xdxf):
    add_articles(glos, xdxf.iterfind('ar'))


def add_articles(glos, articles):
    """

    :param articles: iterator on <ar> tags
    :return: None
    """
    for item in articles:
        word, alts = title_alts(titles(item))
        if word:
            item.tail = None
            defi = tostring(item, encoding='utf-8')
            # <ar>...</ar>
            defi = defi[4:-5]
            glos.data.append((word, defi, {'alts': alts, 'defiFormat': 'x'}))


def titles(article):
    """

    :param article: <ar> tag
    :return: (title (str) | None, alternative titles (set))
    """
    titles = []
    for title_element in article.findall('k'):
        n_opts = len([c for c in title_element if c.tag == 'opt'])
        if n_opts:
            for j in range(n_opts + 1):
                for comb in combinations(range(n_opts), j):
                    titles.append(_mktitle(title_element, comb))
        else:
            titles.append(_mktitle(title_element))

    return titles


def title_alts(titles):
    if not titles:
        return None, []

    title = titles[0]

    if len(titles) == 1:
        return title, []

    return title, list(set(titles[1:]) - {title})


def _mktitle(title_element, include_opts=()):
    title = title_element.text
    opt_i = -1
    for c in title_element:
        if c.tag == 'nu' and c.tail:
            if title:
                title += c.tail
            else:
                title = c.tail
        if c.tag == 'opt':
            opt_i += 1
            if opt_i in include_opts:
                if title:
                    title += c.text
                else:
                    title = c.text
            if c.tail:
                if title:
                    title += c.tail
                else:
                    title = c.tail
    return toStr(title.strip())
