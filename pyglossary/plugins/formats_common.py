from formats_common import *

import sys
import os
from os.path import (
	join,
	split,
	splitext,
	isfile,
	isdir,
	exists,
)

import logging

log = logging.getLogger('root')

from paths import rootDir
sys.path.insert(0, rootDir)

from pyglossary.flags import *

from pyglossary import core
from pyglossary.file_utils import FileLineWrapper
from pyglossary.text_utils import toStr, toBytes
from pyglossary.os_utils import indir

enable = False
format = 'Unknown'
description = 'Unknown'
extentions = []
readOptions = []
writeOptions = []
supportsAlternates = False
sortOnWrite = DEFAULT_NO
sortKey = None
