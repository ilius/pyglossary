import sys

from pyglossary.glossary_creator import GlossaryCreator
from pyglossary.glossary_v2 import Glossary

Glossary.init()

creator = GlossaryCreator(sys.argv[1], "Epub2")

creator.setInfo("title", "Sample EPUB Glossary")
creator.setInfo("author", "PyGlossary")

# numbers are alphabetical rank; list order is deliberately shuffled
entries = [
	("zebra (10)", "<p>African equid with black-and-white stripes.</p>"),
	("mango (9)", "<p>A tropical stone fruit with sweet orange flesh.</p>"),
	("cherry (3)", "<p>A small stone fruit, often red.</p>"),
	("apple (1)", "<p>A round fruit, typically red or green.</p>"),
	("banana (2)", "<p>A long yellow fruit rich in potassium.</p>"),
	("date (4)", "<p>A sweet fruit from the date palm.</p>"),
	("elderberry (5)", "<p>Small dark berries used in syrups and wines.</p>"),
	("fig (6)", "<p>A soft fruit with many tiny seeds.</p>"),
	("grape (7)", "<p>A small round fruit that grows in clusters.</p>"),
	("honeydew (8)", "<p>A pale green melon with sweet flesh.</p>"),
]

for word, defi in entries:
	creator.addEntry(word, defi, defiFormat="h")

creator.finish()
