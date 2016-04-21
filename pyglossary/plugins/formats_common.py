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

log = logging.getLogger('root')

from pyglossary import core
from pyglossary.file_utils import FileLineWrapper
from pyglossary.text_utils import toStr, toBytes
from pyglossary.os_utils import indir
from pyglossary.entry import Entry


