# -*- coding: utf-8 -*-
# octopus_mdic.py
# Read Octopus MDict dictionary format, mdx(dictionary)/mdd(data)
#
# Copyright (C) 2013 Xiaoqiang Wang <xiaoqiangwang AT gmail DOT com>
# Copyright (C) 2013-2016 Saeed Rasooli <saeed.gnu@gmail.com>
#
# This program is a free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# You can get a copy of GNU General Public License along this program
# But you can always get it from http://www.gnu.org/licenses/gpl.txt
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

from formats_common import *

import os
from os.path import splitext, isfile, isdir, extsep, basename, dirname

enable = True
format = 'OctopusMdict'
description = 'Octopus MDict'
extentions = ['.mdx']
readOptions = [
    'encoding',  # str
    'substyle',  # bool
]
writeOptions = []


class Reader(object):
    def __init__(self, glos):
        self._glos = glos
        self.clear()

    def clear(self):
        self._filename = ''
        self._encoding = ''
        self._substyle = True
        self._mdx = None
        self._mdd = None
        self._mddFilename = ''

    def open(self, filename, **options):
        from pyglossary.plugin_lib.readmdict import MDX, MDD
        self._filename = filename
        self._encoding = options.get('encoding', '')
        self._substyle = options.get('substyle', True)
        self._mdx = MDX(filename, self._encoding, self._substyle)

        filenameNoExt, ext = splitext(self._filename)
        mddFilename = ''.join([filenameNoExt, extsep, 'mdd'])
        if isfile(mddFilename):
            self._mdd = MDD(mddFilename)
            self._mddFilename = mddFilename

        log.pretty(self._mdx.header, 'mdx.header=')
        # for key, value in self._mdx.header.items():
        #    key = key.lower()
        #    self._glos.setInfo(key, value)
        try:
            title = self._mdx.header[b'Title']
        except KeyError:
            pass
        else:
            self._glos.setInfo('title', title)
        self._glos.setInfo(
            'description',
            self._mdx.header.get(b'Description', ''),
        )

    def __iter__(self):
        if self._mdx is None:
            log.error('trying to iterate on a closed MDX file')
        else:
            for word, defi in self._mdx.items():
                word = toStr(word)
                defi = toStr(defi)
                yield self._glos.newEntry(word, defi)
            self._mdx = None

        if self._mdd:
            for b_fname, b_data in self._mdd.items():
                fname = toStr(b_fname)
                fname = fname.replace('\\', os.sep).lstrip(os.sep)
                yield self._glos.newDataEntry(fname, b_data)
            self._mdd = None

    def __len__(self):
        if self._mdx is None:
            log.error(
                'OctopusMdict: called len(reader) while reader is not open'
            )
            return 0
        return len(self._mdx)

    def close(self):
        self.clear()
