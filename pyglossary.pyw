#!/usr/bin/env python3
# -*- coding: utf-8 -*-
## ui_main.py
##
## Copyright © 2008-2010 Saeed Rasooli <saeed.gnu@gmail.com>    (ilius)
## This file is part of PyGlossary project, http://sourceforge.net/projects/pyglossary/
##
## This program is a free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 3, or (at your option)
## any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License along
## with this program. Or on Debian systems, from /usr/share/common-licenses/GPL
## If not, see <http://www.gnu.org/licenses/gpl.txt>.

import os, sys
import argparse
import builtins
from os.path import dirname, join, realpath
from pprint import pformat
import logging
import inspect
import traceback

from pyglossary import core ## essential
from pyglossary import VERSION
from pyglossary.text_utils import startRed, endFormat

# the first thing to do is to set up logger.
# other modules also using logger 'root', so it's essential to set it up prior
# to importing anything else; with exception to pyglossary.core which sets up
# logger class, and so should be done before actually initializing logger.
# verbosity level may be given on command line, so we have to parse arguments
# before setting up logger.
# once more:
# - import system modules like os, sys, argparse etc and pyglossary.core
# - parse args
# - set up logger
# - import submodules
# - other code

## no-progress-bar only for command line UI
## FIXME: load ui-dependent available options from ui modules (for example ui_cmd.available_options)
## the only problem is that it has to "import gtk" before it get the "ui_gtk.available_options"

## FIXME
## -v (verbose or version?)
## -r (reverse or read-options)

parser = argparse.ArgumentParser(add_help=False)

parser.add_argument(
    '-v',
    '--verbosity',
    action='store',
    dest='verbosity',
    type=int,
    choices=(0, 1, 2, 3, 4),
    required=False,
    default=3,## FIXME
)
parser.add_argument(
    '--version',
    action='version',
    version='PyGlossary %s'%VERSION,
)
parser.add_argument(
    '-h',
    '--help',
    dest='help',
    action='store_true',
)
parser.add_argument(
    '-u',
    '--ui',
    dest='ui_type',
    default='auto',
    choices=(
        'cmd',
        'gtk',
        'tk',
        #'qt',
        'auto',
    ),
)
parser.add_argument(
    '-r',
    '--read-options',
    dest='read_options',
    default='',
)
parser.add_argument(
    '-w',
    '--write-options',
    dest='write_options',
    default='',
)
parser.add_argument(
    #'-',
    '--read-format',
    dest='read_format',
)
parser.add_argument(
    #'-',
    '--write-format',
    dest='write_format',
    action='store',
)
parser.add_argument(
    #'-',
    '--direct',
    dest='direct',
    action='store_true',
    default=None,
    help='if possible, convert directly without loading into memory',
)
parser.add_argument(
    #'-',
    '--indirect',
    dest='direct',
    action='store_false',
    default=None,
    help='disable `direct` mode, load full data into memory before writing, this is default',
)
parser.add_argument(
    #'-',
    '--reverse',
    dest='reverse',
    action='store_true',
)
parser.add_argument(
    #'-',
    '--no-progress-bar',
    dest='noProgressBar',
    action='store_true',
    default=None,
)
parser.add_argument(
    #'-',
    '--sort',
    dest='sort',
    action='store_true',
    default=None,
)
parser.add_argument(
    #'-',
    '--no-sort',
    dest='sort',
    action='store_false',
    default=None,
)
parser.add_argument(
    #'-',
    '--sort-cache-size',
    dest='sort_cache_size',
    type=int,
    default=1000,
)

parser.add_argument(
    #'-',
    '--utf8-check',
    dest='utf8_check',
    action='store_true',
    default=None,
)
parser.add_argument(
    #'-',
    '--no-utf8-check',
    dest='utf8_check',
    action='store_false',
    default=None,
)
parser.add_argument(
    #'-',
    '--lower',
    dest='lower',
    action='store_true',
    default=None,
    help='lowercase words before writing',
)
parser.add_argument(
    #'-',
    '--no-lower',
    dest='lower',
    action='store_false',
    default=None,
    help='don\'t lowercase words before writing',
)

parser.add_argument(
    #'-',
    '--no-color',
    dest='noColor',
    action='store_true',
)
parser.add_argument(
    'ipath',
    action='store',
    default='',
    nargs='?',
)
parser.add_argument(
    'opath',
    action='store',
    default='',
    nargs='?',
)

args = parser.parse_args()
#log.debug(args) ; sys.exit(0)

def format_exception(exc_info=None, add_locals=False, add_globals=False):
    if not exc_info:
        exc_info = sys.exc_info()
    _type, value, tback = exc_info
    text = ''.join(traceback.format_exception(_type, value, tback))

    if add_locals or add_globals:
        try:
            frame = inspect.getinnerframes(tback, context=0)[-1][0]
        except IndexError:
            pass
        else:
            if add_locals:
                text += 'Traceback locals: %s\n'%pformat(frame.f_locals)
            if add_globals:
                text += 'Traceback globals: %s\n'%pformat(frame.f_globals)

    return text



