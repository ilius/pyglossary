#!/usr/bin/python
import sys
sys.path.append('/usr/share/pyglossary/src')
from glossary import Glossary
import text_utils, time
try:
  import psyco
  print('Using module "psyco" to reduce execution time.')
  psyco.bind(Glossary)
except:
  print('Warning: module "psyco" not found.')


t0 = time.time()
try:
  dicPath = sys.argv[1]
except:
  dicPath ='quick_eng-persian-e0.3.txt'
try:
  wordsFilePath = sys.argv[2]
except:
  wordsFilePath = dicPath[:-4]+'-words.txt'


g = Glossary()
g.readTabfile(dicPath)
g.checkUnicode()
#g.faEdit()

#words = g.takeOutputWords()
#wordsFile = open(wordsFilePath, "w")
#print("%s words found. writing to file..."%len(words))
#wordsFile.write( string.join(words,"\n") )
#del wordsFile

wordsFile = open(wordsFilePath, "r")

g2 = g.reverseDic(wordsFile, {'matchWord':True})
g2.writeTabfile()
print('About',int(time.time()-t0) ,'seconds left.')
