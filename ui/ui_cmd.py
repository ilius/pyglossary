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
        self.reverseStop = False
        self.pref = {}
        self.pref_load(**options)
        #log.debug(self.pref)
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
    def r_start(self, *args):
        self.rWords = self.glosR.takeOutputWords()
        log.info('Number of input words:', len(self.rWords))
        log.info('Reversing glossary... (Press Ctrl+C to stop)')
        try:
            self.glosR.reverseDic(self.rWords, self.pref)
        except KeyboardInterrupt:
            self.r_stop()
            ## if the file closeed ????
    def r_stop(self, *args):
        self.glosR.continueFrom = self.glosR.i
        self.glosR.stoped = True
        self.reverseStop = True
        log.info('Stoped! Press Enter to resume, and press Ctrl+C to quit.')
        try:
            input()
        except KeyboardInterrupt:
            return 0
        else:
            self.r_resume()
    def r_resume(self, *args):
        if self.glosR.stoped==True:
            ## update reverse configuration?
            self.reverseStop = False
            log.info('Continue reversing from index %d ...'%self.glosR.continueFrom)
            try:
                self.glosR.reverseDic(self.rWords, self.pref)
            except KeyboardInterrupt:
                self.r_stop()
        else:
            log.info('self.glosR.stoped=%s'%self.glosR.stoped)
            log.info('Not stoped yet. Wait many seconds and press "Resume" again...')
    def r_finished(self, *args):
        self.glosR.continueFrom=0
        log.info('Reversing completed.')
    def yesNoQuestion(self, msg, yesDefault=True):## FIXME
        return True
    def run(self, ipath, opath='', read_format='', write_format='',
                  read_options={}, write_options={}, reverse=False):
        if read_format:
            #read_format = read_format.capitalize()
            if not read_format in Glossary.readFormats:
                log.error('invalid read format %s'%read_format)
        if write_format:
            #write_format = write_format.capitalize()
            if not write_format in Glossary.writeFormats:
                log.error('invalid write format %s'%write_format)
                log.error('try: %s --help'%COMMAND)
                return 1
        if not opath:
            if reverse:
                opath = os.path.splitext(ipath)[0] + '-reversed.txt'
            elif write_format:
                try:
                    ext = Glossary.formatsExt[write_format][0]
                except (KeyError, IndexError):
                    log.error('invalid write format %s'%write_format)
                    log.error('try: %s --help'%COMMAND)
                    return 1
                else:
                    opath = os.path.splitext(ipath)[0] + ext
            else:
                log.error('neither output file nor output format is given')
                log.error('try: %s --help'%COMMAND)
                return 1
        g = Glossary(ui=self)
        log.info('Reading file "%s"'%ipath)
        if not g.read(ipath, format=read_format, **read_options):
            log.error('reading input file was failed!')
            return 1
        ## When glossary reader uses progressbar, progressbar must be rebuilded:
        self.progressBuild()
        g.uiEdit()
        if reverse:
            log.info('Reversing to file "%s"'%opath)
            self.setText('')
            self.pbar.update_step = 0.1
            self.pref['savePath'] = opath
            self.glosR = g
            self.r_start()
        else:
            log.info('Writing to file "%s"'%opath)
            self.setText('Writing: ')
            if not g.write(opath, format=write_format, **write_options):
                log.error('writing output file was failed!')
                return 1
            log.info('done')
        return 0
