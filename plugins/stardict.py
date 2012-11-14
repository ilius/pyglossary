# -*- coding: utf-8 -*-
from formats_common import *

enable = True
format = 'Stardict'
description = 'StarDict (ifo)'
extentions = ['.ifo']
readOptions = []
writeOptions = ['resOverwrite']
supportsAlternates = True

import sys, os, re, shutil, os.path
from os.path import isfile
sys.path.append('/usr/share/pyglossary/src')

from text_utils import intToBinStr, binStrToInt, runDictzip, printAsError

infoKeys = ('bookname', 'author', 'email', 'website', 'description', 'date')


def read(glos, filename):
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
    sumLen0 = 0
    i = 0
    wrongSorted = []
    ########### Loading idx file (IMPORTANT PART)
    ## %3 to %5 faster than older method (wihout str.find)
    wi = 0
    while True:
        i = idxStr.find('\x00', wi)
        if i < 0:
            break
        word = idxStr[wi:i].replace('<BR>', '\\n').replace('<br>', '\\n')
        sumLen = binStrToInt(idxStr[i+1:i+5])
        if sumLen != sumLen0:
            wrongSorted.append(word)
            sumLen0 = sumLen
        defiLen = binStrToInt(idxStr[i+5:i+9])
        dictFd.seek(sumLen)
        defi = dictFd.read(defiLen).replace('<BR>', '\n').replace('<br>', '\n')
        glos.data.append((word, defi, {}))
        sumLen0 += defiLen
        wi = i + 9
    #########################
    if len(wrongSorted)>0:
        print('Warning: wrong sorting count: %d'%len(wrongSorted))
    ####### Loading syn file
    if isfile(filename+'.syn'):
        synStr = open(filename+'.syn', 'rb').read()
        wi = 0
        while True:
            i = synStr.find('\x00', wi)
            if i < 0:
                break
            alt = synStr[wi:i]
            wIndex = binStrToInt(synStr[i+1:i+5])
            try:
                item = glos.data[wIndex]
            except IndexError:
                print 'invalid word index %s in syn file'%wIndex
            else:
                try:
                    item[2]['alts'].append(alt)
                except KeyError:
                    item[2]['alts'] = [alt]
            wi = i + 5



def write(glos, filename, dictZip=True, richText=True, resOverwrite=False):
    g = glos.copy()
    g.data.sort(stardict_strcmp, lambda x: x[0])
    
    if os.path.splitext(filename)[1].lower() == '.ifo':
        fileBasePath=os.path.splitext(filename)[0]
    elif filename[-1]==os.sep:
        if not os.path.isdir(filename):
            os.makedirs(filename)
        fileBasePath = os.path.join(filename, os.path.split(filename[:-1])[-1])
    elif os.path.isdir(filename):
        fileBasePath = os.path.join(filename, os.path.split(filename)[-1])
    
    if GlossaryHasAdditionalDefinitions(g):
        writeGeneral(g, fileBasePath, 'h' if richText else 'm')
    else:
        writeWithSameTypeSequence(g, fileBasePath, 'h' if richText else 'm')
    
    if dictZip:
        runDictzip(fileBasePath)
    copy_resources(
        glos.resPath,
        os.path.join(os.path.dirname(fileBasePath), 'res'),
        resOverwrite
    )

def writeWithSameTypeSequence(g, fileBasePath, articleFormat):
    """Build StarDict dictionary with sametypesequence option specified.
    Every item definition consists of a single article.
    All articles have the same format, specified in articleFormat parameter.
    
    Parameters:
    g - glossary, g.data are sorted
    fileBasePath - full file path without extension
    articleFormat - format of article definition: h - html, m - plain text
    """
    dictMark = 0
    idxStr = ''
    dictStr = ''
    alternates = [] # contains tuples ('alternate', index-of-word)
    for i in xrange(len(g.data)):
        item = g.data[i]
        word, defi = item[:2]
        if len(item) > 2 and 'alts' in item[2]:
            alternates += [(x, i) for x in item[2]['alts']]
        dictStr += defi
        defiLen = len(defi)
        idxStr += word + '\x00' + intToBinStr(dictMark, 4) + intToBinStr(defiLen, 4)
        dictMark += defiLen
    with open(fileBasePath+'.dict', 'wb') as f:
        f.write(dictStr)
    with open(fileBasePath+'.idx', 'wb') as f:
        f.write(idxStr)
    indexFileSize = len(idxStr)
    del idxStr, dictStr
    
    writeAlternates(alternates, fileBasePath)
    writeIfo(g, fileBasePath, indexFileSize, len(alternates), articleFormat)

