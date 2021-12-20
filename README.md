# PyGlossary

A tool for converting dictionary files aka glossaries.

The primary purpose is to be able to use our offline glossaries in any Open
Source dictionary we like on any OS/device.

There are countless formats, and my time is limited, so I implement formats that
seem more useful for myself, or for Open Source community. Also diversity of
languages is taken into account. Pull requests are welcome.

## Screenshots

<img src="https://raw.githubusercontent.com/wiki/ilius/pyglossary/screenshots/40a-gtk-txt-stardict-aryanpour-dark.png" width="50%" height="50%"/>

Linux - Gtk3-based interface

______________________________________________________________________

<img src="https://raw.githubusercontent.com/wiki/ilius/pyglossary/screenshots/40b-tk-bgl-epub-es-en-2.png" width="50%" height="50%"/>

Windows - Tkinter-based interface

______________________________________________________________________

<img src="https://raw.githubusercontent.com/wiki/ilius/pyglossary/screenshots/32-cmd-freedict-mids-de-ru.png" width="50%" height="50%"/>

Linux - command-line interface

______________________________________________________________________

<img src="https://raw.githubusercontent.com/wiki/ilius/pyglossary/screenshots/40-cmdi-termux-zim-slob-en-med.jpg" width="50%" height="50%"/>

Android Termux - interactive command-line interface

## Supported formats

| Format                                                  |     |    Extension    | Read | Write |
| ------------------------------------------------------- | :-: | :-------------: | :--: | :---: |
| [Aard 2 (slob)](./doc/p/aard2_slob.md)                  |  🔢  |      .slob      |  ✔   |   ✔   |
| [ABBYY Lingvo DSL](./doc/p/dsl.md)                      |  📝  |      .dsl       |  ✔   |       |
| [Almaany.com](./doc/p/almaany.md) (SQLite3, Arabic)     |  🔢  |       .db       |  ✔   |       |
| [AppleDict Binary](./doc/p/appledict_bin.md)            |  🔢  |   .dictionary   |  ✔   |   ❌   |
| [AppleDict Source](./doc/p/appledict.md)                |  📁  |                 |      |   ✔   |
| [Babylon BGL](./doc/p/babylon_bgl.md)                   |  🔢  |      .bgl       |  ✔   |   ❌   |
| [CC-CEDICT](./doc/p/cc_cedict.md) (Chinese)             |  📝  |                 |  ✔   |   ❌   |
| [cc-kedict](./doc/p/cc_kedict.md) (Korean)              |  📝  |                 |  ✔   |   ❌   |
| [CSV](./doc/p/csv.md)                                   |  📝  |      .csv       |  ✔   |   ✔   |
| [Dict.cc](./doc/p/dict_cc.md) (SQLite3, German)         |  🔢  |       .db       |  ✔   |       |
| [DICT.org / Dictd server](./doc/p/dict_org.md)          |  📁  |    (📝.index)    |  ✔   |   ✔   |
| [DICT.org / dictfmt source](./doc/p/dict_org_source.md) |  📝  |     (.dtxt)     |      |   ✔   |
| [dictunformat output file](./doc/p/dictunformat.md)     |  📝  | (.dictunformat) |  ✔   |       |
| [DictionaryForMIDs](./doc/p/dicformids.md)              |  📁  |    (📁.mids)     |  ✔   |   ✔   |
| [DigitalNK](./doc/p/digitalnk.md) (SQLite3, N-Korean)   |  🔢  |       .db       |  ✔   |       |
| [EDLIN](./doc/p/edlin.md)                               |  📁  |     .edlin      |  ✔   |   ✔   |
| [EPUB-2 E-Book](./doc/p/epub2.md)                       |  📦  |      .epub      |  ❌   |   ✔   |
| [FreeDict](./doc/p/freedict.md)                         |  📝  |      .tei       |  ✔   |   ❌   |
| [Gettext Source](./doc/p/gettext_po.md)                 |  📝  |       .po       |  ✔   |   ✔   |
| [HTML Directory (by file size)](./doc/p/html_dir.md)    |  📁  |                 |  ❌   |   ✔   |
| [JMDict](./doc/p/jmdict.md) (Japanese)                  |  📝  |                 |  ✔   |   ❌   |
| [JSON](./doc/p/json.md)                                 |  📝  |      .json      |      |   ✔   |
| [Kobo E-Reader Dictionary](./doc/p/kobo.md)             |  📦  |    .kobo.zip    |  ❌   |   ✔   |
| [Kobo E-Reader Dictfile](./doc/p/kobo_dictfile.md)      |  📝  |       .df       |  ✔   |   ✔   |
| [Lingoes Source](./doc/p/lingoes_ldf.md)                |  📝  |      .ldf       |  ✔   |   ✔   |
| [Mobipocket E-Book](./doc/p/mobi.md)                    |  🔢  |      .mobi      |  ❌   |   ✔   |
| [Octopus MDict](./doc/p/octopus_mdict.md)               |  🔢  |      .mdx       |  ✔   |   ❌   |
| [Sdictionary Binary](./doc/p/sdict.md)                  |  🔢  |      .dct       |  ✔   |       |
| [Sdictionary Source](./doc/p/sdict_source.md)           |  📝  |      .sdct      |      |   ✔   |
| [SQL](./doc/p/sql.md)                                   |  📝  |      .sql       |  ❌   |   ✔   |
| [StarDict](./doc/p/stardict.md)                         |  📁  |     (📝.ifo)     |  ✔   |   ✔   |
| [Tabfile](./doc/p/tabfile.md)                           |  📝  |   .txt, .tab    |  ✔   |   ✔   |
| [Wiktionary Dump](./doc/p/wiktionary_dump.md)           |  📝  |      .xml       |  ✔   |   ❌   |
| [Wordset.org](./doc/p/wordset.md)                       |  📁  |                 |  ✔   |       |
| [XDXF](./doc/p/xdxf.md)                                 |  📝  |      .xdxf      |  ✔   |   ❌   |
| [Zim (Kiwix)](./doc/p/zim.md)                           |  🔢  |      .zim       |  ✔   |       |

