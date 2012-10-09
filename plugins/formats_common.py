enable = False
format = 'Unknown'
description = 'Unknown'
extentions = []
readOptions = []
writeOptions = []
supportsAlternates = False

import sys, os
sys.path.append('/usr/share/pyglossary/src')

from os.path import splitext
from os.path import split as path_split
from os.path import join as path_join

from text_utils import myRaise, printAsError