def writeGeneral(g, fileBasePath, articleFormat):
    """Build StarDict dictionary in general case.
    Every item definition may consist of an arbitrary number of articles.
    sametypesequence option is not used.
    
    Parameters:
    g - glossary, g.data are sorted
    fileBasePath - full file path without extension
    articleFormat - format of article definition: h - html, m - plain text
    """
    assert len(articleFormat) == 1
    dictMark = 0
    idxStr = ''
    dictStr = ''
    alternates = [] # contains tuples ('alternate', index-of-word)
    for i in xrange(len(g.data)):
        item = g.data[i]
        word, defi = item[:2]
        if len(item) > 2 and 'alts' in item[2]:
            alternates += [(x, i) for x in item[2]['alts']]
        dictStr += articleFormat
        dictStr += defi + '\x00'
        dataLen = 1 + len(defi) + 1
        if len(item) > 2 and 'defis' in item[2]:
            for defi in item[2]['defis']:
                dictStr += articleFormat
                dictStr += defi + '\x00'
                dataLen += 1 + len(defi) + 1
        idxStr += word + '\x00' + intToBinStr(dictMark, 4) + intToBinStr(dataLen, 4)
        dictMark += dataLen
    with open(fileBasePath+'.dict', 'wb') as f:
        f.write(dictStr)
    with open(fileBasePath+'.idx', 'wb') as f:
        f.write(idxStr)
    indexFileSize = len(idxStr)
    del idxStr, dictStr
    
    writeAlternates(alternates, fileBasePath)
    writeIfo(g, fileBasePath, indexFileSize, len(alternates))

def writeAlternates(alternates, fileBasePath):
    """Build .syn file
    """
    if len(alternates) > 0:
        alternates.sort(stardict_strcmp, lambda x: x[0])
        synStr = ''
        for item in alternates:
            synStr += item[0] + '\x00' + intToBinStr(item[1], 4)
        with open(fileBasePath+'.syn', 'wb') as f:
            f.write(synStr)
        del synStr

def writeIfo(g, fileBasePath, indexFileSize, synwordcount, sametypesequence = None):
    """Build .ifo file
    """
    ifoStr = "StarDict's dict ifo file\n" \
        + "version=3.0.0\n" \
        + "bookname={0}\n".format(new_lines_2_space(g.getInfo('name'))) \
        + "wordcount={0}\n".format(len(g.data)) \
        + "idxfilesize={0}\n".format(indexFileSize)
    if sametypesequence != None:
        ifoStr += "sametypesequence={0}\n".format(sametypesequence)
    if synwordcount > 0:
        ifoStr += 'synwordcount={0}\n'.format(synwordcount)
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
    with open(fileBasePath+'.ifo', 'wb') as f:
        f.write(ifoStr)
    del ifoStr
    
def copy_resources(fromPath, toPath, overwrite):
    '''Copy resource files from fromPath to toPath.
    '''
    if not fromPath:
        return
    fromPath = os.path.abspath(fromPath)
    toPath = os.path.abspath(toPath)
    if fromPath == toPath:
        return
    if not os.path.isdir(fromPath):
        return
    if len(os.listdir(fromPath))==0:
        return
    if overwrite and os.path.exists(toPath):
        shutil.rmtree(toPath)
    if os.path.exists(toPath):
        if len(os.listdir(toPath)) > 0:
            printAsError(
'''Output resource directory is not empty: "{0}". Resources will not be copied!
Clean the output directory before running the converter or pass option: --write-options=res-overwrite=True.'''\
.format(toPath)
            )
            return
        os.rmdir(toPath)
    shutil.copytree(fromPath, toPath)

