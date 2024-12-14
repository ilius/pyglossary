import logging
import os
import sys
from os.path import (
	exists,
	isdir,
	isfile,
	join,
	split,
	splitext,
)
from pprint import pformat

from pyglossary.core import rootDir

sys.path.insert(0, rootDir)  # noqa: E402

from pyglossary import core
from pyglossary.compression import (
	compressionOpen,
	stdCompressions,
)
from pyglossary.core import (
	cacheDir,
	pip,
)
from pyglossary.flags import (
	ALWAYS,
	DEFAULT_NO,
	DEFAULT_YES,
	NEVER,
	YesNoAlwaysNever,
)
from pyglossary.glossary_types import EntryType, GlossaryType
from pyglossary.option import (
	BoolOption,
	DictOption,
	EncodingOption,
	FileSizeOption,
	FloatOption,
	HtmlColorOption,
	IntOption,
	ListOption,
	NewlineOption,
	Option,
	StrOption,
)
from pyglossary.os_utils import indir
from pyglossary.text_utils import toStr

log = logging.getLogger("pyglossary")

enable = False
lname = ""
name = "Unknown"
description = "Unknown"
extensions: "tuple[str, ...]" = ()
extensionCreate = ""
singleFile = False
kind = ""
wiki = ""
website = None

# key is option/argument name, value is instance of Option
optionsProp: "dict[str, Option]" = {}

sortOnWrite: YesNoAlwaysNever = DEFAULT_NO

__all__ = [
	"ALWAYS",
	"DEFAULT_NO",
	"DEFAULT_YES",
	"NEVER",
	"BoolOption",
	"DictOption",
	"EncodingOption",
	"EntryType",
	"FileSizeOption",
	"FloatOption",
	"GlossaryType",
	"HtmlColorOption",
	"IntOption",
	"ListOption",
	"NewlineOption",
	"StrOption",
	"YesNoAlwaysNever",
	"cacheDir",
	"compressionOpen",
	"core",
	"description",
	"enable",
	"exists",
	"extensionCreate",
	"extensions",
	"indir",
	"isdir",
	"isfile",
	"join",
	"kind",
	"lname",
	"log",
	"logging",
	"name",
	"optionsProp",
	"os",
	"pformat",
	"pip",
	"rootDir",
	"singleFile",
	"sortOnWrite",
	"split",
	"splitext",
	"stdCompressions",
	"toStr",
	"website",
	"wiki",
]
