# -*- coding: utf-8 -*-
## glossary.py
##
## Copyright © 2008-2016 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
## This file is part of PyGlossary project, http://github.com/ilius/pyglossary
##
## This program is a free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 3, or (at your option)
## any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License along
## with this program. Or on Debian systems, from /usr/share/common-licenses/GPL
## If not, see <http://www.gnu.org/licenses/gpl.txt>.

from . import VERSION

homePage = 'http://github.com/ilius/pyglossary'

import os, sys, platform, time, subprocess, shutil, re
from os.path import split, join, splitext, isdir, dirname, basename
import logging
import pkgutil
import string
from collections import Counter
from collections import OrderedDict as odict

from . import core
from .entry import Entry
from .entry_filters import *
from .sort_stream import hsortStream

from .text_utils import (
    fixUtf8,
    takeStrWords,
    findAll,
    addDefaultOptions,
)

import warnings
warnings.resetwarnings() ## ??????

log = logging.getLogger('root')

psys = platform.system()


if os.sep=='/': ## Operating system is Unix-Like
    homeDir = os.getenv('HOME')
    user = os.getenv('USER')
    tmpDir = '/tmp'
    ## os.name == 'posix' ## ????
    if psys=='Darwin':## MacOS X
        confPath = homeDir + '/Library/Preferences/PyGlossary' ## OR '/Library/PyGlossary'
        ## os.environ['OSTYPE'] == 'darwin10.0'
        ## os.environ['MACHTYPE'] == 'x86_64-apple-darwin10.0'
        ## platform.dist() == ('', '', '')
        ## platform.release() == '10.3.0'
    else:## GNU/Linux, ...
        confPath = homeDir + '/.pyglossary'
elif os.sep=='\\': ## Operating system is Windows
    homeDir = os.getenv('HOMEDRIVE') + os.getenv('HOMEPATH')
    user = os.getenv('USERNAME')
    tmpDir = os.getenv('TEMP')
    confPath = os.getenv('APPDATA') + '\\' + 'PyGlossary'
else:
    raise RuntimeError('Unknown path seperator(os.sep=="%s"), unknown operating system!'%os.sep)

get_ext = lambda path: splitext(path)[1].lower()