def GlossaryHasAdditionalDefinitions(glos):
    """Search for additional definitions in the glossary.
    We need to know if the glossary contains additional definitions 
    to make the decision on the format of the StarDict dictionary.
    """
    for rec in glos.data:
        if len(rec) > 2 and 'defis' in rec[2]:
            return True
    return False
    
def read_ext(glos, filename):
    ## This method uses module provided by dictconv, but dictconv is very slow for reading from stardict db!
    ## therefore this method in not used by GUI now.
    ## and binary module "_stardict" is deleted.
    ## If you want to use it, compile it yourglos, or get it from an older version of PyGlossary (version 2008.08.30)
    glos.data = []
    import _stardict
    db = _stardict.new_StarDict(filename)
    _stardict.PySwigIterator_swigregister(db)
    glos.setInfo('title', _stardict.StarDict_bookname(db))
    glos.setInfo('author', _stardict.StarDict_bookname(db))
    glos.setInfo('title', _stardict.StarDict_bookname(db))
    ## geting words:
    idxStr = open(filename[:-4]+'.idx').read()
    words=[]
    #''' # get words list by python codes.
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
    ''' # get words list using _stardict module.
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
    '''
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


def isAsciiUpper(c):
    'imitate ISUPPER macro of glib library gstrfuncs.c file'
    return ord(c) >= ord('A') and ord(c) <= ord('Z')

def asciiLower(c):
    '''imitate TOLOWER macro of glib library gstrfuncs.c file

    This function converts upper case Latin letters to corresponding lower case letters,
    other chars are not changed.

    c must be non-Unicode string of length 1.
    You may apply this function to individual bytes of non-Unicode string.
    The following encodings are allowed: single byte encoding like koi8-r, cp1250, cp1251, cp1252, etc,
    and utf-8 encoding.

    Attention! Python Standard Library provides str.lower() method.
    It is not a correct replacement for this function.
    For non-unicode string str.lower() is locale dependent, it not only converts Latin
    letters to lower case, but also locale specific letters will be converted.
    '''
    if isAsciiUpper(c):
        return chr((ord(c) - ord('A')) + ord('a'))
    else:
        return c

def ascii_strcasecmp(s1, s2):
    'imitate g_ascii_strcasecmp function of glib library gstrfuncs.c file'
    commonLen = min(len(s1), len(s2))
    for i in xrange(commonLen):
        c1 = ord(asciiLower(s1[i]))
        c2 = ord(asciiLower(s2[i]))
        if c1 != c2:
            return c1 - c2
    return len(s1) - len(s2)

def strcmp(s1, s2):
    '''imitate strcmp of standard C library

    Attention! You may have a temptation to replace this function with built-in cmp() function.
    Hold on! Most probably these two function behave identically now, but cmp does not
    document how it compares strings. There is no guaranty it will not be changed in future.
    Since we need predictable sorting order in StarDict dictionary, we need to preserve
    this function despite the fact there are other ways to implement it.
    '''
    commonLen = min(len(s1), len(s2))
    for i in xrange(commonLen):
        c1 = ord(s1[i])
        c2 = ord(s2[i])
        if c1 != c2:
            return c1 - c2
    return len(s1) - len(s2)

def stardict_strcmp(s1, s2):
    '''
        use this function to sort index items in StarDict dictionary
        s1 and s2 must be utf-8 encoded strings
    '''
    a = ascii_strcasecmp(s1, s2)
    if a == 0:
        return strcmp(s1, s2)
    else:
        return a

def new_lines_2_space(text):
    return re.sub('[\n\r]+', ' ', text)

def new_line_2_br(text):
    return re.sub('\n\r?|\r\n?', '<br>', text)

