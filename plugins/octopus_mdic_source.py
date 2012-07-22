#!/usr/bin/python
# -*- coding: utf-8 -*-

from formats_common import *

enable = True
format = 'OctopusMdicSrc'
description = 'Octopus MDic Source'
extentions = ('.mtxt')
readOptions = ()
writeOptions = ()

def read(glos, filename):
    glos.data = []
    for section in open(filename).read().split('</>'):
        lines = section.strip().replace('\r\n', '\n').split('\n')
        if len(lines) < 2:
            continue
        glos.data.append((
            lines[0],
            '\n'.join(lines[1:]),
        ))


def write(glos, filename):
    glos.writeTxt(
        ('\r\n', '\r\n</>\r\n'),
        filename=filename,
        writeInfo=False,
        rplList=[],
        ext='.mtxt',
        head='',
    )


