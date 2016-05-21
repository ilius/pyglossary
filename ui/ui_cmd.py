# -*- coding: utf-8 -*-
## ui_cmd.py
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

from os.path import join
import time

from pyglossary.glossary import *
from .base import *
from . import progressbar as pb


if os.sep=='\\': ## Operating system is Windows
    startRed = ''
    endFormat = ''
    startBold = ''
    startUnderline = ''
    endFormat = ''
else:
    startRed = '\x1b[31m'
    endFormat = '\x1b[0;0;0m'

    startBold = '\x1b[1m' ## Start Bold ## len=4
    startUnderline = '\x1b[4m' ## Start Underline ## len=4
    endFormat = '\x1b[0;0;0m' ## End Format ## len=8
    #redOnGray = '\x1b[0;1;31;47m'


COMMAND = 'pyglossary'
#COMMAND = sys.argv[0]



def formats_table(formats, header):
    names = []
    descriptions = []
    extentions = []
    for f in formats:
        names.append(f)
        descriptions.append(Glossary.formatsDesc[f])
        extentions.append(Glossary.formatsExt[f])
    extentions = list(map(' '.join, extentions))

    maxlen = lambda s, seq: max(len(s), max(list(map(len, seq))))
    names_max = maxlen('name', names)
    descriptions_max = maxlen('description', descriptions)
    extentions_max = maxlen('extentions', extentions)

    s = '\n%s%s%s\n' % (startBold, header, endFormat)
    s += ' | '.join(['name'.center(names_max),
                     'description'.center(descriptions_max),
                     'extentions'.center(extentions_max)]) + '\n'
    s += '-+-'.join(['-' * names_max,
                     '-' * descriptions_max,
                     '-' * extentions_max])+ '\n'
    for i in range(len(names)):  # formats may be lazy, but `names' is a list
        s += ' | '.join([names[i].ljust(names_max),
                         descriptions[i].ljust(descriptions_max),
                         extentions[i].ljust(extentions_max)]) + '\n'
    return s


def help():
    import string
    with open(join(rootDir, 'help')) as fp:
        text = fp.read()
    text = text.replace('<b>', startBold)\
        .replace('<u>', startUnderline)\
        .replace('</b>', endFormat)\
        .replace('</u>', endFormat)
    text = string.Template(text).substitute(
        CMD=COMMAND,
    )
    text += formats_table(Glossary.readFormats, 'Supported input formats:')
    text += formats_table(Glossary.writeFormats, 'Supported output formats:')
    print(text)


def parseFormatOptionsStr(st):
    st = st.strip()
    if not st:
        return {}
    ###
    opt = {}
    parts = st.split(';')
    for part in parts:
        try:
            (key, value) = part.split('=')
        except ValueError:
            log.error('bad option syntax: %s'%part)
            continue
        key = key.strip()
        value = value.strip()
        try:
            value = eval(value) ## if it is string form of a number or boolean or tuple ...
        except:
            pass
        opt[key] = value
    return opt

class NullObj(object):
    def __getattr__(self, attr):
        return self
    def __setattr__(self, attr, value):
        pass
    def __call__(self, *args, **kwargs):
        pass

class UI(UIBase):
    def __init__(self, text='Loading: ', noProgressBar=None, **options):
        self.ptext = text
        self.pref = {}
        self.pref_load(**options)
        #log.debug(self.pref)
        self.reverseKwArgs = {}
        if self.pref['noProgressBar']:
            self.pbar = NullObj()
        else:
            self.progressBuild()
    def setText(self, text):
        self.pbar.widgets[0]=text
    def progressStart(self):
        self.pbar.start()
    def progress(self, rat, text=''):
        self.pbar.update(rat)
    def progressEnd(self):
        self.pbar.finish()
        print('')
    def progressBuild(self):
        rot = pb.RotatingMarker()
        ## SyntaxError(invalid syntax) with python3 with unicode(u'█') argument ## FIXME
        self.pbar = pb.ProgressBar(
            widgets=[
                self.ptext,
                pb.Bar(marker='█', right=rot),
                pb.Percentage(),
                '% ',
                pb.ETA(),
            ],
            maxval=1.0,
            update_step=0.5,
        )
        rot.pbar = self.pbar
    def reverseStart(self, *args):
        log.info('Reversing glossary... (Press Ctrl+C to stop)')
        for key in (
            'words',
            'matchWord',
            'showRel',
            'includeDefs',
            'reportStep',
            'saveStep',
            'savePath',
            'maxNum',
            'minRel',
            'minWordLen'
        ):
            try:
                self.reverseKwArgs[key] = self.pref['reverse_' + key]
            except KeyError:
                pass
        if self.reverseKwArgs:
            log.pretty(self.reverseKwArgs, 'UI.reverseStart: reverseKwArgs = ')
        try:
            self.glos.reverse(
                **self.reverseKwArgs
            )
        except KeyboardInterrupt:
            self.reversePauseWait()
            ## is the file closeed? FIXME
    def reversePauseWait(self, *args):
        self.glos.pause()
        log.info('Waiting for Glossary to be paused ...')
        while not self.glos.isPaused():
            time.sleep(0.1)
        log.info('Reverse is paused. Press Enter to resume, and press Ctrl+C to quit.')
        try:
            input()
        except KeyboardInterrupt:
            return 0
        self.reverseResume()
    def reverseResume(self, *args):
        ## update reverse configuration?
        log.info('Continue reversing from index %d ...'%self.glos.continueFrom)
        try:
            self.glos.reverse(
                **self.reverseKwArgs
            )
        except KeyboardInterrupt:
            self.reversePauseWait()
    def run(
        self,
        ipath,
        opath = '',
        readFormat = '',
        writeFormat = '',
        readOptions = None,
        writeOptions = None,
        reverse = False,
    ):
        if not readOptions:
            readOptions = {}
        if not writeOptions:
            writeOptions = {}

        if readFormat:
            #readFormat = readFormat.capitalize()
            if not readFormat in Glossary.readFormats:
                log.error('invalid read format %s'%readFormat)
        if writeFormat:
            #writeFormat = writeFormat.capitalize()
            if not writeFormat in Glossary.writeFormats:
                log.error('invalid write format %s'%writeFormat)
                log.error('try: %s --help'%COMMAND)
                return 1
        if not opath:
            if reverse:
                pass
            elif writeFormat:
                try:
                    ext = Glossary.formatsExt[writeFormat][0]
                except (KeyError, IndexError):
                    log.error('invalid write format %s'%writeFormat)
                    log.error('try: %s --help'%COMMAND)
                    return 1
                else:
                    opath = os.path.splitext(ipath)[0] + ext
            else:
                log.error('neither output file nor output format is given')
                log.error('try: %s --help'%COMMAND)
                return 1
        g = self.glos = Glossary(ui=self)
        log.info('Reading file "%s"'%ipath)
        if not g.read(ipath, format=readFormat, **readOptions):
            log.error('reading input file was failed!')
            return 1
        ## When glossary reader uses progressbar, progressbar must be rebuilded:
        self.progressBuild()
        if reverse:
            self.setText('Reversing: ')
            self.pbar.update_step = 0.1
            self.reverseKwArgs['savePath'] = opath
            self.reverseStart()
        else:
            self.setText('Writing: ')
            if not g.write(opath, format=writeFormat, **writeOptions):
                log.error('writing output file was failed!')
                return 1
            log.info('done')
        return 0
