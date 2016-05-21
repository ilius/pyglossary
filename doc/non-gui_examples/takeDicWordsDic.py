#!/usr/bin/python
import sys
sys.path.append('/usr/share/pyglossary/src')
from glossary import Glossary
import time

t0 = time.time()

dicPath=sys.argv[1]
g = Glossary()
g.read(dicPath)

words = g.takeOutputWords({'minLen':4, 'noEn':True})

wordsFile = open(dicPath[:-4]+"-words.tab.txt", "w")
print(len(words), "words found. writing to file...")
wordsFile.write( string.join(words, '\t#\n')+'\tNothing\n' )
wordsFile.close()

print('%f  seconds left.' %(time.time()-t0))


