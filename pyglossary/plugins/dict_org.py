# -*- coding: utf-8 -*-

from formats_common import *

enable = True
format = 'DictOrg'
description = 'DICT.org file format (.index)'
extentions = ['.index']
readOptions = []
writeOptions = [
    'sort',
    'dictzip',
    'install',
]


b64_chars = b'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
b64_chars_ord = dict(zip(b64_chars, range(len(b64_chars))))

def intToIndexStr(n, retry=0):
    chars = []
    while True:
        chars.append(b64_chars[n & 0x3f])
        n >>= 6
        if n==0:
            break
    return bytes(reversed(chars))

def indexStrToInt(st):
    n = 0
    for i, c in enumerate(reversed(list(st))):
        k = b64_chars_ord[c]
        assert 0 <= k < 64
        n |= (k << 6*i)
        ## += is safe
        ## |= is probably a little faster
        ## |= is also safe because n has lesser that 6*i bits. why? ## FIXME
    return n

def installToDictd(filename, title=''):## filename is without extention (neither .index or .dict or .dict.dz)
    import shutil
    log.info('Installing %r to DICTD server'%filename)
    shutil.copy(filename + '.index', '/usr/share/dictd')
    if os.path.isfile(filename + '.dict.dz'):
        dictPostfix = '.dict.dz'
    elif os.path.isfile(filename + '.dict'):
        dictPostfix = '.dict'
    else:
        log.error('No .dict file, could not install dictd file %r'%filename)
        return False
    shutil.copy(filename + dictPostfix, '/usr/share/dictd')

    fname = split(filename)[1]
    if not title:
        title = fname
    open('/var/lib/dictd/db.list', 'ab').write('''

database %s
{
    data /usr/share/dictd/%s%s
    index /usr/share/dictd/%s.index
}
'''%(title, fname, dictPostfix, fname))


class Reader(object):
    def __init__(self, glos):
        self._glos = glos
        self._filename = ''
        self._indexFp = None
        self._dictFp = None
        self._leadingLinesCount = 0
        self._len = None
    def open(self, filename):
        import gzip
        if filename.endswith('.index'):
            filename = filename[:-6]
        self._filename = filename
        self._indexFp = open(filename+'.index', 'rb')
        if os.path.isfile(filename+'.dict.dz'):
            self._dictFp = gzip.open(filename+'.dict.dz')
        else:
            self._dictFp = open(filename+'.dict', 'rb')
    def close(self):
        try:
            self._indexFp.close()
        except:
            log.exception('error while closing index file')
        self._indexFp = None
        try:
            self._dictFp.close()
        except:
            log.exception('error while closing dict file')
        self._dictFp = None
    def __len__(self):
        if self._len is None:
            log.warning('Try not to use len(reader) as it takes extra time')
            self._len = fileCountLines(self._filename+'.index') - self._leadingLinesCount
        return self._len
    __iter__ = lambda self: self
    def __iter__(self):
        if not self._indexFp:
            log.error('reader is not open, can not iterate')
            raise StopIteration
        ## read info from header of dict file ## FIXME
        word = ''
        sumLen = 0
        wrongSortedN = 0
        wordCount = 0
        ############################## IMPORTANT PART ############################
        for line in self._indexFp:
            line = line.strip()
            if not line:
                continue
            parts = line.split(b'\t')
            assert len(parts)==3
            word = parts[0].replace(b'<BR>', b'\\n')\
                           .replace(b'<br>', b'\\n')
            sumLen2 = indexStrToInt(parts[1])
            if sumLen2 != sumLen:
                wrongSortedN += 1
            sumLen = sumLen2
            defiLen = indexStrToInt(parts[2])
            self._dictFp.seek(sumLen)
            defi = self._dictFp.read(defiLen)
            defi = defi.replace(b'<BR>', b'\n').replace(b'<br>', b'\n')
            sumLen += defiLen
            yield Entry(toStr(word), toStr(defi)) ; wordCount += 1
        ############################################################################
        if wrongSortedN>0:
            log.warning('Warning: wrong sorting count: %d'%wrongSortedN)
        self._len = wordCount


def write(glos, filename, sort=True, dictzip=True, install=True):## FIXME
    from pyglossary.text_utils import runDictzip
    if sort:
        glos = glos.copy()
        glos.sortWords()
    (filename_nox, ext) = splitext(filename)
    if ext.lower()=='.index':
        filename = filename_nox
    indexFd = open(filename+'.index', 'wb')
    dictFd = open(filename+'.dict', 'wb')
    dictMark = 0
    for entry in glos:
        word = toBytes(entry.getWord())
        defi = toBytes(entry.getDefi())
        lm = len(defi)
        indexFd.write(word + b'\t' + intToIndexStr(dictMark) + b'\t' + intToIndexStr(lm) + b'\n')## FIXME
        dictFd.write(toBytes(defi))
        dictMark += lm
    indexFd.close()
    dictFd.close()
    #for key in glos.infoKeys():
    #    value = glos.getInfo(key)
    #    if value!='':
    #        pass ## FIXME
    if dictzip:
        runDictzip(filename)
    if install:
        installToDictd(filename, glos.getInfo('name').replace(' ', '_'))

