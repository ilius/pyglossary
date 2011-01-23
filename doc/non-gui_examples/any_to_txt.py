#!/usr/bin/python
import sys
sys.path.append('/usr/share/pyglossary/src')
from glossary import Glossary

g = Glossary()
g.read(sys.argv[1])
g.writeTabfile()

