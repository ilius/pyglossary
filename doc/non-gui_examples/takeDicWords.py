#!/usr/bin/python
import sys
sys.path.append('/usr/share/pyglossary/src')
from glossary import Glossary
import time
try:
  import psyco
  print 'Using module "psyco" to reduce execution time.'
  usePsyco=True
except:
  print 'Warning: module "psyco" not found'
  usePsyco=False

t0 = time.time()

dicPath = sys.argv[1]
g = Glossary()
g.read(dicPath)
if usePsyco:
  psyco.bind(Glossary,100)

words = g.takeOutputWords({'minLen':4, 'noEn':True})

#vav='\xd9\x88'
#vavWords=[]
#for i in range(len(words)):
#  word = words[i]
#  if word[:2]==vav:
#    vavWords += [word]
#vavWordsFile = open('vav_words.txt','w')
#vavWordsFile.write('\n'.join(vavWords)+'\n')
#del vavWordsFile

#vavCorFile = open('vav_corrects.txt')
#vavCor = [ word[:-1] for word in vavCorFile.readlines() ]
#for i in range(len(words)):
#  word = words[i][0]
  #if word[:2]==vav and not word in vavCor:
   # del words[i]

wordsFile = open(dicPath[:-4]+"-words.txt", "w")
print len(words),"words found. writing to file..."
wordsFile.write( '\n'.join(words)+'\n')
wordsFile.close()

print  '%f  seconds left.' %(time.time()-t0)


