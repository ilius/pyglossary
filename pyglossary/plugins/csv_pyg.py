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

def read(glos, filename):
    glos.data = []
    with open(filename, 'rb') as csvfile:
        reader = csv.reader(
            csvfile,
            dialect='excel',
        )
        for row in spamreader:
            try:
                alts = row[2].split(',')
            except:
                alts = {}
            glos.data.append((
                row[0],
                row[1],
                {
                    'alts': alts,
                },
            ))

def write(glos, filename):
    with open(filename, 'wb') as csvfile:
        writer = csv.writer(
            csvfile,
            dialect='excel',
            quoting=csv.QUOTE_ALL,## FIXME
        )
        for item in glos.data:
            row = list(item[:2])
            try:
                alts = item[2]['alts']
            except (IndexError, KeyError):## FIXME
                pass
            else:
                row.append(
                    ','.join(alts)
                )
            writer.writerow(row)












