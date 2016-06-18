#!/usr/bin/python
import sys
from pyglossary import Glossary

g = Glossary()
g.read(sys.argv[1])
g.writeTabfile()