Legend:

- 📁	Directory
- 📝	Text file
- 📦	Package/archive file
- 🔢	Binary file
- ✔		Supported
- ❌ 	Will not be supported

Note: SQLite3 `.db` files are not detected by extension; So you need to specify the format.

## Requirements

PyGlossary requires **Python 3.7 or higher**, and works in practically all
modern operating systems. While primarily designed for *GNU/Linux*, it works
on *Windows*, *Mac OS X* and other Unix-based operating systems as well.

As shown in the screenshots, there are multiple User Interface types (multiple
ways to use the program).

- **Gtk3-based interface**, uses [PyGI (Python Gobject Introspection)](http://pygobject.readthedocs.io/en/latest/getting_started.html)
  You can install it on:

  - Debian/Ubuntu: `apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0`
  - openSUSE: `zypper install python3-gobject gtk3`
  - Fedora: `dnf install pygobject3 python3-gobject gtk3`
  - ArchLinux:
    - `pacman -S python-gobject gtk3`
    - https://aur.archlinux.org/packages/pyglossary/
  - Mac OS X: `brew install pygobject3 gtk+3`
  - Nix / NixOS: `nix-shell -p gnome3.gobjectIntrospection python38Packages.pygobject3 python38Packages.pycairo`

- **Tkinter-based interface**, works in the lack of Gtk. Specially on
  Windows where Tkinter library is installed with the Python itself.
  You can also install it on:

  - Debian/Ubuntu: `apt-get install python3-tk tix`
  - openSUSE: `zypper install python3-tk tix`
  - Fedora: `yum install python3-tkinter tix`
  - Mac OS X: read <https://www.python.org/download/mac/tcltk/>
  - Nix / NixOS: `nix-shell -p python38Packages.tkinter tix`

- **Command-line interface**, works in all operating systems without
  any specific requirements, just type:

  `python3 main.py --help`

  - **Interactive command-line interface**
    - Requires: `pip3 install prompt_toolkit`
    - Perfect for mobile devices (like Termux on Android) where no GUI is available
    - Automatically selected if output file argument is not passed **and** one of these:
      - On Linux and `$DISPLAY` environment variable is empty or not set
        - For example when you are using a remote Linux machine over SSH
      - On Mac and no `tkinter` module is found
    - Manually select with `--cmd` or `--ui=cmd`
      - Minimally: `python3 main.py --cmd`
      - You can still pass input file, or any flag/option
    - If both input and output files are passed, non-interactive cmd ui will be default
    - If you are writing a script, you can pass `--no-interactive` to force disable interactive ui
      - Then you have to pass both input and output file arguments
    - Don't forget to use *Up/Down* or *Tab* keys in prompts!
      - Up/Down key shows you recent values you have used
      - Tab key shows available values/options
    - You can press Control+C (on Linux/Windows) at any prompt to exit

## UI (User Interface) selection

When you run PyGlossary without any command-line arguments or options/flags,
PyGlossary tries to find PyGI and open the Gtk3-based interface. If it fails,
it tries to find Tkinter and open the Tkinter-based interface. If that fails,
it tries to find `prompt_toolkit` and run interactive command-line interface.
And if none of these libraries are found, it exits with an error.

But you can explicitly determine the user interface type using `--ui`

- `python3 main.py --ui=gtk`
- `python3 main.py --ui=tk`
- `python3 main.py --ui=cmd`

## Installation on Windows

- [Download and install Python](https://www.python.org/downloads/windows/) (3.8 or above is recommended)
- Open Start -> type Command -> right-click on Command Prompt -> Run as administrator
- To ensure you have `pip`, run: `python -m ensurepip --upgrade`
- To install, run: `pip install --upgrade pyglossary`
- Now you should be able to run `pyglossary` command
- If command was not found, make sure Python environment variables are set up:
  <img src="https://raw.githubusercontent.com/wiki/ilius/pyglossary/screenshots/windows-python39-env-vars.png" width="50%" height="50%"/>

## Feature-specific requirements

- **Using `--remove-html-all` flag**

  `sudo pip3 install lxml beautifulsoup4`

Some formats have additional requirements.
If you have trouble with any format, please check the [link given for that format](#supported-formats) to see its documentations.

**Using Termux on Android?** See [doc/termux.md](./doc/termux.md)

## Configuration

See [doc/config.md](./doc/config.md).

## Direct and indirect modes

Indirect mode means the input glossary is completely read and loaded into RAM, then converted
into the output format. This was the only method available in old versions (before [3.0.0](https://github.com/ilius/pyglossary/releases/tag/3.0.0)).

Direct mode means entries are one-at-a-time read, processed and written into output glossary.

Direct mode was added to limit the memory usage for large glossaries; But it may reduce the
conversion time for most cases as well.

Converting glossaries into some formats like [StarDict](./doc/p/stardict.md) and
[EPUB-2](./doc/p/epub2.md) requires sorting entries.
That's why direct mode will not work for these format, and PyGlossary will use indirect
mode. Otherwise direct mode will be the default. You may override this by `--indirect` flag.

## SQLite mode

As mentioned above, converting glossaries into some formats like [StarDict](./doc/p/stardict.md) will need
them to loaded into RAM.

This can be problematic if the glossary is too big to fit into RAM. That's when
you should try adding `--sqlite` flag to your command. Then it uses SQLite3 as intermediate
storage for storing, sorting and then fetching entries. This fixes the memory issue, and may
even reduce running time of conversion (depending on your home directory storage).

The temporary SQLite file is stored in [cache directory](#cache-directory) then deleted after
conversion (unless you pass `--no-cleanup` flag).

Currently you can not disable alternates in SQLite mode (`--no-alts` is ignored).

## Cache directory

The cache directory is used for storing temporary files which are either moved or deleted
after conversion. You can pass `--no-cleanup` flag in order to keep them.

The path of cache directory:

- Linux or BSD: `~/.cache/pyglossary/`
- Mac: `~/Library/Caches/PyGlossary/`
- Windows: `C:\Users\USERNAME\AppData\Local\PyGlossary\Cache\`

## User plugins

If you want to add your own plugin without adding it to source code directory,
or you want to use a plugin that has been removed from repository,
you can place it in this directory:

- Linux or BSD: `~/.pyglossary/plugins/`
- Mac: `~/Library/Preferences/PyGlossary/plugins/`
- Windows: `C:\Users\USERNAME\AppData\Roaming\PyGlossary\plugins\`

## Using PyGlossary as a Python library

There are a few examples in [doc/lib-examples](./doc/lib-examples) directory.

Here is a basic script that converts any supported glossary format to [Tabfile](./doc/p/tabfile.md):

```
import sys
import pyglossary
from pyglossary import Glossary

# Glossary.init() must be called only once, so make sure you put it
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

You may look at docstring of `Glossary.convert` for full list of keyword arguments.

If you need to add entries inside your Python program (rather than converting one glossary into another), then you use `write` instead of `convert`, here is an example:

```
from pyglossary.glossary import Glossary

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

And if you need to read a glossary from file into a `Glossary` object in RAM (without immediately converting it), you can use `glos.read(filename, format=inputFormat)`. Be wary of RAM usage in this case.

## Internal glossary structure

A glossary contains a number of entries.

Each entry contains:

- Headword (title or main phrase for lookup)
- Alternates (some alternative phrases for lookup)
- Definition

In PyGlossary, headword and alternates together are accessible as a single Python list `entry.l_word`

`entry.defi` is the definition as a Python Unicode `str`. Also `entry.b_defi` is definition in UTF-8 byte array.

`entry.defiFormat` is definition format. If definition is plaintext (not rich text), the value is `m`. And if it's in HTML (contains any html tag), then `defiFormat` is `m`. The value `x` is also allowed for XFXF, but XDXF is not widely supported in dictionary applications.

There is another type of `Entry` which is called **Data Entry**, and generally contains image files, TTL or other audio files, or any file that was included in input glossary. For data entries:

- `entry.s_word` is file name (and `l_word` is still a list containing this string),
- `entry.defiFormat` is `b`
- `entry.data` gives the content of file in `bytes`.
