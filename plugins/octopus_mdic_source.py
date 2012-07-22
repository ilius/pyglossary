#!/usr/bin/python
# -*- coding: utf-8 -*-

from formats_common import *

enable = True
format = 'OctopusMdicSrc'
description = 'Octopus MDic Source'
extentions = ('.mtxt')
readOptions = ()
writeOptions = ()

def write(glos, filename):
    glos.writeTxt(
        ('\r\n', '\r\n</>\r\n'),
        filename=filename,
        writeInfo=False,
        rplList=[],
        ext='.mtxt',
        head='',
    )


