#!/usr/bin/python
# -*- coding: utf-8 -*-
enable = True
format = 'Stardict'
description = 'StarDict (ifo)'
extentions = ('.ifo',)
readOptions = ()
writeOptions = ()

import sys, os, re, shutil
sys.path.append('/usr/share/pyglossary/src')

from text_utils import intToBinStr, binStrToInt, runDictzip, printAsError

infoKeys = ('bookname', 'author', 'email', 'website', 'description', 'date')


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
    filename = os.path.join(filename, os.path.split(filename[:-1])[-1])
  elif os.path.isdir(filename):
    filename = os.path.join(filename, os.path.split(filename)[-1])
  # filename now contains full file path without extension
  dictMark = 0
  idxStr = ''
  dictStr = ''
  alternates = [] # contains tuples ('alternate', index-of-word)
  for i in xrange(len(g.data)):
    item = g.data[i]
    (word, defi) = item[:2]
    if len(item) > 2 and 'alts' in item[2]:
      alternates += [(x, i) for x in item[2]['alts']]
    lm = len(defi)
    idxStr += (word + '\x00' + intToBinStr(dictMark, 4) + intToBinStr(lm, 4))
    dictMark += lm
    dictStr += defi
  with open(filename+'.dict', 'wb') as f:
    f.write(dictStr)
  with open(filename+'.idx', 'wb') as f:
    f.write(idxStr)
  if len(alternates) > 0:
    alternates.sort(stardict_strcmp, lambda x: x[0])
    synStr = ''
    for item in alternates:
      synStr += (item[0] + '\x00' + intToBinStr(item[1], 4))
    with open(filename+'.syn', 'wb') as f:
      f.write(synStr)
  ifoStr = '''StarDict\'s dict ifo file\nversion=3.0.0
bookname=%s
wordcount=%d
idxfilesize=%d
sametypesequence=%s
'''%(new_lines_2_space(g.getInfo('name')), len(g.data), len(idxStr), ('h' if richText else 'm'))
  if len(alternates) > 0:
    ifoStr += 'synwordcount={0}\n'.format(len(alternates))
  for key in infoKeys:
    if key in ('bookname', 'wordcount', 'idxfilesize', 'sametypesequence'):
      continue
    value = g.getInfo(key)
    if value == '':
      continue
    if key == 'description':
      ifoStr += '{0}={1}\n'.format(key, new_line_2_br(value))
    else:
      ifoStr += '{0}={1}\n'.format(key, new_lines_2_space(value))
  with open(filename+'.ifo', 'wb') as f:
    f.write(ifoStr)
  if dictZip:
    runDictzip(filename)
  resPath = os.path.join(os.path.dirname(filename), 'res')
  copy_resources(glos.resPath, resPath)

def copy_resources(fromPath, toPath):
  """Copy resource files from fromPath to toPath.
  """
  fromPath = os.path.abspath(fromPath)
  toPath = os.path.abspath(toPath)
  if fromPath == toPath:
    return
  if not os.path.isdir(fromPath):
    return
  if len(os.listdir(fromPath))==0:
    return
  if os.path.exists(toPath):
    if len(os.listdir(toPath)) > 0:
      printAsError('Output resource directory is not empty: "{0}". Resources will not be copied! '
        'Clean the output directory before running the converter.'\
        .format(toPath))
      return
    os.rmdir(toPath)
  shutil.copytree(fromPath, toPath)
  
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

def new_lines_2_space(text):
  return re.sub("[\n\r]+", ' ', text)

def new_line_2_br(text):
  return re.sub("\n\r?|\r\n?", "<br>", text)
