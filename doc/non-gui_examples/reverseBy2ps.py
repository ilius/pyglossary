#!/usr/bin/python
import sys
sys.path.append('/usr/share/pyglossary/src')
from glossary import *
import text_utils, time
from subprocess import Glossary

try:
  import psyco
  print('Using module "psyco" to reduce execution time.')
  psyco.bind(Glossary)
  usePsyco=True
except:
  print('Warning: module "psyco" not found.')


t0 = time.time()

dicPath ='quick_eng-persian-e0.3.txt'
#dicPath ='xfardic-computer-elec.txt'
wordsFilePath1 = dicPath[:-4]+'-words-1.txt'
wordsFilePath2 = dicPath[:-4]+'-words-2.txt'


psCode = 'from glossary import *\nimport text_utils, time, sys\n'
if usePsyco:
  psCode += 'import psyco\npsyco.bind(Glossary)\n'
psCode += 'g = Glossary()\ng.readTabfile(\'%s\')\ng.checkUnicode()\n'%(dicPath)
psCode += 'g2 = g.reverseDic(\'%s\', {\'matchWord\':True})\ng2.writeTabfile()\n' %(wordsFilePath2)
ps = Popen(['python', '-c', psCode])

g = Glossary()
g.readTabfile(dicPath)
g.checkUnicode()
g2 = g.reverseDic(wordsFilePath1, {'matchWord':True})
g2.writeTabfile(dicPath[:-4]+'_reversed2.txt')

print('About %d seconds left.'%(time.time()-t0))

