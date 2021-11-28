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

log = logging.getLogger("pyglossary")

from pprint import pformat

from pyglossary.core import rootDir
sys.path.insert(0, rootDir)

from pyglossary.flags import *

from pyglossary import core
from pyglossary.core import (
	pip,
	cacheDir,
)
from pyglossary.option import *
from pyglossary.text_utils import (
	toStr,
	toBytes,
	replaceStringTable,
)
from pyglossary.compression import (
	compressionOpen,
	stdCompressions,
)
from pyglossary.os_utils import indir
from pyglossary.entry_base import BaseEntry

from pyglossary.glossary_type import GlossaryType

enable = False
lname = ""
format = "Unknown"
description = "Unknown"
extensions = ()  # type: Tuple[str, ...]
extensionCreate = ""  # type: str
singleFile = False
kind = ""
wiki = ""
website = None

# key is option/argument name, value is instance of Option
optionsProp = {}  # type: Dict[str, Option]

sortOnWrite = DEFAULT_NO  # type: YesNoAlwaysNever
