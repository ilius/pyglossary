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
glos.setInfo("name", name)
glos.detectLangsFromName()
print(f"{name!r}\t{glos.sourceLangName or None}\t{glos.targetLangName or None}")
