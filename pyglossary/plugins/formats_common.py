from formats_common import *

enable = False
format = 'Unknown'
description = 'Unknown'
extentions = []
readOptions = []
writeOptions = []
supportsAlternates = False

import sys, os
sys.path.append('/usr/share/pyglossary')

from os.path import splitext
from os.path import split as path_split
from os.path import join as path_join
import logging

from pyglossary import core

log = logging.getLogger('root')