class StdLogHandler(logging.Handler):
    def __init__(self, noColor=False):
        logging.Handler.__init__(self)
        self.noColor = noColor
    def emit(self, record):
        msg = record.getMessage()
        ###
        if record.exc_info:
            _type, value, tback = record.exc_info
            tback_text = format_exception(
                exc_info = record.exc_info,
                add_locals = (log.level <= logging.DEBUG),## FIXME
                add_globals = False,
            )

            if not msg:
                msg = 'unhandled exception:'
            msg += '\n'
            msg += tback_text
        ###
        if record.levelname in ('CRITICAL', 'ERROR'):
            if not self.noColor:
                msg = startRed + msg + endFormat
            fp = sys.stderr
        else:
            fp = sys.stdout
        ###
        fp.write(msg + '\n')
        fp.flush()
    #def exception(self, msg):
    #    if not self.noColor:
    #        msg = startRed + msg + endFormat
    #    sys.stderr.write(msg + '\n')
    #    sys.stderr.flush()


log = logging.getLogger('root')
log.setVerbosity(args.verbosity)
log.addHandler(
    StdLogHandler(noColor=args.noColor),
)


# with the logger setted up, we can import other pyglossary modules, so they
# can do some loggging in right way.

##############################

def my_excepthook(*exc_info):
    tback_text = format_exception(
        exc_info = exc_info,
        add_locals = (log.level <= logging.DEBUG),## FIXME
        add_globals = False,
    )
    log.critical(tback_text)
sys.excepthook = my_excepthook

##############################

from pyglossary.glossary import confPath
from ui.ui_cmd import COMMAND, help, parseFormatOptionsStr

##############################

def dashToCamelCase(text):## converts "hello-PYTHON-user" to "helloPythonUser"
    parts = text.split('-')
    parts[0] = parts[0].lower()
    for i in range(1, len(parts)):
        parts[i] = parts[i].capitalize()
    return ''.join(parts)

use_psyco_file = '%s_use_psyco'%confPath
psyco_found = None

ui_list = (
    'gtk',
    'gtk_new',
    'tk',
    'qt',
)

#log.info('PyGlossary %s'%VERSION)

if os.path.isfile(use_psyco_file):
    try:
        import psyco
    except ImportError:
        log.warning('Warning: module "psyco" not found. It could speed up execution.')
        psyco_found = False
    else:
        psyco.full()
        log.info('Using module "psyco" to speed up execution.')
        psyco_found = True


if args.help:
    help()
    sys.exit(0)


if os.sep != '/':
    args.noColor = True


## only used in ui_cmd for now
read_options = parseFormatOptionsStr(args.read_options)
write_options = parseFormatOptionsStr(args.write_options)

if args.direct != None:
    read_options['direct'] = args.direct


"""
    examples for read and write options:
    --read-options testOption=stringValue
    --read-options enableFoo=True
    --read-options fooList=[1,2,3]
    --read-options 'fooList=[1, 2, 3]'
    --read-options 'testOption=stringValue; enableFoo=True; fooList=[1, 2, 3]'
    --read-options 'testOption=stringValue;enableFoo=True;fooList=[1,2,3]'
"""



## FIXME
ui_options_params = (
    'noProgressBar',
    #'verbosity',
    'sort',
    'sort_cache_size',
    'utf8_check',
    'lower',
)

ui_options = {}
for param in ui_options_params:
    value = getattr(args, param, None)
    if value is not None:
        ui_options[param] = value


log.pretty(ui_options, 'ui_options =')

"""
ui_type: User interface type
Possible values:
    cmd - Command line interface, this ui will automatically selected if you give both input and output file
    gtk - GTK interface
    tk - Tkinter interface
    qt - Qt interface
    auto - Use the first available UI
"""
ui_type = args.ui_type

#if len(arguments)<1:## open GUI
#    ipath = opath = ''
#elif len(arguments)==1:## open GUI, in edit mode (if gui support, like DB Editor in ui_gtk)
#    ipath = arguments[0]
#    opath = ''
#else:## run the commnad line interface
#    ui_type = 'cmd'
#    ipath = arguments[0]
#    opath = arguments[1]


if args.ipath:
    if args.opath:
        ui_type = 'cmd' ## silently? FIXME
else:
    if ui_type == 'cmd':
        log.error('no input file given, try --help')
        exit(1)

#try:
if ui_type == 'cmd':
    from ui import ui_cmd
    sys.exit(ui_cmd.UI(**ui_options).run(
        args.ipath,
        opath=args.opath,
        read_format=args.read_format,
        write_format=args.write_format,
        read_options=read_options,
        write_options=write_options,
        reverse=args.reverse,
    ))
if ui_type=='auto':
    ui_module = None
    for ui_type2 in ui_list:
        try:
            ui_module = getattr(__import__('ui.ui_%s'%ui_type2), 'ui_%s'%ui_type2)
        except ImportError:
            log.exception('error while importing UI module:')## FIXME
        else:
            break
    if ui_module==None:
        log.error('no user interface module found!')
        sys.exit(1)
else:
    ui_module = getattr(__import__('ui.ui_%s'%ui_type), 'ui_%s'%ui_type)
sys.exit(ui_module.UI(**ui_options).run(
    editPath=args.ipath,
    read_options=read_options,
))
## don't forget to append "**options" at every UI.__init__ arguments
#except Exception as e:
#    log.exception('')



