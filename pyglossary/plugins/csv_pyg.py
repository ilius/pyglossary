# -*- coding: utf-8 -*-
##
## Copyright © 2013 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
## This file is part of PyGlossary project, http://sourceforge.net/projects/pyglossary/
##
## This program is a free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 3, or (at your option)
## any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License along
## with this program. Or on Debian systems, from /usr/share/common-licenses/GPL
## If not, see <http://www.gnu.org/licenses/gpl.txt>.

from formats_common import *

enable = True
format = 'Csv'
description = 'CSV'
extentions = ['.csv']
readOptions = []
writeOptions = []
supportsAlternates = True

import csv
from pyglossary.file_utils import fileCountLines


class Reader(object):
    def __init__(self, glos):
        self._glos = glos
        self._filename = ''
        self._fp = None
        self._leadingLinesCount = 0
        self._len = None
        self._csvReader = None
    def open(self, filename):
        self._filename = filename
        self._fp = open(filename, 'rb')
        self._csvReader = csv.reader(
            self._fp,
            dialect='excel',
        )
    def close(self):
        if not self._fp:
            return
        try:
            self._fp.close()
        except:
            log.exception('error while closing tabfile')
        self._fp = None
        self._csvReader = None
    def __len__(self):
        if self._len is None:
            log.warn('Try not to use len(reader) as it takes extra time')
            self._len = fileCountLines(self._filename) - self._leadingLinesCount
        return self._len
    __iter__ = lambda self: self
    def next(self):
        if not self._csvReader:
            log.error('%s is not open, can not iterate'%self)
            raise StopIteration
        row = self._csvReader.next()
        if not row:
            return
        try:
            word = row[0]
            defi = row[1]
        except IndexError:
            log.error('invalid row: %r'%row)
            return
        try:
            alts = row[2].split(',')
        except IndexError:
            pass
        else:
            word = [word] + alts
        return Entry(word, defi)



def write(glos, filename):
    with open(filename, 'wb') as csvfile:
        writer = csv.writer(
            csvfile,
            dialect='excel',
            quoting=csv.QUOTE_ALL,## FIXME
        )
        for entry in glos:
            words = entry.getWords()
            if not words:
                continue
            word, alts = words[0], words[1:]
            defi = entry.getDefi()

            row = [
                words[0],
                defi,
            ]
            if alts:
                row.append(','.join(alts))
            
            writer.writerow(row)