class Glossary(object):
    """
    Direct access to glos.data is droped
    Use `glos.addEntry(word, defi, [defiFormat])`
        where both word and defi can be list (including alternates) or string
    See help(glos.addEntry)
    
    Use `for entry in glos:` to iterate over entries (glossary data)
    See help(pyglossary.entry.Entry) for details

    """

    ## Should be changed according to plugins? FIXME
    infoKeysAliasDict = {
        'title': 'name',
        'bookname': 'name',
        'dbname': 'name',
        ##
        'sourcelang': 'sourceLang',
        'inputlang': 'sourceLang',
        'origlang': 'sourceLang',
        ##
        'targetlang': 'targetLang',
        'outputlang': 'targetLang',
        'destlang': 'targetLang',
        ##
        'license': 'copyright',
    }
    readFormats = []
    writeFormats = []
    readFunctions = {}
    readerClasses = {}
    writeFunctions = {}
    formatsDesc = {}
    formatsExt = {}
    formatsReadOptions = {}
    formatsWriteOptions = {}
    readExt = []
    writeExt = []
    readDesc = []
    writeDesc = []
    descFormat = {}
    descExt = {}
    extFormat = {}

    @classmethod
    def loadPlugins(cls, directory):
        """executed on startup.  as name implies, loads plugins from directory."""
        log.debug('loading plugins from directory: %r' % directory)
        if not isdir(directory):
            log.error('invalid plugin directory: %r' % directory)
            return

        sys.path.append(directory)
        for _, plugin, _ in pkgutil.iter_modules([directory]):
            cls.loadPlugin(plugin)

    @classmethod
    def loadPlugin(cls, pluginName):
        log.debug('loading plugin %s' % pluginName)
        try:
            plugin = __import__(pluginName)
        except (ImportError, SyntaxError) as e:
            log.error('error while importing plugin %s' % pluginName, exc_info=1)
            return

        if (not hasattr(plugin, 'enable')) or (not plugin.enable):
            log.debug('plugin disabled or not a plugin: %s.  skipping...' % pluginName)
            return

        format = plugin.format

        extentions = plugin.extentions
        # FIXME: deprecate non-tuple values in plugin.extentions
        if isinstance(extentions, str):
            extentions = (extentions,)
        elif not isinstance(extentions, tuple):
            extentions = tuple(extentions)

        if hasattr(plugin, 'description'):
            desc = plugin.description
        else:
            desc = '%s (%s)' % (format, extentions[0])

        cls.descFormat[desc] = format
        cls.descExt[desc] = extentions[0]
        for ext in extentions:
            cls.extFormat[ext] = format
        cls.formatsExt[format] = extentions
        cls.formatsDesc[format] = desc

        ###################################################

        hasReadSupport = False
        try:
            Reader = plugin.Reader
        except AttributeError:
            pass
        else:
            for attr in (
                '__init__',
                'open',
                'close',
                '__len__',
                '__iter__',
            ):
                if not hasattr(Reader, attr):
                    log.error('invalid Reader class in "%s" plugin, no "%s" method'%(
                        format,
                        attr,
                    ))
                    break
            else:
                cls.readerClasses[format] = Reader
                hasReadSupport = True

        try:
            cls.readFunctions[format] = plugin.read
        except AttributeError:
            pass
        else:
            hasReadSupport = True

        if hasReadSupport:
            cls.readFormats.append(format)
            cls.readExt.append(extentions)
            cls.readDesc.append(desc)
            cls.formatsReadOptions[format] = getattr(plugin, 'readOptions', [])

        ###################################################

        if hasattr(plugin, 'write'):
            cls.writeFunctions[format] = plugin.write
            cls.writeFormats.append(format)
            cls.writeExt.append(extentions)
            cls.writeDesc.append(desc)
            cls.formatsWriteOptions[format] = getattr(plugin, 'writeOptions', [])

        log.debug('plugin loaded OK: %s' % pluginName)
        return plugin

    def clear(self):
        self.info = odict()

        self._data = []
        self._iter = None

        self.filename = ''
        self.resPath = ''
        self._defaultDefiFormat = 'm'

    def __init__(self, info=None, ui=None, filename='', resPath=''):
        """
            info: OrderedDict instance, or None
                  no need to copy OrderedDict instance, we will not reference to it
        """
        self.info = odict()
        if info:
            for key, value in info.items():
                self.setInfo(key, value)

        self._data = []
        self._readers = []
        '''
        self._data is a list of tuples with length 2 or 3:
            (word, definition)
            (word, definition, defiFormat)
            where both word and definition can be a string, or list (containing alternates)

            defiFormat: format of the definition:
                'm': plain text
                'h': html
                'x': xdxf
        '''
        self.ui = ui
        self.filename = filename
        self.resPath = resPath
        self._defaultDefiFormat = 'm'

        self.entryFilters = []
        self._iter = None

        self._sort = False
        self._sortKey = None

    def updateEntryFilters(self):
        self.entryFilters = []
        pref = getattr(self.ui, 'pref', {})

        self.entryFilters.append(StripEntryFilter(self))
        self.entryFilters.append(NonEmptyWordFilter(self))

        if pref.get('utf8_check', True):
            self.entryFilters.append(FixUnicodeFilter(self))

        if pref.get('lower', True):
            self.entryFilters.append(LowerWordFilter(self))

        self.entryFilters.append(LangEntryFilter(self))
        self.entryFilters.append(CleanEntryFilter(self))
        self.entryFilters.append(NonEmptyWordFilter(self))
        self.entryFilters.append(NonEmptyDefiFilter(self))


    __str__ = lambda self: 'glossary.Glossary'

    def addEntryObj(self, entry):
        self._data.append(entry.getRaw())

    def addEntry(self, word, defi, defiFormat=None):
        if defiFormat == self._defaultDefiFormat:
            defiFormat = None

        self.addEntryObj(Entry(word, defi, defiFormat))

    def _loadedEntryGen(self):
        for rawEntry in self._data:
            yield Entry.fromRaw(
                rawEntry,
                defaultDefiFormat=self._defaultDefiFormat
            )

    def _readersEntryGen(self):
        for reader in self._readers:
            for entry in reader:
                yield entry
            reader.close()

    def _applyEntryFiltersGen(self, gen):
        for entry in gen:
            if not entry:
                continue
            for entryFilter in self.entryFilters:
                entry = entryFilter.run(entry)
                if not entry:
                    break
            else:
                yield entry

    def __iter__(self):
        if not self._iter:
            log.error('Trying to iterate over a blank Glossary, must call `glos.read` first')
            return []
        return self._iter

    def iterEntryBuckets(self, size):
        """
            iterate over buckets of entries, with size `size`
            For example:
                for bucket in glos.iterEntryBuckets(100):
                    assert len(bucket) == 100
                    for entry in bucket:
                        print(entry.getWord())
                    print('-----------------')
        """
        bucket = []
        for entry in self:
            if len(bucket) >= size:
                yield bucket
                bucket = []
            bucket.append(entry)
        yield bucket

    def setDefaultDefiFormat(self, defiFormat):
        self._defaultDefiFormat = defiFormat

    def getDefaultDefiFormat(self):
        return self._defaultDefiFormat


    __len__ = lambda self: len(self._data) + sum(
        len(reader) for reader in self._readers
    )

    def copy(self):
        newGlos = Glossary(
            info = self.info,## no need to copy
            ui = self.ui, ## FIXME
            filename = self.filename,
            resPath = self.resPath,
        )
        #newGlos.__Glossary_data = deepcopy(self._data)
        for entry in self:
            newGlos.addEntryObj(entry)
        return newGlos

    def infoKeys(self):
        return list(self.info.keys())

    def getMostUsedDefiFormats(self, count=None):
        return Counter([
            entry.getDefiFormat() \
            for entry in self
        ]).most_common(count)

    #def formatInfoKeys(self, format):## FIXME

    def getInfo(self, key):
        key = str(key)

        try:
            key = self.infoKeysAliasDict[key.lower()]
        except KeyError:
            #log.warning('uknown info key: %s'%key)## FIXME
            pass

        return self.info.get(key, '')## '' or None as defaul?## FIXME
        
    def setInfo(self, key, value):
        ## FIXME
        origKey = key
        key = fixUtf8(key)
        value = fixUtf8(value)

        try:
            key = self.infoKeysAliasDict[key.lower()]
        except KeyError:
            #log.warning('uknown info key: %s'%key)## FIXME
            pass

        if origKey != key:
            log.debug('setInfo: %s -> %s'%(origKey, key))

        self.info[key] = value

    def read(
        self,
        filename,
        format='',
        direct=False,
        sort=None,
        sortKey=None,
        **options
    ):
        """
            filename (str): name/path of input file
            format (str): name of inout format, or '' to detect from file extention
            direct (bool): enable direct mode
            sort (bool): True (enable sorting), False (disable sorting), None (auto, get from UI)
            sortKey (callable or None):
                key function for sorting
                takes a word as argument, which is str or list (with alternates)
        """
        self.updateEntryFilters()
        pref = getattr(self.ui, 'pref', {})
        if sort is None:
            sort = pref.get('sort', False)
        self._sort = sort
        self._sortKey = sortKey
        ###
        delFile=False
        ext = splitext(filename)[1]
        ext = ext.lower()
        if ext in ('.gz', '.bz2', '.zip'):
            if ext=='.bz2':
                (output, error) = subprocess.Popen(
                    ['bzip2', '-dk', filename],
                    stdout=subprocess.PIPE,
                ).communicate()
                ## -k ==> keep original bz2 file
                ## bunzip2 ~= bzip2 -d
                if error:
                    log.error('%s\nfail to decompress file "%s"'%(error, filename))
                    return False
                else:
                    filename = filename[:-4]
                    ext = splitext(filename)[1]
                    delFile = True
            elif ext=='.gz':
                (output, error) = subprocess.Popen(
                    ['gzip', '-dc', filename],
                    stdout=subprocess.PIPE,
                ).communicate()
                ## -c ==> write to stdout (because we want to keep original gz file)
                ## gunzip ~= gzip -d
                if error:
                    log.error('%s\nfail to decompress file "%s"'%(error, filename))
                    return False
                else:
                    filename = filename[:-3]
                    open(filename, 'w').write(output)
                    ext = splitext(filename)[1]
                    delFile = True
            elif ext=='.zip':
                (output, error) = subprocess.Popen(
                    ['unzip', filename, '-d', dirname(filename)],
                    stdout=subprocess.PIPE,
                ).communicate()
                if error:
                    log.error('%s\nfail to decompress file "%s"'%(error, filename))
                    return False
                else:
                    filename = filename[:-4]
                    ext = splitext(filename)[1]
                    delFile = True
        if not format:
            for key in Glossary.formatsExt.keys():
                if ext in Glossary.formatsExt[key]:
                    format = key
            if not format:
                #if delFile:
                #    os.remove(filename)
                log.error('Unknown extension "%s" for read support!'%ext)
                return False
        validOptionKeys = self.formatsReadOptions[format]
        for key in options.keys():
            if not key in validOptionKeys:
                log.error('Invalid read option "%s" given for %s format'%(key, format))
                del options[key]

        filenameNoExt, ext = splitext(filename)
        if not ext.lower() in self.formatsExt[format]:
            filenameNoExt = filename

        self.filename = filenameNoExt
        if self.getInfo('name') == '':
            self.setInfo('name', split(filename)[1])
        
        try:
            Reader = self.readerClasses[format]
        except KeyError:
            if direct:
                log.warning('no `Reader` class found in %s plugin, falling back to indirect mode'%format)
                direct = False
            result = self.readFunctions[format].__call__(
                self,
                filename,
                **options
            )
            #if not result:## FIXME
            #    return False
            if delFile:
                os.remove(filename)
        else:
            reader = Reader(self)
            reader.open(filename, **options)
            if direct:
                self._readers.append(reader)
                log.info(
                    'using Reader class from %s plugin for direct conversion without loading into memory'%format
                )
            else:
                self.loadReader(reader)


        if sort and not direct:
            self.sortWords(key=sortKey)

        self._updateGen(
            direct=direct,
        )

        return True

    def loadReader(self, reader):
        """
            iterates over `reader` object and loads the whole data into self._data
            must call `reader.open(filename)` before calling this function
        """
        for entry in reader:
            if not entry:
                continue
            self.addEntryObj(entry)
        reader.close()
        return True

    def inactivateDirectMode(self):
        for reader in self._readers:
            self.loadReader(reader)
        self._readers = []
        self._updateGen(direct=False)

    def _updateGen(self, direct=False):
        """
            direct: True (enable direct mode), False (disable direct mode)
        """
        pref = getattr(self.ui, 'pref', {})
        if direct:
            gen = self._readersEntryGen()
            if self._sort:
                sortKey = self._sortKey
                cacheSize = pref.get('sort_cache_size', 1000)## FIXME
                log.info('stream sorting enabled, cache size: %s'%cacheSize)
                if sortKey:
                    sortEntryKey = lambda entry: sortKey(entry.getWord())
                else:
                    sortEntryKey = lambda entry: entry.getWord()
                gen = hsortStream(
                    gen,
                    cacheSize,
                    key=sortEntryKey,
                )
        else:
            gen = self._loadedEntryGen()

        self._iter = self._applyEntryFiltersGen(gen)

    def write(self, filename='', format='', **options):
        if not filename:
            filename = self.filename
        if not filename:
            log.error('Invalid filename %r'%filename)
            return False
        ext = ''
        (filenameNoExt, fext) = splitext(filename)
        fext = fext.lower()
        if fext in ('.gz', '.bz2', '.zip'):
            zipExt = fext
            filename = filenameNoExt
            fext = splitext(filename)[1].lower()
        else:
            zipExt = ''
        del filenameNoExt
        if format:
            try:
                ext = Glossary.formatsExt[format][0]
            except KeyError:
                log.exception('no file extention found for file format %s'%format)
                format = '' ## FIXME
        if not format:
            items = Glossary.formatsExt.items()
            for (fmt, extList) in items:
                for e in extList:
                    if format==e[1:] or format==e:
                        format = fmt
                        ext = e
                        break
                if format:
                    break
            if not format:
                for (fmt, extList) in items:
                    if filename==fmt:
                        format = filename
                        ext = extList[0]
                        filename = self.filename + ext
                        break
                    for e in extList:
                        if filename==e[1:] or filename==e:
                            format = fmt
                            ext = e
                            filename = self.filename + ext
                            break
                    if format:
                        break
            if not format:
                for (fmt, extList) in items:
                    if fext in extList:
                        format = fmt
                        ext = fext
        if not format:
            log.error('Unable to detect write format!')
            return False
        if isdir(filename):
            # write to directory, use filename (not filepath) of input file.
            filename = join(filename, basename(self.filename)+ext)
        validOptionKeys = self.formatsWriteOptions[format]
        for key in options.keys():
            if not key in validOptionKeys:
                log.error('Invalid write option "%s" given for %s format'%(key, format))
                del options[key]
        log.info('filename=%s'%filename)
        self.writeFunctions[format].__call__(self, filename, **options)

        if zipExt:
            try:
                os.remove('%s%s'%(filename, zipExt))
            except OSError:
                pass
            if zipExt=='.gz':
                (output, error) = subprocess.Popen(
                    ['gzip', filename],
                    stdout=subprocess.PIPE,
                ).communicate()
                if error:
                    log.error('%s\nfail to compress file "%s"'%(error, filename))
            elif zipExt=='.bz2':
                (output, error) = subprocess.Popen(
                    ['bzip2', filename],
                    stdout=subprocess.PIPE,
                ).communicate()
                if error:
                    log.error('%s\nfail to compress file "%s"'%(error, filename))
            elif zipExt=='.zip':
                (dirn, name) = split(filename)
                initCwd = os.getcwd()
                os.chdir(dirn)
                (output, error) = subprocess.Popen(
                    ['zip', filename+'.zip', name, '-m'],
                    stdout=subprocess.PIPE,
                ).communicate()
                if error:
                    log.error('%s\nfail to compress file "%s"'%(error, filename))
                os.chdir(initCwd)
        return True

    def writeTxt(
        self,
        sep,
        filename='',
        writeInfo=True,
        rplList=None,
        ext='.txt',
        head='',
        iterEntries=None,
        entryFilterFunc=None,
        outInfoKeysAliasDict=None,
        encoding='utf-8',
    ):
        if rplList is None:
            rplList = []
        if not filename:
            filename = self.filename + ext
        if not outInfoKeysAliasDict:
            outInfoKeysAliasDict = {}

        fp = open(filename, 'w', encoding=encoding)
        fp.write(head)
        if writeInfo:
            for key, desc in self.info.items():
                try:
                    key = outInfoKeysAliasDict[key]
                except KeyError:
                    pass
                for rpl in rplList:
                    desc = desc.replace(rpl[0], rpl[1])
                fp.write('##' + key + sep[0] + desc + sep[1])
        fp.flush()

        if not iterEntries:
            iterEntries = self
        for entry in iterEntries:
            if entryFilterFunc:
                entry = entryFilterFunc(entry)
                if not entry:
                    continue
            word = entry.getWord()
            defi = entry.getDefi()
            if word.startswith('#'):## FIXME
                continue
            #if self.getPref('enable_alts', True):## FIXME

            for rpl in rplList:
                defi = defi.replace(rpl[0], rpl[1])
            fp.write(word + sep[0] + defi + sep[1])
        fp.close()
        return True

    def writeTabfile(self, filename='', **kwargs):
        self.writeTxt(
            sep=('\t', '\n'),
            filename=filename,
            rplList=(
                ('\\', '\\\\'),
                ('\n', '\\n'),
                ('\t', '\\t'),
            ),
            ext='.txt',
            **kwargs
        )

    def writeDict(self, filename='', writeInfo=False):
        ## Used in '/usr/share/dict/' for some dictionarys such as 'ding'.
        self.writeTxt(
            (' :: ', '\n'),
            filename,
            writeInfo,
            (
                ('\n', '\\n'),
            ),
            '.dict',
        )


    ###################################################################

    def sortWords(self, key=None, reverse=False):
        ## call `inactivateDirectMode` to load entries into memory FIXME
        self.inactivateDirectMode()
        if key:
            entryKey = lambda x: key(
                x[0][0] if isinstance(x[0], (list, tuple)) else x[0]
            )
        else:
            entryKey = lambda x: \
                x[0][0] if isinstance(x[0], (list, tuple)) else x[0]
        self._data.sort(
            key=entryKey,
            reverse=reverse,
        )

    takeWords = lambda self: [item[0] for item in self._data]


    def takeOutputWords(self, opt=None):
        if opt is None:
            opt = {}
        words = sorted(takeStrWords(' '.join([item[1] for item in self._data]), opt))
        words = removeRepeats(words)
        return words

    getInputList = lambda self: [x[0] for x in self._data]

    getOutputList = lambda self: [x[1] for x in self._data]
        

    def attach(self, other):# only simplicity attach two glossaries (or more that others be as a list).
    # no ordering. Use when you split input words to two(or many) parts after ordering.
        try:
            other._data, other.info
        except AttributeError:
            if isinstance(other, (list, tuple)):
                if len(other)==0:
                    return self
                if len(other)==1:
                    return self.attach(other[0])
                return self.attach(other[0]).attach(other[1:])
            else:
                return self
        newName = '"%s" attached to "%s"'%(self.getInfo('name'), other.getInfo('name') )
        newGloss = Glossary(
            info = [
                ('name', newName),
            ],
        )
        newGloss.__Glossary_data = self._data + other.__Glossary_data ## FIXME
        ## here attach and set info of two glossary ## FIXME
        return newGloss

    def merge(self, other):
        try:
            other._data, other.info
        except AttributeError:
            if isinstance(other, (list, tuple)):
                if len(other)==0:
                    return self
                if len(other)==1:
                    return self.merge(other[0])
                return self.merge(other[0]).merge(other[1:])
            else:
                raise TypeError('bad argument given to merge! other="%s"'%other)
        newName = '"%s" merged with "%s"'%(
            self.getInfo('name'),
            other.getInfo('name'),
        )
        newGloss = Glossary(
            info = [
                ('name', newName),
            ],
        )
        newGloss.__Glossary_data = sorted(self._data + other.__Glossary_data) ## FIXME
        return newGloss


    def deepMerge(self, other, sep='\n'):
        ## merge two optional glossarys nicly. no repets in words of result glossary
        try:
            other._data, other.info
        except AttributeError:
            if isinstance(other, (list, tuple)):
                if len(other)==0:
                    return self
                if len(other)==1:
                    return self.deepMerge(other[0])
                return self.deepMerge(other[0]).deepMerge(other[1:])
            else:
                raise TypeError('bad argument given to deepMerge! other="%s"'%other)
        newName = '"%s" deep merged with "%s"'%( self.getInfo('name'), other.getInfo('name') )
        data = sorted(
            self._data + other.__Glossary_data,
            key = lambda x: x[0],## why? FIXME
        )
        n = len(data)
        i = 0
        while i < len(data)-1:
            if data[i][0] == data[i+1][0]:
                if data[i][1] != data[i+1][1]:
                    data[i] = (
                        data[i][0],
                        data[i][1] + sep + data[i+1][1],
                    )
                data.pop(i+1)
            else:
                i += 1
        return Glossary(
            info = [
                ('name', newName),
            ],
        )
        self._data = data


    def __add__(self, other):
        return self.merge(other)


    def searchWordInDef(self, st, opt):
        #seachs word 'st' in meanings(definitions) of the glossary 'self'
        opt = addDefaultOptions(opt, {
            'minRel': 0.0,
            'maxNum': 100,
            'sep': commaFa,
            'matchWord': True,
            'showRel': 'Percent',
        })
        sep = opt['sep']
        matchWord = opt['matchWord']
        maxNum = opt['maxNum']
        minRel = opt['minRel']
        defs = opt['includeDefs']
        outRel = []
        for item in self._data:
            (word, defi) = item[:2]
            defiParts = defi.split(sep)
            if not st in defi:
                continue
            rel = 0 ## relation value of word (as a float number between 0 and 1
            for part in defiParts:
                for ch in sch:
                    part = part.replace(ch, ' ')
                pRel = 0 # part relation
                if matchWord:
                    pNum = 0
                    partWords = takeStrWords(part)
                    pLen = len(partWords)
                    if pLen==0:
                        continue
                    for pw in partWords:
                        if pw == st:
                            pNum += 1
                    pRel = float(pNum)/pLen ## part relation
                else:
                    pLen = len(part.replace(' ', ''))
                    if pLen==0:
                        continue
                    pNum = len(findAll(part, st))*len(st)
                    pRel = float(pNum)/pLen ## part relation
                if pRel > rel:
                    rel = pRel
            if rel <= minRel:
                continue
            if defs:
                outRel.append((word, rel, defi))
            else:
                outRel.append((word, rel))
        #sortby_inplace(outRel, 1, True)##???
        outRel.sort(key=1, reverse=True)
        n = len(outRel)
        if n > maxNum > 0:
            outRel = outRel[:maxNum]
            n = maxNum
        num = 0
        out = []
        if defs:
            for j in range(n):
                numP = num
                (w, num, m) = outRel[j]
                m = m.replace('\n', '\\n').replace('\t', '\\t')
                onePer = int(1.0/num)
                if onePer == 1.0:
                    out.append('%s\\n%s'%(w, m))
                elif opt['showRel'] == 'Percent':
                    out.append('%s(%%%d)\\n%s'%(w, 100*num, m))
                elif opt['showRel'] == 'Percent At First':
                    if num == numP:
                        out.append('%s\\n%s'%(w, m))
                    else:
                        out.append('%s(%%%d)\\n%s'%(w, 100*num, m))
                else:
                    out.append('%s\\n%s'%(w, m))
            return out
        for j in range(n):
            numP = num
            (w, num) = outRel[j]
            onePer = int(1.0/num)
            if onePer == 1.0:
                out.append(w)
            elif opt['showRel'] == 'Percent':
                out.append('%s(%%%d)'%(w, 100*num))
            elif opt['showRel'] == 'Percent At First':
                if num == numP:
                    out.append(w)
                else:
                    out.append('%s(%%%d)'%(w, 100*num))
            else:
                out.append(w)
        return out


    def reverseDic(self, wordsArg=None, opt=None):
        if opt is None:
            opt = {}
        opt = addDefaultOptions(opt, {
            'matchWord': True,
            'showRel': 'None',
            'includeDefs': False,
            'background': False,
            'reportStep': 300,
            'autoSaveStep': 1000, ## set this to zero to disable auto saving.
            'savePath': '',
        })
        self.stoped = False
        ui = self.ui
        try:
            c = self.continueFrom
        except AttributeError:
            c = 0
        savePath = opt['savePath']
        if c == -1:
            log.debug('c=%s'%c)
            return
        elif c==0:
            saveFile = open(savePath, 'wb')
            ui.progressStart()
            ui.progress(0.0, 'Starting...')
        elif c>0:
            saveFile = open(savePath, 'ab')
        if wordsArg is None:
            words = self.takeOutputWords()
        elif isinstance(wordsArg, file):
            words = wordsArg.read().split('\n')
        elif isinstance(wordsArg, (list, tuple)):
            words = wordsArg[:]
        elif isinstance(wordsArg, str):
            with open(wordsArg) as fp:
                words = fp.read().split('\n')
        else:
            raise TypeError('Argumant wordsArg to function reverseDic is not valid!')
        autoSaveStep = opt['autoSaveStep']
        if not opt['savePath']:
            opt['savePath'] = self.getInfo('name')+'.txt'
        revG = Glossary(
            info = self.info[:],
        )
        revG.setInfo('name', self.getInfo('name')+'_reversed')
        revG.setInfo('inputlang', self.getInfo('outputlang'))
        revG.setInfo('outputlang', self.getInfo('inputlang'))
        wNum = len(words)
        #steps = opt['reportStep']
        #div = 0
        #mod = 0
        #total = int(wNum/steps)
        """
        if c==0:
            log.info('Number of input words:', wNum)
            log.info('Reversing glossary...')
        else:
            log.info('continue reversing from index %d ...'%c)
        """
        t0 = time.time()
        if not ui:
            log.info('passed ratio\ttime:\tpassed\tremain\ttotal\tprocess')
        n = len(words)
        for i in range(c, n):
            word = words[i]
            rat = float(i+1)/n
            ui.progress(rat, '%d / %d words completed'%(i, n))
            if ui.reverseStop:
                saveFile.close() ## if with KeyboardInterrupt it will be closed ??????????????
                self.continueFrom = i
                self.stoped = True
                #thread.exit_thread()
                return
            else:
                self.i = i
            """
            if mod == steps:
                mod = 0 ; div += 1
                t = time.time()
                dt = t-t0
                tRem = (total-div)*dt/div ## (n-i)*dt/n
                rat = float(i)/n
                if ui:
                    ############# FIXME
                    #ui.progressbar.set_text(
                        '%d/%d words completed (%%%2f) remaining %d seconds'%(i,n,rat*100,tRem)
                    )
                    ui.progressbar.update(rat)
                    while gtk.events_pending():
                        gtk.main_iteration_do(False)
                else:
                    log.info('%4d / %4d\t%8s\t%8s\t%8s\t%s'%(
                        div,
                        total,
                        timeHMS(dt),
                        timeHMS(tRem),
                        timeHMS(dt + tRem),
                        sys.argv[0],
                    ))
            else:
                mod += 1
            """
            if autoSaveStep>0 and i%autoSaveStep==0 and i>0:
                saveFile.close()
                saveFile = open(savePath, 'ab')
            result = self.searchWordInDef(word, opt)
            if len(result)>0:
                try:
                    if opt['includeDefs']:
                        defi = '\\n\\n'.join(result)
                    else:
                        defi = ', '.join(result) + '.'
                except Exception:
                    open('result', 'wb').write(str(result))
                    log.exception('')
                    return False
                if autoSaveStep>0:
                    saveFile.write('%s\t%s\n'%(word, defi))
                else:
                    revG._data.append((word, defi))
            if autoSaveStep>0 and i==n-1:
                saveFile.close()
        if autoSaveStep==0:
            revG.writeTabfile(opt['savePath'])
        ui.r_finished()
        ui.progressEnd()
        return True


    def iterSqlLines(self, filename='', infoKeys=None, newline='\\n', transaction=False):
        newline = '<br>'
        infoDefLine = 'CREATE TABLE dbinfo ('
        infoValues = []
        #######################
        if not infoKeys:
            infoKeys = [
                'dbname',
                'author',
                'version',
                'direction',
                'origLang',
                'destLang',
                'license',
                'category',
                'description',
            ]
        ######################
        for key in infoKeys:
            value = self.getInfo(key)
            value = value.replace('\'', '\'\'')\
                               .replace('\x00', '')\
                               .replace('\r', '')\
                               .replace('\n', newline)
            infoValues.append('\'' + value + '\'')
            infoDefLine += '%s char(%d), '%(key, len(value))
        ######################
        infoDefLine = infoDefLine[:-2] + ');'
        yield infoDefLine
        yield 'CREATE TABLE word (\'id\' INTEGER PRIMARY KEY NOT NULL, \'w\' TEXT, \'m\' TEXT);'
        if transaction:
            yield 'BEGIN TRANSACTION;';
        yield 'INSERT INTO dbinfo VALUES(%s);'%(','.join(infoValues))
        for i, entry in enumerate(self):
            word = entry.getWord()
            defi = entry.getDefi()
            word = word.replace('\'', '\'\'').replace('\r', '').replace('\n', newline)
            defi = defi.replace('\'', '\'\'').replace('\r', '').replace('\n', newline)
            yield 'INSERT INTO word VALUES(%d, \'%s\', \'%s\');'%(i+1, word, defi)
        if transaction:
            yield 'END TRANSACTION;'
        yield 'CREATE INDEX ix_word_w ON word(w COLLATE NOCASE);'


    def uiEdit(self):## remove? FIXME
        p = self.ui.pref
        if p['sort']:
            self.sortWords()

    def getPref(self, name, default):
        if self.ui:
            return self.ui.pref.get(name, default)
        else:
            return default



Glossary.loadPlugins(join(dirname(__file__), 'plugins'))
