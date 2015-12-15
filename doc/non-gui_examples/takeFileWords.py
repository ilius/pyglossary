#!/usr/bin/python
import sys
sys.path.append('/usr/share/pyglossary/src')
import text_utils
import string, os, time

t0 = time.time()

fp=file(sys.argv[1])
words = text_utils.takeStrWords(fp.read(), {'sort':False})
wordsFile=file(sys.argv[1][:-4]+'-words.txt', 'w')
print(len(words), 'words found. writing to file...')
wordsFile.write('\n'.join(words) + '\n')
wordsFile.close()
fp.close()

print('%f  seconds left.' %(time.time()-t0))

