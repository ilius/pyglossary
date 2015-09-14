#!/usr/bin/env python2
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
import __builtin__
from pyglossary.glossary import confPath, VERSION
#from pyglossary.text_utils import printAsError ## No red color, plain
from os.path import dirname, join, realpath

from ui.ui_cmd import COMMAND, printAsError, help, parseFormatOptionsStr

def myRaise(File=None):
    i = sys.exc_info()
    if File==None:
        sys.stderr.write('line %s: %s: %s'%(i[2].tb_lineno, i[0].__name__, i[1]))
    else:
        sys.stderr.write('File "%s", line %s: %s: %s'%(File, i[2].tb_lineno, i[0].__name__, i[1]))

def dashToCamelCase(text):## converts "hello-PYTHON-user" to "helloPythonUser"
    parts = text.split('-')
    parts[0] = parts[0].lower()
    for i in range(1, len(parts)):
        parts[i] = parts[i].capitalize()
    return ''.join(parts)

use_psyco_file = '%s_use_psyco'%confPath
psyco_found = None


ui_list = ('gtk', 'tk', 'qt')

#print('PyGlossary %s'%VERSION)

if os.path.isfile(use_psyco_file):
    try:
        import psyco
    except ImportError:
        print('Warning: module "psyco" not found. It could speed up execution.')
        psyco_found = False
    else:
        psyco.full()
        print('Using module "psyco" to speed up execution.')
        psyco_found = True


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
    choices=(0, 1, 2, 3),
    required=False,
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
    '--reverse',
    dest='reverse',
    action='store_true',
)
parser.add_argument(
    #'-',
    '--no-progress-bar',
    dest='noProgressBar',
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
#print args ; sys.exit(0)



if args.help:
    help()
    sys.exit(0)

## only used in ui_cmd for now
read_options = parseFormatOptionsStr(args.read_options)
write_options = parseFormatOptionsStr(args.write_options)

'''
    examples for read and write options:
    --read-options testOption=stringValue
    --read-options enableFoo=True
    --read-options fooList=[1,2,3]
    --read-options 'fooList=[1, 2, 3]'
    --read-options 'testOption=stringValue; enableFoo=True; fooList=[1, 2, 3]'
    --read-options 'testOption=stringValue;enableFoo=True;fooList=[1,2,3]'
'''



## FIXME
ui_options_params = (
    'noProgressBar',
)

ui_options = {}
for param in ui_options_params:
    ui_options[param] = getattr(args, param, None)


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
        printAsError('no input file given, try --help')
        exit(1)

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
else:
    if ui_type=='auto':
        ui_module = None
        for ui_type2 in ui_list:
            try:
                ui_module = getattr(__import__('ui.ui_%s'%ui_type2), 'ui_%s'%ui_type2)
            except ImportError:
                myRaise()## FIXME
            else:
                break
        if ui_module==None:
            printAsError('no user interface module found!')
            sys.exit(1)
    else:
        ui_module = getattr(__import__('ui.ui_%s'%ui_type), 'ui_%s'%ui_type)
    sys.exit(ui_module.UI(**ui_options).run(
        editPath=args.ipath,
        read_options=read_options,
    ))
    ## don't forget to append "**options" at every UI.__init__ arguments

