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

log = logging.getLogger("root")

from pprint import pformat

from paths import rootDir
sys.path.insert(0, rootDir)

from pyglossary.flags import *

from pyglossary import core
from pyglossary.option import *
from pyglossary.file_utils import FileLineWrapper
from pyglossary.text_utils import toStr, toBytes
from pyglossary.os_utils import indir

enable = False
format = "Unknown"
description = "Unknown"
extentions = [] # type: List[str]
readOptions = [] # type: List[str]
writeOptions = [] # type: List[str]

# key is option/argument name, value is instance of Option
optionsProp = {} # type: Dict[str, Option]

depends = {}
supportsAlternates = False
sortOnWrite = DEFAULT_NO
sortKey = None
