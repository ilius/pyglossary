#!/usr/bin/python
# -*- coding: utf-8 -*-
enable = True
format = 'Stardict'
description = 'StarDict (ifo)'
extentions = ('.ifo',)
readOptions = ()
writeOptions = ()

import sys, os
sys.path.append('/usr/share/pyglossary/src')

from text_utils import intToBinStr, binStrToInt, runDictzip, printAsError

infoKeys = ('bookname', 'author', 'email', 'website', 'description',
            'copyright', 'sourceLang', 'targetLang', 'charset')


def read(glos, filename, options={}):
  if filename.endswith('.ifo'):
    filename = filename[:-4]
  ifoStr = open(filename+'.ifo', 'rb').read()
  idxStr = open(filename+'.idx', 'rb').read()
  if os.path.isfile(filename+'.dict.dz'):
    import gzip
    #dictStr = gzip.open(filename+'.dict.dz').read() 
    dictFd = gzip.open(filename+'.dict.dz')
  else:
    #dictStr = open(filename+'.dict', 'rb').read()
    dictFd = open(filename+'.dict', 'rb')
  for line in ifoStr.split('\n'):
    line = line.strip()
    if not line:
      continue
    ind = line.find('=')
    if ind==-1:
      #printAsError('Unknown ifo line: %r'%line)
      continue
    glos.setInfo(line[:ind].strip(), line[ind+1:].strip())
  glos.data = []
  word = ''
  sumLen = 0
  i = 0
  wrongSorted = []
  ##############################  IMPORTANT PART ############################
  while i < len(idxStr):
    if idxStr[i]=='\x00':
      sumLen2 = binStrToInt(idxStr[i+1:i+5])
      if sumLen2 != sumLen:
        wrongSorted.append(word)
      sumLen = sumLen2
      defiLen = binStrToInt(idxStr[i+5:i+9])
      #defi = dictStr[sumLen:sumLen+defiLen].replace('<BR>', '\n')\
      #                                     .replace('<br>', '\n')
      dictFd.seek(sumLen)
      defi = dictFd.read(defiLen).replace('<BR>', '\n')\
                                 .replace('<br>', '\n')
      word = word.replace('<BR>', '\\n')\
                 .replace('<br>', '\\n')
      glos.data.append((word, defi))
      sumLen += defiLen
      word = ''
      i += 9
    else:
      word += idxStr[i]
      i += 1
  dictFd.close()
  ############################################################################
  if len(wrongSorted)>0:
    print('Warning: wrong sorting count: %d'%len(wrongSorted))

def write(glos, filename, dictZip=True, richText=True):
  g = glos.copy()
  g.data.sort(stardict_strcmp, lambda x: x[0])
  if filename[-4:].lower()=='.ifo':
    filename=filename[:-4]
  elif filename[-1]==os.sep:
    if not os.path.isdir(filename):
      os.makedirs(filename)
    filename = path_join(filename, path_split(filename)[-1])
  elif os.path.isdir(filename):
    filename = path_join(filename, path_split(filename)[-1])
  dictMark = 0
  idxStr = ''
  dictStr = ''
  for item in g.data:
    (word, defi) = item
    if richText:
      defi = defi.replace('\n', '<BR>')
    lm = len(defi)
    idxStr += (word + '\x00' + intToBinStr(dictMark, 4) + intToBinStr(lm, 4))
    dictMark += lm
    dictStr += defi
  open(filename+'.dict', 'wb').write(dictStr)
  open(filename+'.idx', 'wb').write(idxStr)
  ifoStr = '''StarDict\'s dict ifo file\nversion=2.4.2
wordcount=%d
idxfilesize=%d
bookname=%s
sametypesequence=%s
'''%(len(g.data), len(idxStr), g.getInfo('name'), ('h' if richText else 'm'))
  for key in infoKeys:
    value = g.getInfo(key)
    if value!='':
      ifoStr += '%s=%s\n'%(key, value)
  open(filename+'.ifo', 'wb').write(ifoStr)
  if dictZip:
    runDictzip(filename)

