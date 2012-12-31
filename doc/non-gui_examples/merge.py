#!/usr/bin/python
import sys
sys.path.append('/usr/share/pyglossary/src')
from glossary import Glossary

g1 = Glossary()
g2 = Glossary()
g1.read(sys.argv[1])
g2.read(sys.argv[2])
gm = g1.merge(g2)
gm.writeTabfile()




