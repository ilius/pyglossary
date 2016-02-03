# -*- coding: utf-8 -*-
## glossary.py
##
## Copyright © 2008-2010 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
## This file is part of PyGlossary project, http://sourceforge.net/projects/pyglossary/
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

import core
from text_utils import faEditStr, replacePostSpaceChar, removeTextTags,\
                       takeStrWords, findWords, findAll, addDefaultOptions

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




class Glossary:
    infoKeysAlias = (## Should be changed according to a plugin???
        ('name', 'title', 'dbname', 'bookname'),
        ('sourceLang', 'inputlang', 'origlang'),
        ('targetLang', 'outputlang', 'destlang'),
        ('copyright', 'license'),
    )
    readFormats = []
    writeFormats = []
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
    """
    a list if tuples: ('key', 'definition') or ('key', 'definition', dict() )
    in general we should assume the tuple may be of arbitrary length >= 2
    known dictionary keys:
        data[i][2]['alts'] - list of alternates, filled by bgl reader
        data[i][2]['defis'] - list of alternative definitions.
            For example, run (eng.) may be 1. verb, 2. noun, 3. adjective.
            self.data[i][1] contains the main definition of the word, the verb, in the example.
            While additional definitions goes to self.data[i][2]['defis'] list, noun and adjective,
            in the example.
            You may merge additional definition with the main definition if the target dictionary
            format does not support several definitions per word.
        data[i][2]['defis'][j][0] - definition data
        data[i][2]['defis'][j][1] - definition format. See 'defiFormat' option below.
        data[i][2]['defiFormat'] - format of the definition: 'h' - html, 'm' - plain text, 'x' - xdxf,
                                    use xdxf.xdxf_to_html to convert
    """
    data = []

    @classmethod
    def load_plugins(cls, directory):
        """executed on startup.  as name implies, loads plugins from directory."""
        log.debug("loading plugins from directory: %r" % directory)
        if not isdir(directory):
            log.error('invalid plugin directory: %r' % directory)
            return

        sys.path.append(directory)
        for _, plugin, _ in pkgutil.iter_modules([directory]):
            cls.load_plugin(plugin)

    @classmethod
    def load_plugin(cls, plugin_name):
        log.debug('loading plugin %s' % plugin_name)
        try:
            plugin = __import__(plugin_name)
        except (ImportError, SyntaxError) as e:
            log.error("error while importing plugin %s" % plugin_name, exc_info=1)
            return

        if (not hasattr(plugin, 'enable')) or (not plugin.enable):
            log.debug("plugin disabled or not a plugin: %s.  skipping..." % plugin_name)
            return

        format = plugin.format

        extentions = plugin.extentions
        # FIXME: deprecate non-tuple values in plugin.extentions
        if isinstance(extentions, basestring):
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

        if hasattr(plugin, 'read'):
            exec('cls.read%s = plugin.read' % format)  # FIXME: OMG WTF
            cls.readFormats.append(format)
            cls.readExt.append(extentions)
            cls.readDesc.append(desc)
            cls.formatsReadOptions[format] = plugin.readOptions \
                if hasattr(plugin, 'readOptions') else []

        if hasattr(plugin, 'write'):
            exec('cls.write%s = plugin.write' % format)
            cls.writeFormats.append(format)
            cls.writeExt.append(extentions)
            cls.writeDesc.append(desc)
            cls.formatsWriteOptions[format] = plugin.writeOptions \
                if hasattr(plugin, 'writeOptions') else []

        log.debug("plugin loaded OK: %s" % plugin_name)
        return plugin


    def __init__(self, info=None, data=None, ui=None, filename='', resPath=''):
        if info is None:
            info = []
        if data is None:
            data = []
        self.info = []
        self.setInfos(info, True)
        self.data = data
        self.ui = ui
        self.filename = filename
        self.resPath = resPath

    __str__ = lambda self: 'glossary.Glossary'

    def copy(self):
        return Glossary(
            info = self.info[:],
            data = self.data[:],
            ui = self.ui, ## FIXME
            filename = self.filename,
            resPath = self.resPath,
        )

    def infoKeys(self):
        return [t[0] for t in self.info]

    #def formatInfoKeys(self, format):## FIXME

    def getInfo(self, key):
        lkey = str(key).lower()
        for group in Glossary.infoKeysAlias:
            if not isinstance(group, (list, tuple)):
                raise TypeError('group=%s'%group)
            if key in group or lkey in group:
                for skey in group:
                    for t in self.info:
                        if t[0] == skey:
                            return t[1]
        for t in self.info:
            if t[0].lower() == lkey:
                return t[1]
        return ''

    def setInfo(self, key, value):
        lkey = str(key).lower()
        for group in Glossary.infoKeysAlias:
            if not isinstance(group, (list, tuple)):
                raise TypeError('group=%s'%group)
            if key in group or lkey in group:
                skey=group[0]
                for i in xrange(len(self.info)):
                    if self.info[i][0]==skey:
                        self.info[i] = (self.info[i][0], value)
                        return
                for i in xrange(len(self.info)):
                    if self.info[i][0] in group:
                        self.info[i] = (self.info[i][0], value)
                        return
        for i in xrange(len(self.info)):
            if self.info[i][0]==key or self.info[i][0].lower()==lkey:
                    self.info[i] = (self.info[i][0], value)
                    return
        self.info.append([key, value])

    def setInfos(self, info, setAll=False):
        for t in info:
            self.setInfo(t[0], t[1])
        if setAll:
            for key in self.infoKeys():
                if not self.getInfo(key):
                    self.setInfo(key, '')

    def removeTags(self, tags):
        n = len(self.data)
        for i in xrange(n):
            self.data[i] = (
                self.data[i][0],
                removeTextTags(self.data[i][1], tags),
            ) + self.data[i][2:]

    def lowercase(self):
        for i in xrange(len(self.data)):
            self.data[i] = (self.data[i][0].lower(), self.data[i][1]) + self.data[i][2:]

    def capitalize(self):
        for i in xrange(len(self.data)):
            self.data[i] = (self.data[i][0].capitalize(), self.data[i][1]) + self.data[i][2:]

    def read(self, filename, format='', **options):
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
        getattr(self, 'read%s'%format).__call__(filename, **options)

        (filename_nox, ext) = splitext(filename)
        if ext.lower() in self.formatsExt[format]:
            filename = filename_nox
        self.filename = filename
        if self.getInfo('name') == '':
            self.setInfo('name', split(filename)[1])

        if delFile:
            os.remove(filename)
        return True


    def write(self, filename, format='', **options):
        if not filename:
            log.error('Invalid filename %r'%filename)
            return False
        ext = ''
        (filename_nox, fext) = splitext(filename)
        fext = fext.lower()
        if fext in ('.gz', '.bz2', '.zip'):
            zipExt = fext
            filename = filename_nox
            fext = splitext(filename)[1].lower()
        else:
            zipExt = ''
        del filename_nox
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
        getattr(self, 'write%s'%format).__call__(filename, **options)
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

    def writeTxt(self, sep, filename='', writeInfo=True, rplList=None, ext='.txt', head=''):
        if rplList is None:
            rplList = []
        if not filename:
            filename = self.filename + ext
        fp = open(filename, 'wb')
        fp.write(head)
        if writeInfo:
            for key, desc in self.info:
                for rpl in rplList:
                    desc = desc.replace(rpl[0], rpl[1])
                fp.write('##' + key + sep[0] + desc + sep[1])
        fp.flush()
        for item in self.data:
            (word, defi) = item[:2]
            if word.startswith('#'):## FIXME
                continue
            if self.getPref('enable_alts', True):
                try:
                    alts = item[2]['alts']
                except (IndexError, KeyError):
                    pass
                else:
                    if alts:
                        if not word in alts:
                            alts.insert(0, word)
                        word = '|'.join(alts)
            for rpl in rplList:
                defi = defi.replace(rpl[0], rpl[1])
            fp.write(word + sep[0] + defi + sep[1])
        fp.close()
        return True



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


    def printTabfile(self):
        for item in self.data:
            (word, defi) = item[:2]
            defi = defi.replace('\n', '\\n')
            try:
                print(word + '\t' + defi)
            except Exception:
                log.exception('')


    ###################################################################
    takeWords = lambda self: [item[0] for item in self.data]


    def takeOutputWords(self, opt=None):
        if opt is None:
            opt = {}
        words = sorted(takeStrWords(' '.join([item[1] for item in self.data]), opt))
        words = removeRepeats(words)
        return words

    getInputList = lambda self: [x[0] for x in self.data]

    getOutputList = lambda self: [x[1] for x in self.data]

    def simpleSwap(self):
        # loosing item[2:]
        return Glossary(
            info = self.info[:],
            data = [
                (item[1], item[0]) \
                for item in self.data
            ],
        )

    def attach(self, other):# only simplicity attach two glossaries (or more that others be as a list).
    # no ordering. Use when you split input words to two(or many) parts after ordering.
        try:
            other.data, other.info
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
            data = self.data + other.data,
        )
        ## here attach and set info of two glossary ## FIXME
        return newGloss

    def merge(self, other):
        try:
            other.data, other.info
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
            data = sorted(self.data + other.data),
        )
        return newGloss


    def deepMerge(self, other, sep='\n'):
        ## merge two optional glossarys nicly. no repets in words of result glossary
        try:
            other.data, other.info
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
            self.data + other.data,
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
            data = data,
        )


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
        for item in self.data:
            (word, defi) = item[:2]
            defiParts = defi.split(sep)
            if defi.find(st) == -1:
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
            for j in xrange(n):
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
        for j in xrange(n):
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
        elif isinstance(wordsArg, basestring):
            words = open(wordsArg).read().split('\n')
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
        '''
        if c==0:
            log.info('Number of input words:', wNum)
            log.info('Reversing glossary...')
        else:
            log.info('continue reversing from index %d ...'%c)
        '''
        t0 = time.time()
        if not ui:
            log.info('passed ratio\ttime:\tpassed\tremain\ttotal\tprocess')
        n = len(words)
        for i in xrange(c, n):
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
            '''
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
            '''
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
                    revG.data.append((word, defi))
            if autoSaveStep>0 and i==n-1:
                saveFile.close()
        if autoSaveStep==0:
            revG.writeTabfile(opt['savePath'])
        ui.r_finished()
        ui.progressEnd()
        return True

    def replaceInDefinitions(self, replaceList, matchWord=False):
        if not matchWord:
            for rpl in replaceList:
                for i in xrange(len(self.data)):
                    if self.data[i][1].find(rpl[0])>-1:
                        self.data[i][1] = self.data[i][1].replace(rpl[0], rpl[1])
        else:
            num = 0
            for rpl in replaceList:
                for j in xrange(len(self.data)):
                    # words indexes
                    wdsIdx = findWords(self.data[j][1], {'word': rpl[0]})
                    for [i0, i1] in wdsIdx:
                        self.data[j][1] = self.data[j][1][:i0] + rpl[1] + self.data[j][1][i1:]
                        num += 1
            return num

    def takePhonetic_oxford_gb(self):
        phg = Glossary(self.info[:]) ## phonetic glossary
        phg.setInfo('name', self.getInfo('name') + '_phonetic')
        for item in self.data:
            word = item[0]
            defi = item[1]
            if not defi.startswith('/'):
                continue
            #### Now set the phonetic to the `ph` variable.
            ph = ''
            for s in (
                '/ adj',
                '/ v',
                '/ n',
                '/ adv',
                '/adj',
                '/v',
                '/n',
                '/adv',
                '/ n',
                '/ the',
            ):
                i = defi.find(s, 2, 85)
                if i==-1:
                    continue
                else:
                    ph = defi[:i+1]
                    break
            ph = ph.replace(';', '\t')\
                   .replace(',', '\t')\
                   .replace('     ', '\t')\
                   .replace('    ', '\t')\
                   .replace('  ', '\t')\
                   .replace('//', '/')\
                   .replace('\t/\t', '\t')\
                   .replace('<i>US</i>\t', '\tUS: ')\
                   .replace('<i>US</i>', '\tUS: ')\
                   .replace('\t\t\t', '\t')\
                   .replace('\t\t', '\t')\
            #      .replace('/', '')
            #      .replace('\\n ', '\\n')
            #      .replace('\\n ', '\\n')
            if ph != '':
                phg.data.append((word, ph))
        return phg


    def getSqlLines(self, filename='', info=None, newline='\\n'):
        lines = []
        newline = '<br>'
        infoDefLine = 'CREATE TABLE dbinfo ('
        infoList = []
        #######################
        #keys=('name', 'author', 'version', 'direction', 'origLang', 'destLang', 'license', 'category', 'description')
        #for key in keys:
        #    inf = "'" + self.getInfo(key).replace('\'', '"').replace('\n',newline) + "'"
        #    infoList.append(inf)
        #    infoDefLine += '%s varchar(%d), '%(key, len(inf)+10)
        ######################
        if not info:
            info = self.info
        for item in info:
            inf = "'" + item[1].replace("'", '\'\'')\
                               .replace('\x00', '')\
                               .replace('\r', '')\
                               .replace('\n', newline) + "'"
            infoList.append(inf)
            infoDefLine += '%s char(%d), '%(item[0], len(inf))
        ######################
        infoDefLine = infoDefLine[:-2] + ');'
        lines.append(infoDefLine)
        lines.append("CREATE TABLE word ('id' INTEGER PRIMARY KEY NOT NULL, 'w' TEXT, 'm' TEXT);")
        lines.append("BEGIN TRANSACTION;");
        lines.append('INSERT INTO dbinfo VALUES(%s);'%(','.join(infoList)))
        for i, item in enumerate(self.data):
            w = item[0].replace('\'', '\'\'').replace('\r', '').replace('\n', newline)
            m = item[1].replace('\'', '\'\'').replace('\r', '').replace('\n', newline)
            lines.append("INSERT INTO word VALUES(%d,'%s','%s');"%(i+1, w, m))
        lines.append('END TRANSACTION;')
        lines.append('CREATE INDEX ix_word_w ON word(w COLLATE NOCASE);')
        return lines

    def utf8ReplaceErrors(self):
        errors = 0
        for i in xrange(len(self.data)):
            (w, m) = self.data[i][:2]
            w = w.replace('\x00', '')
            m = m.replace('\x00', '')
            try:
                m.decode('utf-8')
            except UnicodeDecodeError:
                m = m.decode('utf-8', 'replace').encode('utf-8')
                errors += 1
            try:
                w.decode('utf-8')
            except UnicodeDecodeError:
                w = w.decode('utf-8', 'replace').encode('utf-8')
                errors += 1
            if len(self.data[i]) >= 3:
                d = self.data[i][2]
                if 'alts' in d:
                    a = d['alts']
                    for j in xrange(len(a)):
                        a[j] = a[j].replace('\x00', '')
                        try:
                            a[j].decode('utf-8')
                        except UnicodeDecodeError:
                            a[j] = a[j].decode('utf-8', 'replace').encode('utf-8')
                            errors += 1
                d = [d]
            else:
                d = []
            a = [w, m]
            a.extend(d)
            a.extend(self.data[i][3:])
            self.data[i] = a
        for i in xrange(len(self.info)):
            (w, m) = self.info[i]
            w = w.replace('\x00', '')
            m = m.replace('\x00', '')
            try:
                m.decode('utf-8')
            except UnicodeDecodeError:
                m = m.decode('utf-8', 'replace').encode('utf-8')
                errors += 1
            try:
                w.decode('utf-8')
            except UnicodeDecodeError:
                w = w.decode('utf-8', 'replace').encode('utf-8')
                errors += 1
            self.info[i] = (w, m)
        if errors:
            log.error('There was %s number of invalid utf8 strings, invalid characters are replaced with "�"'%errors)

    def clean(self):
        d = self.data
        n = len(d)
        for i in range(n):
            # key must not contain tags, at least in bgl dictionary ???
            w = d[i][0].strip()
            m = d[i][1].strip()\
                       .replace('♦  ', '♦ ')

            m = re.sub('[\r\n]+', '\n', m)
            m = re.sub(' *\n *', '\n', m)

            '''
            This code may correct snippets like:
            - First sentence .Second sentence. -> First sentence. Second sentence.
            - First clause ,second clause. -> First clause, second clause.
            But there are cases when this code have undesirable effects
            ( '<' represented as '&lt;' in HTML markup):
            - <Adj.> -> < Adj. >
            - <fig.> -> < fig. >
            '''
            '''
            for j in range(3):
                for ch in ',.;':
                    m = replacePostSpaceChar(m, ch)
            '''

            m = re.sub('♦\n+♦', '♦', m)
            if m.endswith('<p'):
                m = m[:-2]
            m = m.strip()
            if m.endswith(','):
                m = m[:-1]
            d[i] = (w, m) + d[i][2:]
        # remove items with empty keys and definitions
        d2 = []
        for item in d:
            if not item[0] or not item[1]:
                continue
            if len(item) >= 3:
                if 'alts' in item[2]:
                    a = item[2]['alts']
                    a2 = []
                    for s in a:
                        if s:
                            a2.append(s)
                    item[2]['alts'] = a2
            d2.append(item)
        self.data[:] = d = d2

    def faEdit(self):
        RLM = '\xe2\x80\x8f'
        for i in range(len(self.data)):
            (w, m) = self.data[i][:2]
            ## m = '\n'.join([RLM+line for line in m.split('\n')]) ## for GoldenDict
            self.data[i] = (faEditStr(w), faEditStr(m)) + self.data[i][2:]
        for i in range(len(self.info)):
            (w, m) = self.info[i]
            self.info[i] = (faEditStr(w), faEditStr(m))

    def uiEdit(self):
        p = self.ui.pref
        if p['sort']:
            self.data.sort()
        if p['lower']:
            self.lowercase()
        if p['remove_tags']:
            self.removeTags(p['tags'])
        langs = (self.getInfo('sourceLang') + self.getInfo('targetLang')).lower()
        if 'persian' in langs or 'farsi' in langs:
            self.faEdit()
        self.clean()
        if p['utf8_check']:
            self.utf8ReplaceErrors()

    def getPref(self, name, default):
        if self.ui:
            return self.ui.pref.get(name, default)
        else:
            return default

    def dump(self, dataPath):
        'Dump data into the file for debugging'
        with open(dataPath, 'wb') as f:
            for item in g.data:
                f.write('key = ' + item[0] + '\n')
                f.write('defi = ' + item[1] + '\n\n')

Glossary.load_plugins(join(dirname(__file__), 'plugins'))
