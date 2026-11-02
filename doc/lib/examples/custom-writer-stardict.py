import os
import sys
from os.path import isfile

from pyglossary.exp.stardict_creator import StarDictCreator
from pyglossary.glossary_v2 import Glossary

Glossary.init()

defiFormat = "h"
defiFormatB = defiFormat.encode("ascii")

tmpDbFile = "/tmp/stardict-tmp.db"
if isfile(tmpDbFile):
	os.remove(tmpDbFile)

outPath = sys.argv[1]

creator = StarDictCreator(
	defiFormat=defiFormat,
	filename=outPath,
	tmpDbFile=tmpDbFile,
)

for i in reversed(range(10)):
	creator.addEntry(f"word-{i}", f"defi-{i}")

creator.write()
creator.finish()
