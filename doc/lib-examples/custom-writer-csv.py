import sys

from pyglossary.glossary_creator import GlossaryCreator
from pyglossary.glossary_v2 import Glossary

Glossary.init()

creator = GlossaryCreator(sys.argv[1], "Csv")

for i in range(10):
	creator.addEntry(f"word-{i}", f"defi-{i}")

creator.finish()
