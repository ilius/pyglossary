# -*- coding: utf-8 -*-
# ui_cmd.py
#
# Copyright © 2008-2010 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
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

from os.path import join
import time
import signal

from pyglossary.glossary import *
from .base import *
from . import progressbar as pb


if os.sep == '\\':  # Operating system is Windows
    startRed = ''
    endFormat = ''
    startBold = ''
    startUnderline = ''
    endFormat = ''
else:
    startRed = '\x1b[31m'
    endFormat = '\x1b[0;0;0m'

    startBold = '\x1b[1m'  # Start Bold # len=4
    startUnderline = '\x1b[4m'  # Start Underline # len=4
    endFormat = '\x1b[0;0;0m'  # End Format # len=8
    # redOnGray = '\x1b[0;1;31;47m'


COMMAND = 'pyglossary'
# COMMAND = sys.argv[0]


def getColWidth(subject, strings):
    return max(
        len(x) for x in [subject] + strings
    )


def getFormatsTable(names, header):
    descriptions = [
        Glossary.formatsDesc[name]
        for name in names
    ]
    extentions = [
        ' '.join(Glossary.formatsExt[name])
        for name in names
    ]

    nameWidth = getColWidth('Name', names)
    descriptionWidth = getColWidth('Description', descriptions)
    extentionsWidth = getColWidth('Extentions', extentions)

    lines = ['\n']
    lines.append('%s%s%s' % (startBold, header, endFormat))

    lines.append(
        ' | '.join([
            'Name'.center(nameWidth),
            'Description'.center(descriptionWidth),
            'Extentions'.center(extentionsWidth)
        ])
    )
    lines.append(
        '-+-'.join([
            '-' * nameWidth,
            '-' * descriptionWidth,
            '-' * extentionsWidth,
        ])
    )
    for index, name in enumerate(names):
        lines.append(
            ' | '.join([
                name.ljust(nameWidth),
                descriptions[index].ljust(descriptionWidth),
                extentions[index].ljust(extentionsWidth)
            ])
        )

    return '\n'.join(lines)


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
    text += getFormatsTable(Glossary.readFormats, 'Supported input formats:')
    text += getFormatsTable(Glossary.writeFormats, 'Supported output formats:')
    print(text)


def parseFormatOptionsStr(st):
    st = st.strip()
    if not st:
        return {}

    opt = {}
    parts = st.split(';')
    for part in parts:
        try:
            (key, value) = part.split('=')
        except ValueError:
            log.error('bad option syntax: %s' % part)
            continue
        key = key.strip()
        value = value.strip()
        # if it is string form of a number or boolean or tuple ...
        try:
            newValue = eval(value)
        except:
            pass
        else:
            if isinstance(newValue, (
                bool,
                int,
                float,
                tuple,
                list,
                dict,
            )):
                value = newValue
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
    def __init__(self, **options):
        self.pref = {}
        # log.debug(self.pref)
        self.pbar = NullObj()
        self._toPause = False

    def onSigInt(self, *args):
        if self._toPause:
            log.info('\nOperation Canceled')
            sys.exit(0)
        else:
            self._toPause = True
            log.info('\nPlease wait...')

    def setText(self, text):
        self.pbar.widgets[0] = text

    def progressInit(self, title):
        rot = pb.RotatingMarker()
        self.pbar = pb.ProgressBar(
            widgets=[
                title,
                pb.Bar(marker='█', right=rot),
                pb.Percentage(),
                '% ',
                pb.ETA(),
            ],
            maxval=1.0,
            update_step=0.5,
        )
        rot.pbar = self.pbar

    def progress(self, rat, text=''):
        self.pbar.update(rat)

    def reverseLoop(self, *args, **kwargs):
        reverseKwArgs = {}
        for key in (
            'words',
            'matchWord',
            'showRel',
            'includeDefs',
            'reportStep',
            'saveStep',
            'maxNum',
            'minRel',
            'minWordLen'
        ):
            try:
                reverseKwArgs[key] = self.pref['reverse_' + key]
            except KeyError:
                pass
        reverseKwArgs.update(kwargs)

        # log.pretty(reverseKwArgs, 'reverseKwArgs = ')
        if not self._toPause:
            log.info('Reversing glossary... (Press Ctrl+C to pause/stop)')
        for wordI in self.glos.reverse(**reverseKwArgs):
            if self._toPause:
                log.info(
                    'Reverse is paused.'
                    ' Press Enter to continue, and Ctrl+C to exit'
                )
                input()
                self._toPause = False

    def run(
        self,
        inputFilename,
        outputFilename='',
        inputFormat='',
        outputFormat='',
        reverse=False,
        prefOptions=None,
        readOptions=None,
        writeOptions=None,
        convertOptions=None,
    ):
        if not prefOptions:
            prefOptions = {}
        if not readOptions:
            readOptions = {}
        if not writeOptions:
            writeOptions = {}
        if not convertOptions:
            convertOptions = {}

        self.pref_load(**prefOptions)

        if inputFormat:
            # inputFormat = inputFormat.capitalize()
            if inputFormat not in Glossary.readFormats:
                log.error('invalid read format %s' % inputFormat)
        if outputFormat:
            # outputFormat = outputFormat.capitalize()
            if outputFormat not in Glossary.writeFormats:
                log.error('invalid write format %s' % outputFormat)
                log.error('try: %s --help' % COMMAND)
                return 1
        if not outputFilename:
            if reverse:
                pass
            elif outputFormat:
                try:
                    ext = Glossary.formatsExt[outputFormat][0]
                except (KeyError, IndexError):
                    log.error('invalid write format %s' % outputFormat)
                    log.error('try: %s --help' % COMMAND)
                    return 1
                else:
                    outputFilename = os.path.splitext(inputFilename)[0] + ext
            else:
                log.error('neither output file nor output format is given')
                log.error('try: %s --help' % COMMAND)
                return 1

        glos = self.glos = Glossary(ui=self)
        if reverse:
            signal.signal(signal.SIGINT, self.onSigInt)  # good place? FIXME
            readOptions['direct'] = False
            if not glos.read(
                inputFilename,
                format=inputFormat,
                **readOptions
            ):
                log.error('reading input file was failed!')
                return False
            self.setText('Reversing: ')
            self.pbar.update_step = 0.1
            self.reverseLoop(savePath=outputFilename)
        else:
            finalOutputFile = self.glos.convert(
                inputFilename,
                inputFormat=inputFormat,
                outputFilename=outputFilename,
                outputFormat=outputFormat,
                readOptions=readOptions,
                writeOptions=writeOptions,
                **convertOptions
            )
            return bool(finalOutputFile)

        return True
