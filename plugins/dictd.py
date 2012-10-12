# -*- coding: utf-8 -*-

from formats_common import *

enable = True
format = 'Dictd'
description = 'DICTD dictionary server (.index)'
extentions = ['.index']
readOptions = []
writeOptions = [
    'sort',
    'dictZip',
    'install',
]

from text_utils import chBaseIntToList, runDictzip
import shutil

b64_chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'

def intToIndexStr(n, retry=0):
    chars = []
    while True:
        chars.append(b64_chars[n & 0x3f])
        n >>= 6
        if n==0:
            break
    return ''.join(reversed(chars))

def indexStrToInt(st):
    n = 0
    for i, c in enumerate(reversed(list(st))):
        k = b64_chars.find(c)
        assert 0 <= k < 64
        n |= (k << 6*i)
        ## += is safe
        ## |= is probably a little faster
        ## |= is also safe because n has lesser that 6*i bits. why? ## FIXME
    return n

def installToDictd(filename, title=''):## filename is without extention (neither .index or .dict or .dict.dz)
    print 'Installing %r to DICTD server'%filename
    shutil.copy(filename + '.index', '/usr/share/dictd')
    if os.path.isfile(filename + '.dict.dz'):
        dictPostfix = '.dict.dz'
    elif os.path.isfile(filename + '.dict'):
        dictPostfix = '.dict'
    else:
        printAsError('No .dict file, could not install dictd file %r'%filename)
        return False
    shutil.copy(filename + dictPostfix, '/usr/share/dictd')

    fname = path_split(filename)[1]
    if not title:
        title = fname
    open('/var/lib/dictd/db.list', 'ab').write('''

database %s
{
    data /usr/share/dictd/%s%s
    index /usr/share/dictd/%s.index
}
'''%(title, fname, dictPostfix, fname))


def read(glos, filename):
    if filename.endswith('.index'):
        filename = filename[:-6]
    idxStr = open(filename+'.index', 'rb').read()
    if os.path.isfile(filename+'.dict.dz'):
        import gzip
        dictStr = gzip.open(filename+'.dict.dz').read()
    else:
        dictStr = open(filename+'.dict', 'rb').read()
    ## read info from header of dict file ## FIXME
    glos.data = []
    word = ''
    sumLen = 0
    wrongSorted = []
    ############################## IMPORTANT PART ############################
    for line in idxStr.split('\n'):
        line = line.strip()
        if not line:
            continue
        parts = line.split('\t')
        assert len(parts)==3
        word = parts[0].replace('<BR>', '\\n')\
                        .replace('<br>', '\\n')
        sumLen2 = indexStrToInt(parts[1])
        if sumLen2 != sumLen:
            wrongSorted.append(word)
        sumLen = sumLen2
        defiLen = indexStrToInt(parts[2])
        defi = dictStr[sumLen:sumLen+defiLen].replace('<BR>', '\n')\
                                             .replace('<br>', '\n')
        glos.data.append((word, defi))
        sumLen += defiLen
    ############################################################################
    if len(wrongSorted)>0:
        print('Warning: wrong sorting count: %d'%len(wrongSorted))



def write(glos, filename, sort=True, dictZip=True, install=True):## FIXME
    if sort:
        glos = glos.copy()
        glos.data.sort()
    (filename_nox, ext) = splitext(filename)
    if ext.lower()=='.index':
        filename = filename_nox
    indexFd = open(filename+'.index', 'wb')
    dictFd = open(filename+'.dict', 'wb')
    dictMark = 0
    for item in glos.data:
        (word, defi) = item[:2]
        lm = len(defi)
        indexFd.write(word + '\t' + intToIndexStr(dictMark) + '\t' + intToIndexStr(lm) + '\n')## FIXME
        dictFd.write(defi)
        dictMark += lm
    indexFd.close()
    dictFd.close()
    #for key in glos.infoKeys():
    #    value = glos.getInfo(key)
    #    if value!='':
    #        pass ## FIXME
    if dictZip:
        runDictzip(filename)
    if install:
        installToDictd(filename, glos.getInfo('name').replace(' ', '_'))

