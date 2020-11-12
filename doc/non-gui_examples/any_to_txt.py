#!/usr/bin/env python3

import sys
import pyglossary
from pyglossary import Glossary
from pyglossary.text_writer import writeTabfile

Glossary.init()

glos = Glossary()
glos.convert(inputFilename=sys.argv[1], outputFilename=f"{sys.argv[1]}.txt")
