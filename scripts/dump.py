#!/usr/bin/env python3

import sys
from pprint import pformat

from pyglossary.glossary import Glossary

glos = Glossary()
glos.read(sys.argv[1])
for entry in glos:
	print("Words: " + pformat(entry.l_term))
	print("Definitions: " + pformat(entry.defis))
	print("-------------------------")
