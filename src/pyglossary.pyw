#!/usr/bin/python
# -*- coding: utf-8 -*-
##  ui_main.py 
##
##  Copyright © 2008-2010 Saeed Rasooli <saeed.gnu@gmail.com>  (ilius)
##  This file is part of PyGlossary project, http://sourceforge.net/projects/pyglossary/
##
##  This program is a free software; you can redistribute it and/or modify
##  it under the terms of the GNU General Public License as published by
##  the Free Software Foundation; either version 3, or (at your option)
##  any later version.
##
##  This program is distributed in the hope that it will be useful,
##  but WITHOUT ANY WARRANTY; without even the implied warranty of
##  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##  GNU General Public License for more details.
##
##  You should have received a copy of the GNU General Public License along
##  with this program. Or on Debian systems, from /usr/share/common-licenses/GPL
##  If not, see <http://www.gnu.org/licenses/gpl.txt>.

import os, sys, getopt
from glossary import confPath, VERSION
from ui_cmd import COMMAND, printAsError, help, parseFormatOptionsStr
#from text_utils import printAsError ## No red color, plain


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

path = ''
"""Interface type
Possible values:
cmd - command line mode
gtk - GTK GUI
tk - TK GUI
qt - QT GUI
auto - use the first available GUI
"""
ui_type = 'cmd'

available_options = ['version', 'help', 'ui=', 'read-options=', 'write-options=', 
                     'read-format=', 'write-format=', 'reverse', 'no-progress-bar']

## FIXME: load ui-dependent available options from ui modules (for example ui_cmd.available_options)
## the only problem is that it has to "import gtk" before it get the "ui_gtk.available_options"

try:
  (options, arguments) = getopt.gnu_getopt(
    sys.argv[1:],
    'vhu:r:w:',
    available_options
  )
except getopt.GetoptError:
  printAsError(sys.exc_info()[1])
  print 'try: %s --help'%COMMAND
  sys.exit(1)

if len(arguments)<1:
  ui_type = 'auto' ## Open GUI, not command line usage
  ipath = opath = ''
else:
  ipath = arguments[0]
  if len(arguments)>1:
    opath = arguments[1]
  else:
    opath = ''

read_format = ''
write_format = ''
read_options = {}
write_options = {}
ui_options = {}
reverse = False
# only for command line UI
enable_progress_bar = True

for (opt, opt_arg) in options:
  if opt in ('-v', '--version'):
    print('PyGlossary %s'%VERSION)
    sys.exit(0)
  elif opt in ('-h', '--help'):
    help()
    sys.exit(0)
  elif opt in ('-u', '--ui'):
    if opt_arg in ui_list:
      ui_type = opt_arg
    else:
      printAsError('invalid ui type %s'%opt_arg)
  elif opt in ('-r', '--read-options'):
    read_options = parseFormatOptionsStr(opt_arg)
  elif opt in ('-w', '--write-options'):
    write_options = parseFormatOptionsStr(opt_arg)
  elif opt == '--read-format':
    read_format = opt_arg
  elif opt == '--write-format':
    write_format = opt_arg
  elif opt == '--reverse':
    reverse = True
  elif opt.startswith('--'):
    ui_options[dashToCamelCase(opt[2:])] = opt_arg ## opt_arg is not None, UI just ignores None value


## FIXME
## -v  (verbose or version?)
## -r  (reverse or read-options)

if ui_type == 'cmd' and not ipath and not (reverse or opath or write_format):
  ui_type = 'auto'

if ui_type == 'cmd':
  import ui_cmd
  sys.exit(ui_cmd.UI(text='Loading: ', **ui_options).run(
    ipath,
    opath=opath,
    read_format=read_format,
    write_format=write_format, 
    read_options=read_options,
    write_options=write_options, 
    reverse=reverse
  ))
else:
  if ui_type=='auto':
    ui_module = None
    for ui_type2 in ui_list:
      try:
        ui_module = __import__('ui_%s'%ui_type2)
      except ImportError:
        pass
      else:
        break
    if ui_module==None:
      printAsError('no user interface module found!')
      sys.exit(1)
  else:
    ui_module = __import__('ui_%s'%ui_type)
  sys.exit(ui_module.UI(ipath, **ui_options).run())
  ## don't forget to append "**options" at every UI.__init__ arguments

