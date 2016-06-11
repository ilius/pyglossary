# -*- coding: utf-8 -*-
# glossary.py
#
# Copyright © 2008-2016 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
# This file is part of PyGlossary project, https://github.com/ilius/pyglossary
#
# This program is a free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. Or on Debian systems, from /usr/share/common-licenses/GPL
# If not, see <http://www.gnu.org/licenses/gpl.txt>.

from . import VERSION

import logging

import sys

import os
from os.path import (
    split,
    join,
    splitext,
    isdir,
    dirname,
    basename,
    abspath,
)

from time import time as now
import subprocess
import re

import pkgutil
from collections import Counter
from collections import OrderedDict as odict

import io

from .flags import *
from . import core
from .core import userPluginsDir
from .entry import Entry
from .entry_filters import *
from .sort_stream import hsortStreamList

from .text_utils import (
    fixUtf8,
)
from .os_utils import indir


homePage = 'https://github.com/ilius/pyglossary'
log = logging.getLogger('root')

file = io.BufferedReader


def get_ext(path):
    return splitext(path)[1].lower()


class Glossary(object):
    """
    Direct access to glos.data is droped
    Use `glos.addEntry(word, defi, [defiFormat])`
        where both word and defi can be list (including alternates) or string
    See help(glos.addEntry)

    Use `for entry in glos:` to iterate over entries (glossary data)
    See help(pyglossary.entry.Entry) for details

    """

    # Should be changed according to plugins? FIXME
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
    plugins = {}  # format => pluginModule
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
        """
        executed on startup.  as name implies, loads plugins from directory
        """
        log.debug('loading plugins from directory: %r' % directory)
        if not isdir(directory):
            log.error('invalid plugin directory: %r' % directory)
            return

        sys.path.append(directory)
        for _, pluginName, _ in pkgutil.iter_modules([directory]):
            cls.loadPlugin(pluginName)
        sys.path.pop()

    @classmethod
    def loadPlugin(cls, pluginName):
        try:
            plugin = __import__(pluginName)
        except Exception as e:
            log.exception('error while importing plugin %s' % pluginName)
            return

        if (not hasattr(plugin, 'enable')) or (not plugin.enable):
            log.debug('plugin disabled or not a plugin: %s' % pluginName)
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

        cls.plugins[format] = plugin
        cls.descFormat[desc] = format
        cls.descExt[desc] = extentions[0]
        for ext in extentions:
            cls.extFormat[ext] = format
        cls.formatsExt[format] = extentions
        cls.formatsDesc[format] = desc

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
                    log.error(
                        'invalid Reader class in "%s" plugin' % format +
                        ', no "%s" method' % attr
                    )
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

        if hasattr(plugin, 'write'):
            cls.writeFunctions[format] = plugin.write
            cls.writeFormats.append(format)
            cls.writeExt.append(extentions)
            cls.writeDesc.append(desc)
            cls.formatsWriteOptions[format] = getattr(
                plugin,
                'writeOptions',
                []
            )

        return plugin

    def clear(self):
        self._info = odict()

        self._data = []

        try:
            readers = self._readers
        except AttributeError:
            pass
        else:
            for reader in readers:
                try:
                    reader.close()
                except Exception:
                    log.exception('')
        self._readers = []

        self._iter = None
        self._entryFilters = []
        self._sortKey = None
        self._sortCacheSize = 1000

        self._filename = ''
        self.resPath = ''
        self._defaultDefiFormat = 'm'
        self._progressbar = True

    def __init__(self, info=None, ui=None):
        """
        info: OrderedDict instance, or None
              no need to copy OrderedDict instance,
              we will not reference to it
        """
        self.clear()
        if info:
            if not isinstance(info, (dict, odict)):
                raise TypeError(
                    'Glossary: `info` has invalid type'
                    ', dict or OrderedDict expected'
                )
            for key, value in info.items():
                self.setInfo(key, value)

        '''
        self._data is a list of tuples with length 2 or 3:
            (word, definition)
            (word, definition, defiFormat)
            where both word and definition can be a string, or list
                (containing word and alternates)

            defiFormat: format of the definition:
                'm': plain text
                'h': html
                'x': xdxf
        '''
        self.ui = ui

    def updateEntryFilters(self):
        self._entryFilters = []
        pref = getattr(self.ui, 'pref', {})

        self._entryFilters.append(StripEntryFilter(self))
        self._entryFilters.append(NonEmptyWordFilter(self))

        if pref.get('utf8Check', True):
            self._entryFilters.append(FixUnicodeFilter(self))

        if pref.get('lower', True):
            self._entryFilters.append(LowerWordFilter(self))

        self._entryFilters.append(LangEntryFilter(self))
        self._entryFilters.append(CleanEntryFilter(self))
        self._entryFilters.append(NonEmptyWordFilter(self))
        self._entryFilters.append(NonEmptyDefiFilter(self))

    def __str__(self):
        return 'glossary.Glossary'

    def addEntryObj(self, entry):
        self._data.append(entry.getRaw())

    def addEntry(self, word, defi, defiFormat=None):
        if defiFormat == self._defaultDefiFormat:
            defiFormat = None

        self.addEntryObj(Entry(word, defi, defiFormat))

    def _loadedEntryGen(self):
        wordCount = len(self._data)
        progressbar = self.ui and self._progressbar
        if progressbar:
            self.progressInit('Writing')
        for index, rawEntry in enumerate(self._data):
            yield Entry.fromRaw(
                rawEntry,
                defaultDefiFormat=self._defaultDefiFormat
            )
            if progressbar:
                self.progress(index, wordCount)
        if progressbar:
            self.progressEnd()

    def _readersEntryGen(self):
        for reader in self._readers:
            wordCount = 0
            progressbar = False
            if self.ui and self._progressbar:
                try:
                    wordCount = len(reader)
                except Exception:
                    log.exception('')
                if wordCount:
                    progressbar = True
            if progressbar:
                self.progressInit('Converting')
            try:
                for index, entry in enumerate(reader):
                    yield entry
                    if progressbar:
                        self.progress(index, wordCount)
            finally:
                reader.close()
            if progressbar:
                self.progressEnd()

    def _applyEntryFiltersGen(self, gen):
        for entry in gen:
            if not entry:
                continue
            for entryFilter in self._entryFilters:
                entry = entryFilter.run(entry)
                if not entry:
                    break
            else:
                yield entry

    def __iter__(self):
        if self._iter is None:
            log.error(
                'Trying to iterate over a blank Glossary'
                ', must call `glos.read` first'
            )
            return iter([])
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

    def __len__(self):
        return len(self._data) + sum(
            len(reader) for reader in self._readers
        )

    def infoKeys(self):
        return list(self._info.keys())

    def getMostUsedDefiFormats(self, count=None):
        return Counter([
            entry.getDefiFormat()
            for entry in self
        ]).most_common(count)

    # def formatInfoKeys(self, format):# FIXME

    def iterInfo(self):
        return self._info.items()

    def getInfo(self, key):
        key = str(key)

        try:
            key = self.infoKeysAliasDict[key.lower()]
        except KeyError:
            pass

        return self._info.get(key, '')  # '' or None as default? FIXME

    def setInfo(self, key, value):
        #  FIXME
        origKey = key
        key = fixUtf8(key)
        value = fixUtf8(value)

        try:
            key = self.infoKeysAliasDict[key.lower()]
        except KeyError:
            pass

        if origKey != key:
            log.debug('setInfo: %s -> %s' % (origKey, key))

        self._info[key] = value

    def getExtraInfos(self, excludeKeys):
        """
        excludeKeys: a list of (basic) info keys to be excluded
        returns an OrderedDict including the rest of info keys,
                with associated values
        """
        excludeKeySet = set()
        for key in excludeKeys:
            excludeKeySet.add(key)
            try:
                excludeKeySet.add(self.infoKeysAliasDict[key.lower()])
            except KeyError:
                pass

        extra = odict()
        for key, value in self._info.items():
            if key in excludeKeySet:
                continue
            extra[key] = value

        return extra

    def getPref(self, name, default):
        if self.ui:
            return self.ui.pref.get(name, default)
        else:
            return default

    # ________________________________________________________________________#

    def read(
        self,
        filename,
        format='',
        direct=False,
        progressbar=True,
        **options
    ):
        """
        filename (str): name/path of input file
        format (str): name of inout format,
                      or '' to detect from file extention
        direct (bool): enable direct mode
        """
        filename = abspath(filename)

        # don't allow direct=False when there are readers
        # (read is called before with direct=True)
        if self._readers and not direct:
            raise ValueError(
                'there are already %s readers' % len(self._readers) +
                ', you can not read with direct=False mode'
            )

        self.updateEntryFilters()
        ###
        delFile = False
        ext = get_ext(filename)
        if ext in ('.gz', '.bz2', '.zip'):
            if ext == '.bz2':
                output, error = subprocess.Popen(
                    ['bzip2', '-dk', filename],
                    stdout=subprocess.PIPE,
                ).communicate()
                # -k ==> keep original bz2 file
                # bunzip2 ~= bzip2 -d
                if error:
                    log.error(
                        error + '\n' +
                        'failed to decompress file "%s"' % filename
                    )
                    return False
                else:
                    filename = filename[:-4]
                    ext = get_ext(filename)
                    delFile = True
            elif ext == '.gz':
                output, error = subprocess.Popen(
                    ['gzip', '-dc', filename],
                    stdout=subprocess.PIPE,
                ).communicate()
                # -c ==> write to stdout (we want to keep original gz file)
                # gunzip ~= gzip -d
                if error:
                    log.error(
                        error + '\n' +
                        'failed to decompress file "%s"' % filename
                    )
                    return False
                else:
                    filename = filename[:-3]
                    open(filename, 'w').write(output)
                    ext = get_ext(filename)
                    delFile = True
            elif ext == '.zip':
                output, error = subprocess.Popen(
                    ['unzip', filename, '-d', dirname(filename)],
                    stdout=subprocess.PIPE,
                ).communicate()
                if error:
                    log.error(
                        error + '\n' +
                        'failed to decompress file "%s"' % filename
                    )
                    return False
                else:
                    filename = filename[:-4]
                    ext = get_ext(filename)
                    delFile = True
        if not format:
            for key in Glossary.formatsExt.keys():
                if ext in Glossary.formatsExt[key]:
                    format = key
            if not format:
                # if delFile:
                #    os.remove(filename)
                log.error('Unknown extension "%s" for read support!' % ext)
                return False
        validOptionKeys = self.formatsReadOptions[format]
        for key in list(options.keys()):
            if key not in validOptionKeys:
                log.error(
                    'Invalid read option "%s" ' % key +
                    'given for %s format' % format
                )
                del options[key]

        filenameNoExt, ext = splitext(filename)
        if not ext.lower() in self.formatsExt[format]:
            filenameNoExt = filename

        self._filename = filenameNoExt
        if not self.getInfo('name'):
            self.setInfo('name', split(filename)[1])
        self._progressbar = progressbar

        try:
            Reader = self.readerClasses[format]
        except KeyError:
            if direct:
                log.warning(
                    'no `Reader` class found in %s plugin' % format +
                    ', falling back to indirect mode'
                )
            result = self.readFunctions[format].__call__(
                self,
                filename,
                **options
            )
            # if not result:## FIXME
            #    return False
            if delFile:
                os.remove(filename)
        else:
            reader = Reader(self)
            reader.open(filename, **options)
            if direct:
                self._readers.append(reader)
                log.info(
                    'using Reader class from %s plugin' % format +
                    ' for direct conversion without loading into memory'
                )
            else:
                self.loadReader(reader)

        self._updateIter()

        return True

    def loadReader(self, reader):
        """
        iterates over `reader` object and loads the whole data into self._data
        must call `reader.open(filename)` before calling this function
        """
        wordCount = 0
        progressbar = False
        if self.ui and self._progressbar:
            try:
                wordCount = len(reader)
            except Exception:
                log.exception('')
            if wordCount:
                progressbar = True
        if progressbar:
            self.progressInit('Reading')
        try:
            for index, entry in enumerate(reader):
                if entry:
                    self.addEntryObj(entry)
                if progressbar:
                    self.progress(index, wordCount)
        finally:
            reader.close()
        if progressbar:
            self.progressEnd()

        return True

    def _inactivateDirectMode(self):
        """
        loads all of `self._readers` into `self._data`
        closes readers
        and sets self._readers to []
        """
        for reader in self._readers:
            self.loadReader(reader)
        self._readers = []

    def _updateIter(self, sort=False):
        """
        updates self._iter
        depending on:
            1- Wheather or not direct mode is On (self._readers not empty)
                or Off (self._readers empty)
            2- Wheather sort is True, and if it is,
                checks for self._sortKey and self._sortCacheSize
        """
        if self._readers:  # direct mode
            if sort:
                sortKey = self._sortKey
                cacheSize = self._sortCacheSize
                log.info('stream sorting enabled, cache size: %s' % cacheSize)
                # only sort by main word, or list of words + alternates? FIXME
                gen = hsortStreamList(
                    self._readers,
                    cacheSize,
                    key=Entry.getEntrySortKey(sortKey),
                )
            else:
                gen = self._readersEntryGen()
        else:
            gen = self._loadedEntryGen()

        self._iter = self._applyEntryFiltersGen(gen)

    def sortWords(self, key=None, cacheSize=None):
        # only sort by main word, or list of words + alternates? FIXME
        if self._readers:
            self._sortKey = key
            if cacheSize:
                self._sortCacheSize = cacheSize  # FIXME
        else:
            self._data.sort(
                key=Entry.getRawEntrySortKey(key),
            )
        self._updateIter(sort=True)

    def write(
        self,
        filename='',
        format='',
        sort=None,
        sortKey=None,
        sortCacheSize=1000,
        **options
    ):
        """
        sort (bool):
            True (enable sorting),
            False (disable sorting),
            None (auto, get from UI)
        sortKey (callable or None):
            key function for sorting
            takes a word as argument, which is str or list (with alternates)
        """
        if not filename:
            filename = self._filename
        if not filename:
            log.error('Invalid filename %r' % filename)
            return False
        ext = ''
        filenameNoExt, fext = splitext(filename)
        fext = fext.lower()
        if fext in ('.gz', '.bz2', '.zip'):
            archiveType = fext[1:]
            filename = filenameNoExt
            fext = get_ext(filename)
        else:
            archiveType = ''
        del filenameNoExt
        if format:
            try:
                ext = Glossary.formatsExt[format][0]
            except KeyError:
                log.exception(
                    'no file extention found for file format %s' % format
                )
                format = ''  # FIXME
        if not format:
            items = Glossary.formatsExt.items()
            for (fmt, extList) in items:
                for e in extList:
                    if format == e[1:] or format == e:
                        format = fmt
                        ext = e
                        break
                if format:
                    break
            if not format:
                for (fmt, extList) in items:
                    if filename == fmt:
                        format = filename
                        ext = extList[0]
                        filename = self._filename + ext
                        break
                    for e in extList:
                        if filename == e[1:] or filename == e:
                            format = fmt
                            ext = e
                            filename = self._filename + ext
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
            filename = join(filename, basename(self._filename)+ext)
        validOptionKeys = self.formatsWriteOptions[format]
        for key in list(options.keys()):
            if key not in validOptionKeys:
                log.error(
                    'Invalid write option "%s"' % key +
                    ' given for %s format' % format
                )
                del options[key]

        plugin = self.plugins[format]
        sortOnWrite = plugin.sortOnWrite
        if sortOnWrite == ALWAYS:
            if sort is False:
                log.warning(
                    'writing %s requires sorting' % format +
                    ', ignoring user sort=False option'
                )
            if self._readers:
                log.warning(
                    'writing to %s format requires full sort' % format +
                    ', falling back to indirect mode'
                )
                self._inactivateDirectMode()
                log.info('loaded %s entries' % len(self._data))
            sort = True
        elif sortOnWrite == DEFAULT_YES:
            if sort is None:
                sort = True
        elif sortOnWrite == DEFAULT_NO:
            if sort is None:
                sort = False
        elif sortOnWrite == NEVER:
            if sort:
                log.warning(
                    'plugin prevents sorting before write' +
                    ', ignoring user sort=True option'
                )
            sort = False

        if sort:
            if sortKey is None:
                try:
                    sortKey = plugin.sortKey
                except AttributeError:
                    pass
                else:
                    log.debug(
                        'using sort key function from %s plugin' % format
                    )
            elif sortOnWrite == ALWAYS:
                try:
                    sortKey = plugin.sortKey
                except AttributeError:
                    pass
                else:
                    log.warning(
                        'ignoring user-defined sort order, ' +
                        'and using key function from %s plugin' % format
                    )
            self.sortWords(
                key=sortKey,
                cacheSize=sortCacheSize
            )
        else:
            self._updateIter(sort=False)

        filename = abspath(filename)
        log.info('Writing to file "%s"' % filename)
        try:
            self.writeFunctions[format].__call__(self, filename, **options)
        except Exception:
            log.exception('exception while calling plugin\'s write function')
            return False
        finally:
            self.clear()

        if archiveType:
            self.archiveOutDir(filename, archiveType)

        return True

    def archiveOutDir(self, filename, archiveType):
        """
        filename is the existing file path
        archiveType is the archive extention (without dot): 'gz', 'bz2', 'zip'
        """
        try:
            os.remove('%s.%s' % (filename, archiveType))
        except OSError:
            pass
        if archiveType == 'gz':
            output, error = subprocess.Popen(
                ['gzip', filename],
                stdout=subprocess.PIPE,
            ).communicate()
            if error:
                log.error('%s\nfail to compress file "%s"' % (error, filename))
        elif archiveType == 'bz2':
            output, error = subprocess.Popen(
                ['bzip2', filename],
                stdout=subprocess.PIPE,
            ).communicate()
            if error:
                log.error('%s\nfail to compress file "%s"' % (error, filename))
        elif archiveType == 'zip':
            dirn, name = split(filename)
            with indir(dirn):
                output, error = subprocess.Popen(
                    ['zip', filename+'.zip', name, '-m'],
                    stdout=subprocess.PIPE,
                ).communicate()
                if error:
                    log.error(
                        error + '\n' +
                        'failed to compress file "%s"' % filename
                    )

    def convert(
        self,
        inputFilename,
        inputFormat='',
        direct=None,
        progressbar=True,
        outputFilename='',
        outputFormat='',
        sort=None,
        sortKey=None,
        sortCacheSize=1000,
        readOptions=None,
        writeOptions=None,
    ):
        if not readOptions:
            readOptions = {}
        if not writeOptions:
            writeOptions = {}

        if direct is None:
            if sort is not True:
                direct = True  # FIXME

        tm0 = now()
        if not self.read(
            inputFilename,
            format=inputFormat,
            direct=direct,
            progressbar=progressbar,
            **readOptions
        ):
            return False
        log.info('')

        if not self.write(
            filename=outputFilename,
            format=outputFormat,
            sort=sort,
            sortKey=sortKey,
            sortCacheSize=sortCacheSize,
            **writeOptions
        ):
            return False
        log.info('')
        log.info('Running time of convert: %.1f seconds' % (now() - tm0))

        return True

    # ________________________________________________________________________#

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
            filename = self._filename + ext
        if not outInfoKeysAliasDict:
            outInfoKeysAliasDict = {}

        fp = open(filename, 'w', encoding=encoding)
        fp.write(head)
        if writeInfo:
            for key, desc in self._info.items():
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
            if word.startswith('#'):  # FIXME
                continue
            # if self.getPref('enable_alts', True):  # FIXME

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
        # Used in '/usr/share/dict/' for some dictionarys such as 'ding'
        self.writeTxt(
            (' :: ', '\n'),
            filename,
            writeInfo,
            (
                ('\n', '\\n'),
            ),
            '.dict',
        )

    def iterSqlLines(
        self,
        filename='',
        infoKeys=None,
        addExtraInfo=True,
        newline='\\n',
        transaction=False,
    ):
        newline = '<br>'
        infoDefLine = 'CREATE TABLE dbinfo ('
        infoValues = []

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

        for key in infoKeys:
            value = self.getInfo(key)
            value = value.replace('\'', '\'\'')\
                         .replace('\x00', '')\
                         .replace('\r', '')\
                         .replace('\n', newline)
            infoValues.append('\'' + value + '\'')
            infoDefLine += '%s char(%d), ' % (key, len(value))

        infoDefLine = infoDefLine[:-2] + ');'
        yield infoDefLine

        if addExtraInfo:
            yield 'CREATE TABLE dbinfo_extra ('
            '\'id\' INTEGER PRIMARY KEY NOT NULL, '
            '\'name\' TEXT UNIQUE, \'value\' TEXT);'

        yield 'CREATE TABLE word (\'id\' INTEGER PRIMARY KEY NOT NULL, '
        '\'w\' TEXT, \'m\' TEXT);'

        if transaction:
            yield 'BEGIN TRANSACTION;'
        yield 'INSERT INTO dbinfo VALUES(%s);' % (','.join(infoValues))

        if addExtraInfo:
            extraInfo = self.getExtraInfos(infoKeys)
            for index, (key, value) in enumerate(extraInfo.items()):
                yield 'INSERT INTO dbinfo_extra ' + \
                    'VALUES(%d, \'%s\', \'%s\');' % (
                        index + 1,
                        key.replace('\'', '\'\''),
                        value.replace('\'', '\'\''),
                    )

        for i, entry in enumerate(self):
            word = entry.getWord()
            defi = entry.getDefi()
            word = word.replace('\'', '\'\'')\
                .replace('\r', '').replace('\n', newline)
            defi = defi.replace('\'', '\'\'')\
                .replace('\r', '').replace('\n', newline)
            yield 'INSERT INTO word VALUES(%d, \'%s\', \'%s\');' % (
                i+1,
                word,
                defi,
            )
        if transaction:
            yield 'END TRANSACTION;'
        yield 'CREATE INDEX ix_word_w ON word(w COLLATE NOCASE);'

    # ________________________________________________________________________#

    def takeOutputWords(self, minWordLen=3):
        wordPattern = re.compile('[\w]{%d,}' % minWordLen, re.U)
        words = set()
        for entry in self:
            words.update(re.findall(
                wordPattern,
                entry.getDefi(),
            ))
        return sorted(words)

    # ________________________________________________________________________#

    def progressInit(self, *args):
        if self.ui:
            self.ui.progressInit(*args)

    def progress(self, wordI, wordCount):
        if self.ui and wordI % (wordCount//500) == 0:
            self.ui.progress(
                (wordI + 1) / wordCount,
                '%d / %d completed' % (wordI, wordCount),
            )

    def progressEnd(self):
        if self.ui:
            self.ui.progressEnd()

    # ________________________________________________________________________#

    def searchWordInDef(
        self,
        st,
        matchWord=True,
        sepChars='.,،',
        maxNum=100,
        minRel=0.0,
        minWordLen=3,
        includeDefs=False,
        showRel='Percent',
    ):
        # searches word 'st' in definitions of the glossary
        splitPattern = re.compile(
            '|'.join([re.escape(x) for x in sepChars]),
            re.U,
        )
        wordPattern = re.compile('[\w]{%d,}' % minWordLen, re.U)
        outRel = []
        for item in self._data:
            word, defi = item[:2]
            if st not in defi:
                continue
            rel = 0  # relation value of word (0 <= rel <= 1)
            for part in re.split(splitPattern, defi):
                if not part:
                    continue
                if matchWord:
                    partWords = re.findall(
                        wordPattern,
                        part,
                    )
                    if not partWords:
                        continue
                    rel = max(
                        rel,
                        partWords.count(st) / len(partWords)
                    )
                else:
                    rel = max(
                        rel,
                        part.count(st) * len(st) / len(part)
                    )
            if rel <= minRel:
                continue
            if includeDefs:
                outRel.append((word, rel, defi))
            else:
                outRel.append((word, rel))
        outRel.sort(
            key=lambda x: x[1],
            reverse=True,
        )
        n = len(outRel)
        if n > maxNum > 0:
            outRel = outRel[:maxNum]
            n = maxNum
        num = 0
        out = []
        if includeDefs:
            for j in range(n):
                numP = num
                w, num, m = outRel[j]
                m = m.replace('\n', '\\n').replace('\t', '\\t')
                onePer = int(1.0/num)
                if onePer == 1.0:
                    out.append('%s\\n%s' % (w, m))
                elif showRel == 'Percent':
                    out.append('%s(%%%d)\\n%s' % (w, 100*num, m))
                elif showRel == 'Percent At First':
                    if num == numP:
                        out.append('%s\\n%s' % (w, m))
                    else:
                        out.append('%s(%%%d)\\n%s' % (w, 100*num, m))
                else:
                    out.append('%s\\n%s' % (w, m))
            return out
        for j in range(n):
            numP = num
            w, num = outRel[j]
            onePer = int(1.0/num)
            if onePer == 1.0:
                out.append(w)
            elif showRel == 'Percent':
                out.append('%s(%%%d)' % (w, 100*num))
            elif showRel == 'Percent At First':
                if num == numP:
                    out.append(w)
                else:
                    out.append('%s(%%%d)' % (w, 100*num))
            else:
                out.append(w)
        return out

    def reverse(
        self,
        savePath='',
        words=None,
        includeDefs=False,
        reportStep=300,
        saveStep=1000,  # set this to zero to disable auto saving
        **kwargs
    ):
        """
        This is a generator
        Usage:
            for wordIndex in glos.reverse(...):
                pass

        Inside the `for` loop, you can pause by waiting (for input or a flag)
            or stop by breaking

        Potential keyword arguments:
            words = None ## None, or list
            reportStep = 300
            saveStep = 1000
            savePath = ''
            matchWord = True
            sepChars = '.,،'
            maxNum = 100
            minRel = 0.0
            minWordLen = 3
            includeDefs = False
            showRel = 'None'
                allowed values: 'None', 'Percent', 'Percent At First'
        """
        if not savePath:
            savePath = self.getInfo('name') + '.txt'

        if saveStep < 2:
            raise ValueError('saveStep must be more than 1')

        ui = self.ui

        if words:
            words = list(words)
        else:
            words = self.takeOutputWords()

        wordCount = len(words)
        log.info(
            'Reversing to file "%s"' % savePath +
            ', number of words: %s' % wordCount
        )
        with open(savePath, 'w') as saveFile:
            for wordI in range(wordCount):
                word = words[wordI]
                self.progress(wordI, wordCount)

                if wordI % saveStep == 0 and wordI > 0:
                    saveFile.flush()
                result = self.searchWordInDef(
                    word,
                    includeDefs=includeDefs,
                    **kwargs
                )
                if result:
                    try:
                        if includeDefs:
                            defi = '\\n\\n'.join(result)
                        else:
                            defi = ', '.join(result) + '.'
                    except Exception:
                        log.exception('')
                        log.pretty(result, 'result = ')
                        return False
                    saveFile.write('%s\t%s\n' % (word, defi))
                yield wordI

        self.finished()
        yield wordCount


Glossary.loadPlugins(join(dirname(__file__), 'plugins'))
Glossary.loadPlugins(userPluginsDir)
