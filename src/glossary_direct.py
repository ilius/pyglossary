#!/usr/bin/python
# -*- coding: utf-8 -*-
##  glossary.py
##
##  Copyright © 2008-2010 Saeed Rasooli <saeed.gnu@gmail.com>  (ilius)
##  Thanks to 'Mehdi Bayazee' and 'carp3(Pedram Azimaie)' for program bgl2xdb.py
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

VERSION = '2010.2.20'

licenseText='''PyGlossary - A tool for workig with dictionary databases
Copyright © 2008-2010 Saeed Rasooli
This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation; either version 3 of the License,  or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program. Or on Debian systems, from /usr/share/common-licenses/GPL. If not, see <http://www.gnu.org/licenses/gpl.txt>.'''


homePage = 'http://sourceforge.net/projects/pyglossary'
## homePage = 'http://ospdev.net/projects/glossary-pywork'


import string, os, sys, time
from text_utils import *
from glossary import Glossary

import warnings
warnings.resetwarnings()


initCwd = os.getcwd()
srcDir = os.path.dirname(sys.argv[0])
rootDir = os.path.dirname(srcDir)
libDir=os.path.join(rootDir,'dependencies','py2.5-lib')
if os.path.isdir(libDir):
  sys.path.append(libDir)
plugDir = os.path.join(rootDir,'plugins')
if os.path.isdir(plugDir):
  sys.path.append(plugDir)
else:
  plugDir = ''
libDir = os.path.join(rootDir,'lib')
sys.path.append(libDir)



if os.sep=='/': ## Operating system is unix-like
  homeDir = os.getenv('HOME')
  confDir = homeDir
  tmpDir  = '/tmp'
  user    = os.getenv('USER')
elif os.sep=='\\': ## Operating system is windows
  homeDir = os.getenv('HOMEDRIVE')+os.getenv('HOMEPATH')
  confDir = os.getenv('APPDATA')
  tmpDir  = os.getenv('TEMP')
  user    = os.getenv('USERNAME')
else:
  raise RuntimeError('Unknown path seperator(os.sep=="%s") ! What is your operating system?'%os.sep)


#class DGlossary(Glossary):
#  def convert(


