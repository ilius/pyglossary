#!/usr/bin/env python3

import sys
from os.path import dirname

sys.path.insert(0, dirname(dirname(__file__)))

import logging

from pyglossary.glossary_v2 import Glossary

log = logging.getLogger()
log.setLevel(logging.INFO)

name = " ".join(sys.argv[1:])
glos = Glossary()
glos.info.name = name
glos.info.detectLangsFromName()
print(f"{name!r}\t{glos.info.sourceLangName or None}\t{glos.info.targetLangName or None}")
