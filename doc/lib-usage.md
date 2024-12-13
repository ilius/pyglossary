# Using PyGlossary as a Python library

There are a few examples in [doc/lib-examples](./doc/lib-examples) directory.

Here is a basic script that converts any supported glossary format to [Tabfile](./doc/p/tabfile.md):

```python
import sys
from pyglossary import Glossary

# Glossary.init() should be called only once, so make sure you put it
# in the right place
Glossary.init()

glos = Glossary()
glos.convert(
	inputFilename=sys.argv[1],
	outputFilename=f"{sys.argv[1]}.txt",
	# although it can detect format for *.txt, you can still pass outputFormat
	outputFormat="Tabfile",
	# you can pass readOptions or writeOptions as a dict
	# writeOptions={"encoding": "utf-8"},
)
```

And if you choose to use `glossary_v2`:

```python
import sys
from pyglossary.glossary_v2 import ConvertArgs, Glossary

# Glossary.init() should be called only once, so make sure you put it
# in the right place
Glossary.init()

glos = Glossary()
glos.convert(ConvertArgs(
	inputFilename=sys.argv[1],
	outputFilename=f"{sys.argv[1]}.txt",
	# although it can detect format for *.txt, you can still pass outputFormat
	outputFormat="Tabfile",
	# you can pass readOptions or writeOptions as a dict
	# writeOptions={"encoding": "utf-8"},
))
```

You may look at docstring of `Glossary.convert` for full list of keyword arguments.

If you need to add entries inside your Python program (rather than converting one glossary into another), then you use `write` instead of `convert`, here is an example:

```python
from pyglossary import Glossary

Glossary.init()

glos = Glossary()
mydict = {
	"a": "test1",
	"b": "test2",
	"c": "test3",
}
for word, defi in mydict.items():
	glos.addEntryObj(glos.newEntry(
		word,
		defi,
		defiFormat="m",  # "m" for plain text, "h" for HTML
	))

glos.setInfo("title", "My Test StarDict")
glos.setInfo("author", "John Doe")
glos.write("test.ifo", format="Stardict")
```

**Note:** `addEntryObj` is renamed to `addEntry` in `pyglossary.glossary_v2`.

**Note:** Switching to `glossary_v2` is optional and recommended.

And if you need to read a glossary from file into a `Glossary` object in RAM (without immediately converting it), you can use `glos.read(filename, format=inputFormat)`. Be wary of RAM usage in this case.

If you want to include images, css, js or other files in a glossary that you are creating, you need to add them as **Data Entries**, for example:

```python
with open(os.path.join(imageDir, "a.jpeg")) as fp:
	glos.addEntry(glos.newDataEntry("img/a.jpeg", fp.read()))
```

The first argument to `newDataEntry` must be the relative path (that generally html codes of your definitions points to).
