from pyglossary.glossary import Glossary

Glossary.init()

glos = Glossary()

defiFormat = "m"
# "m" for plain text, "h" for HTML

mydict = {
	"a": "test1",
	"b": "test2",
	"c": "test3",
	"d": "test4",
	"e": "test5",
	"f": "test6",
}

for word, defi in mydict.items():
	glos.addEntryObj(glos.newEntry(word, defi, defiFormat=defiFormat))

glos.setInfo("title", "My Test StarDict")
glos.setInfo("author", "John Doe")
glos.write("test.ifo", format="Stardict")
