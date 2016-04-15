# -*- coding: utf-8 -*-
## octopus_mdic.py
## Read Octopus MDict dictionary format, mdx(dictionary)/mdd(data)
##
## Copyright (C) 2013 Xiaoqiang Wang <xiaoqiangwang AT gmail DOT com>
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

from formats_common import *

from pyglossary.plugin_lib.readmdict import MDX, MDD
import os

enable = True
format = 'OctopusMdict'
description = 'Octopus MDict'
extentions = ['.mdx']
readOptions = ['resPath', 'encoding', 'substyle']
writeOptions = []

def read(glos, filename, **options):
    mdx = MDX(filename, options.get('encoding', ''), options.get('substyle', True))
    glos.setInfo('title', mdx.header.get('Title', os.path.basename(filename)))
    glos.setInfo('description', mdx.header.get('Description', ''))
    for word, defi in mdx.items():
        glos.addEntry(word, defi)

    # find companion mdd file
    base, ext = os.path.splitext(filename)
    mdd_filename = ''.join([base, os.path.extsep, 'mdd'])
    if (os.path.exists(mdd_filename)):
        mdd = MDD(mdd_filename)
        # write out optional data files
        datafolder = options.get('resPath', base + '_files')
        if not os.path.exists(datafolder):
            os.makedirs(datafolder)
        for key, value in mdd.items():
            fname = ''.join([datafolder, key.replace('\\', os.path.sep)]);
            if not os.path.exists(os.path.dirname(fname)):
                os.makedirs(os.path.dirname(fname))
            f = open(fname, 'wb')
            f.write(value)
            f.close()