def read_ext(glos, filename):
  ## This method uses module provided by dictconv, but dictconv is very slow for reading from stardict db!
  ## therefore this method in not used by GUI now.
  ## and binary module "_stardict" is deleted.
  ## If you want to use it, compile it yourglos, or get it from an older version of PyGlossary (version 2008.08.30)
  glos.data=[]
  import _stardict
  db = _stardict.new_StarDict(filename)
  _stardict.PySwigIterator_swigregister(db)
  glos.setInfo('title', _stardict.StarDict_bookname(db))
  glos.setInfo('author', _stardict.StarDict_bookname(db))
  glos.setInfo('title', _stardict.StarDict_bookname(db))
  ## geting words:
  idxStr = open(filename[:-4]+'.idx').read()
  words=[]
  #""" # get words list by python codes.
  word=''
  i=0
  while i < len(idxStr):
    if idxStr[i]=='\x00':
      if word!='':
        words.append(word)
        word = ''
      i += 9
    else:
      word += idxStr[i]
      i += 1
  """ # get words list using _stardict module.
  lst = _stardict.StarDict_dump(db) ## don't know how to get std::vector items
  _stardict.PySwigIterator_swigregister(lst)
  num = _stardict.StarDict_vector_get_size(db, lst)
  _stardict.PySwigIterator_swigregister(num)
  for i in xrange(num):
    word = _stardict.StarDict_vector_get_item(db, lst, i)
    words.append(word)
    if i%100==0:
      print(i)
      while gtk.events_pending():
        gtk.main_iteration_do(False)
  """
  ui = glos.ui
  n = len(words)
  i=0
  if ui==None:
    for word in words:
      defi = _stardict.StarDict_search(db, word).replace('<BR>', '\n')
      glos.data.append((word, defi))
  else:
    ui.progressStart()
    k = 1000
    for i in xrange(n):
      word = words[i]
      defi = _stardict.StarDict_search(db, word).replace('<BR>', '\n')
      glos.data.append((word, defi))
      if i%k==0:
        rat = float(i)/n
        ui.progress(rat)
    #ui.progress(1.0, 'Loading Completed')
    ui.progressEnd()


def write_ext(glos, filename, sort=True, dictZip=True):
  if sort:
    g = glos.copy()
    g.data.sort()
  else:
    g = glos
  try:
    import _stardictbuilder
  except ImportError:
    printAsError('Binary module "_stardictbuilder" can not be imported! '+\
      'Using internal StarDict builder')
    return g.writeStardict(filename, sort=False)
  db = _stardictbuilder.new_StarDictBuilder(filename)
  _stardictbuilder.StarDictBuilder_swigregister(db)
  for item in g.data:
    _stardictbuilder.StarDictBuilder_addHeadword(db,item[0],item[1], '')
  _stardictbuilder.StarDictBuilder_setTitle(db, g.getInfo('name'))
  _stardictbuilder.StarDictBuilder_setAuthor(db, g.getInfo('author'))
  _stardictbuilder.StarDictBuilder_setLicense(db, g.getInfo('license'))
  _stardictbuilder.StarDictBuilder_setOrigLang(db, g.getInfo('origLang'))
  _stardictbuilder.StarDictBuilder_setDestLang(db, g.getInfo('destLang'))
  _stardictbuilder.StarDictBuilder_setDescription(db, g.getInfo('description'))
  _stardictbuilder.StarDictBuilder_setComments(db, g.getInfo('comments'))
  _stardictbuilder.StarDictBuilder_setEmail(db, g.getInfo('email'))
  _stardictbuilder.StarDictBuilder_setWebsite(db, g.getInfo('website'))
  _stardictbuilder.StarDictBuilder_setVersion(db, g.getInfo('version'))
  _stardictbuilder.StarDictBuilder_setcreationTime(db, '')
  _stardictbuilder.StarDictBuilder_setLastUpdate(db, '')
  _stardictbuilder.StarDictBuilder_finish(db)
  if dictZip:
    if filename[-4:]=='.ifo':
      filename = filename[:-4]
      runDictzip(filename)

# ISUPPER macro in glib library gstrfuncs.c file
def glib_ISUPPER(c):
  return ord(c) >= ord('A') and ord(c) <= ord('Z')
  
# TOLOWER macro in glib library gstrfuncs.c file
def glib_TOLOWER(c):
  if glib_ISUPPER(c):
    return chr((ord(c) - ord('A')) + ord('a'))
  else:
    return c
  
# g_ascii_strcasecmp function in glib library gstrfuncs.c file
def glib_ascii_strcasecmp(s1, s2):
  commonLen = min(len(s1), len(s2))
  for i in xrange(commonLen):
    c1 = ord(glib_TOLOWER(s1[i]))
    c2 = ord(glib_TOLOWER(s2[i]))
    if c1 != c2:
      return c1 - c2
  return len(s1) - len(s2)

def strcmp(s1, s2):
  commonLen = min(len(s1), len(s2))
  for i in xrange(commonLen):
    c1 = ord(s1[i])
    c2 = ord(s2[i])
    if c1 != c2:
      return c1 - c2
  return len(s1) - len(s2)

# use this function to sort index items in StarDict dictionary
# s1 and s2 must be utf-8 encoded strings
def stardict_strcmp(s1, s2):
  a = glib_ascii_strcasecmp(s1, s2)
  if a == 0:
    return strcmp(s1, s2)
  else:
    return a
